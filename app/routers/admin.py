from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from app.database import get_db
from app.models.models import Budget, User, Inventory
from app.auth import get_admin_user, get_password_hash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    # Статистика пользователей
    users_count = db.query(User).count()
    budget_entries_count = db.query(Budget).count()
    inventory_count = db.query(Inventory).count()
    
    # НОВОЕ: Счетчик ожидающих модерации
    pending_moderation_count = db.query(Budget).filter(Budget.is_approved == False).count()
    
    # Последние записи
    recent_budget = db.query(Budget).order_by(Budget.id.desc()).limit(5).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": admin_user,
        "users_count": users_count,
        "budget_entries_count": budget_entries_count,
        "inventory_count": inventory_count,
        "pending_moderation_count": pending_moderation_count,  # НОВОЕ
        "recent_budget": recent_budget
    })

@router.get("/admin/budget", response_class=HTMLResponse)
async def admin_budget(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    # Получаем все записи бюджета с пагинацией
    budget_entries = db.query(Budget).order_by(Budget.data.desc()).limit(100).all()
    
    return templates.TemplateResponse("admin/budget.html", {
        "request": request,
        "user": admin_user,
        "budget_entries": budget_entries
    })

@router.get("/admin/budget/add", response_class=HTMLResponse)
async def admin_add_budget_page(request: Request, admin_user: User = Depends(get_admin_user)):
    return templates.TemplateResponse("admin/add_budget.html", {
        "request": request,
        "user": admin_user,
        "today": date.today().strftime('%Y-%m-%d')
    })

@router.post("/admin/budget/add")
async def admin_add_budget(
    request: Request,
    description: str = Form(...),
    price: float = Form(...),
    data: date = Form(...),
    type: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    budget_entry = Budget(
        description=description,
        price=price,
        data=data,
        type=type
    )
    
    db.add(budget_entry)
    db.commit()
    
    return RedirectResponse(url="/admin/budget", status_code=302)

@router.get("/admin/budget/edit/{budget_id}", response_class=HTMLResponse)
async def admin_edit_budget_page(budget_id: int, request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    entry = db.query(Budget).filter(Budget.id == budget_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Budget entry not found")
    
    return templates.TemplateResponse("admin/edit_budget.html", {
        "request": request,
        "user": admin_user,
        "entry": entry
    })

@router.post("/admin/budget/edit/{budget_id}")
async def admin_edit_budget(
    budget_id: int,
    request: Request,
    description: str = Form(...),
    price: float = Form(...),
    data: date = Form(...),
    type: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    budget_entry = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget_entry:
        raise HTTPException(status_code=404, detail="Budget entry not found")
    
    budget_entry.description = description
    budget_entry.price = price
    budget_entry.data = data
    budget_entry.type = type
    
    db.commit()
    
    return RedirectResponse(url="/admin/budget", status_code=302)

@router.post("/admin/budget/delete/{budget_id}")
async def admin_delete_budget(budget_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    budget_entry = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget_entry:
        raise HTTPException(status_code=404, detail="Budget entry not found")
    
    db.delete(budget_entry)
    db.commit()
    
    return RedirectResponse(url="/admin/budget", status_code=302)

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": admin_user,
        "users": users
    })

@router.get("/admin/inventory", response_class=HTMLResponse)
async def admin_inventory(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    # Получаем данные инвентаря
    inventory_query = text('''
        SELECT owner, COUNT(*) as item_count, ARRAY_TO_STRING(ARRAY_AGG(item_name), ', ') as items
        FROM inventory 
        GROUP BY owner
        ORDER BY owner
    ''')
    
    inventory_summary = db.execute(inventory_query).fetchall()
    
    return templates.TemplateResponse("admin/inventory.html", {
        "request": request,
        "user": admin_user,
        "inventory_summary": inventory_summary
    })

@router.post("/admin/reset-password")
async def admin_reset_password(
    request: Request,
    user_id: int = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Проверяем, что пароли совпадают
    if new_password != confirm_password:
        return RedirectResponse(url="/admin/users?error=passwords_mismatch", status_code=302)
    
    # Проверяем минимальную длину пароля
    if len(new_password) < 4:
        return RedirectResponse(url="/admin/users?error=password_too_short", status_code=302)
    
    # Находим пользователя
    user_to_update = db.query(User).filter(User.id == user_id).first()
    if not user_to_update:
        return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)
    
    # Обновляем пароль
    user_to_update.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return RedirectResponse(url="/admin/users?success=password_changed", status_code=302) 