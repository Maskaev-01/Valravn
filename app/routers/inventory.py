from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import date
from typing import Optional
from app.database import get_db
from app.models.models import Inventory, User
from app.auth import get_current_user_from_cookie, get_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db),
    owner: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    # Базовый запрос
    query = db.query(Inventory)
    
    # Применяем фильтры
    if owner and owner != "all":
        query = query.filter(Inventory.owner == owner)
    if item_type and item_type != "all":
        query = query.filter(Inventory.item_type == item_type)
    if search:
        query = query.filter(
            (Inventory.item_name.ilike(f"%{search}%")) |
            (Inventory.owner.ilike(f"%{search}%")) |
            (Inventory.notes.ilike(f"%{search}%"))
        )
    
    inventory_items = query.order_by(Inventory.owner, Inventory.item_name).all()
    
    # Получаем списки для фильтров
    owners_list = db.query(Inventory.owner).distinct().order_by(Inventory.owner).all()
    types_list = db.query(Inventory.item_type).distinct().filter(Inventory.item_type.isnot(None)).order_by(Inventory.item_type).all()
    
    # Статистика
    total_items = db.query(func.count(Inventory.id)).scalar()
    unique_owners = db.query(func.count(func.distinct(Inventory.owner))).scalar()
    
    return templates.TemplateResponse("inventory/list.html", {
        "request": request,
        "user": current_user,
        "inventory_items": inventory_items,
        "owners_list": owners_list,
        "types_list": types_list,
        "total_items": total_items,
        "unique_owners": unique_owners,
        "filters": {
            "owner": owner,
            "item_type": item_type,
            "search": search
        }
    })

@router.get("/inventory/add", response_class=HTMLResponse)
async def add_inventory_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("inventory/add.html", {
        "request": request,
        "user": current_user
    })

@router.post("/inventory/add")
async def add_inventory(
    request: Request,
    owner: str = Form(...),
    item_name: str = Form(...),
    item_type: Optional[str] = Form(None),
    subtype: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    find_type: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    burial_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    inventory_item = Inventory(
        owner=owner,
        item_name=item_name,
        item_type=item_type if item_type else None,
        subtype=subtype if subtype else None,
        material=material if material else None,
        color=color if color else None,
        size=size if size else None,
        find_type=find_type if find_type else None,
        region=region if region else None,
        place=place if place else None,
        burial_number=burial_number if burial_number else None,
        notes=notes if notes else None
    )
    
    db.add(inventory_item)
    db.commit()
    
    return RedirectResponse(url="/inventory", status_code=302)

@router.get("/inventory/edit/{item_id}", response_class=HTMLResponse)
async def edit_inventory_page(
    item_id: int, 
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return templates.TemplateResponse("inventory/edit.html", {
        "request": request,
        "user": current_user,
        "item": item
    })

@router.post("/inventory/edit/{item_id}")
async def edit_inventory(
    item_id: int,
    request: Request,
    owner: str = Form(...),
    item_name: str = Form(...),
    item_type: Optional[str] = Form(None),
    subtype: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    find_type: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    place: Optional[str] = Form(None),
    burial_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.owner = owner
    item.item_name = item_name
    item.item_type = item_type if item_type else None
    item.subtype = subtype if subtype else None
    item.material = material if material else None
    item.color = color if color else None
    item.size = size if size else None
    item.find_type = find_type if find_type else None
    item.region = region if region else None
    item.place = place if place else None
    item.burial_number = burial_number if burial_number else None
    item.notes = notes if notes else None
    
    db.commit()
    
    return RedirectResponse(url="/inventory", status_code=302)

@router.post("/inventory/delete/{item_id}")
async def delete_inventory(
    item_id: int, 
    current_user: User = Depends(get_admin_user), 
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    
    return RedirectResponse(url="/inventory", status_code=302)

@router.get("/inventory/summary", response_class=HTMLResponse)
async def inventory_summary(
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    # Получаем данные из view "Имущество сводная"
    summary_query = text('''
        SELECT owner,
               COUNT(*) as item_count,
               ARRAY_TO_STRING(ARRAY_AGG(item_name ORDER BY item_name), ', ') as items
        FROM inventory 
        GROUP BY owner
        ORDER BY owner
    ''')
    
    summary_results = db.execute(summary_query).fetchall()
    
    # Статистика по типам предметов
    types_query = text('''
        SELECT item_type, COUNT(*) as count
        FROM inventory 
        WHERE item_type IS NOT NULL
        GROUP BY item_type
        ORDER BY count DESC
    ''')
    
    types_results = db.execute(types_query).fetchall()
    
    # Статистика по материалам
    materials_query = text('''
        SELECT material, COUNT(*) as count
        FROM inventory 
        WHERE material IS NOT NULL
        GROUP BY material
        ORDER BY count DESC
    ''')
    
    materials_results = db.execute(materials_query).fetchall()
    
    return templates.TemplateResponse("inventory/summary.html", {
        "request": request,
        "user": current_user,
        "summary_results": summary_results,
        "types_results": types_results,
        "materials_results": materials_results
    })

@router.get("/inventory/{item_id}", response_class=HTMLResponse)
async def view_inventory_item(
    item_id: int, 
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Найдем похожие предметы того же владельца
    similar_items = db.query(Inventory).filter(
        Inventory.owner == item.owner,
        Inventory.id != item.id
    ).limit(5).all()
    
    return templates.TemplateResponse("inventory/detail.html", {
        "request": request,
        "user": current_user,
        "item": item,
        "similar_items": similar_items
    }) 