from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
from typing import Optional
from app.database import get_db
from app.models.models import Budget, User
from app.models.schemas import BudgetCreate, BudgetApproval
from app.auth import get_current_user_from_cookie, get_admin_user, get_current_user_optional
from app.file_manager import file_manager

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    # Получаем последние взносы (только одобренные)
    recent_contributions = db.query(Budget).filter(
        Budget.type == "Взнос", 
        Budget.is_approved == True
    ).order_by(Budget.data.desc()).limit(10).all()
    
    # Получаем сводную информацию (только одобренные операции)
    total_income = db.query(Budget).filter(
        Budget.price > 0, 
        Budget.type != "Погашение Долга",
        Budget.is_approved == True
    ).all()
    
    total_expenses = db.query(Budget).filter(
        Budget.price < 0, 
        Budget.type != "Долг",
        Budget.is_approved == True
    ).all()
    
    income_sum = sum([b.price for b in total_income]) if total_income else 0
    expenses_sum = sum([b.price for b in total_expenses]) if total_expenses else 0
    balance = income_sum + expenses_sum
    
    # Если пользователь админ, показываем количество ожидающих модерации
    pending_count = 0
    if current_user.is_admin == 1:
        pending_count = db.query(Budget).filter(Budget.is_approved == False).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "recent_contributions": recent_contributions,
        "income_sum": income_sum,
        "expenses_sum": abs(expenses_sum),
        "balance": balance,
        "pending_count": pending_count
    })

@router.get("/add-contribution", response_class=HTMLResponse)
async def add_contribution_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    # Определяем имя пользователя
    user_name = ""
    if current_user.vk_id:  # VK пользователь
        user_name = f"{current_user.first_name} {current_user.last_name}".strip()
    
    return templates.TemplateResponse("add_contribution.html", {
        "request": request,
        "user": current_user,
        "user_name": user_name,
        "is_vk_user": bool(current_user.vk_id)
    })

@router.post("/add-contribution")
async def add_contribution(
    request: Request,
    description: str = Form(...),
    price: float = Form(...),
    contribution_date: date = Form(...),
    contributor_name: Optional[str] = Form(None),
    screenshot: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        # ДОБАВЛЯЕМ ВАЛИДАЦИЮ ДАННЫХ
        # Проверяем сумму
        if price <= 0:
            raise HTTPException(status_code=400, detail="Сумма взноса должна быть положительной")
        
        if price > 1000000:  # Максимум 1 миллион
            raise HTTPException(status_code=400, detail="Сумма взноса слишком большая (максимум 1,000,000 ₽)")
        
        # Проверяем описание
        if not description or len(description.strip()) < 3:
            raise HTTPException(status_code=400, detail="Описание должно содержать минимум 3 символа")
        
        if len(description) > 500:
            raise HTTPException(status_code=400, detail="Описание слишком длинное (максимум 500 символов)")
        
        # Проверяем дату
        if contribution_date > date.today():
            raise HTTPException(status_code=400, detail="Дата взноса не может быть в будущем")
        
        from datetime import timedelta
        if contribution_date < date.today() - timedelta(days=365):
            raise HTTPException(status_code=400, detail="Дата взноса не может быть старше года")
        
        # Определяем имя участника
        if current_user.vk_id and not contributor_name:
            # Для VK пользователей используем их имя
            contributor_name = f"{current_user.first_name} {current_user.last_name}".strip()
        elif not contributor_name:
            # Для обычных пользователей используем username
            contributor_name = current_user.username
        
        # Проверяем имя участника
        if not contributor_name or len(contributor_name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Имя участника должно содержать минимум 2 символа")
        
        if len(contributor_name) > 100:
            raise HTTPException(status_code=400, detail="Имя участника слишком длинное (максимум 100 символов)")
        
        # Обрабатываем скриншот если есть
        screenshot_path = None
        if screenshot and screenshot.filename:
            # Проверяем размер файла (максимум 10MB)
            if hasattr(screenshot, 'size') and screenshot.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Размер файла не должен превышать 10MB")
            
            # Проверяем тип файла
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if screenshot.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Поддерживаются только изображения (JPEG, PNG, GIF, WebP)")
            
            screenshot_path = await file_manager.save_screenshot(screenshot)
        
        # Создаем новый взнос
        budget_entry = Budget(
            description=description.strip(),
            price=price,
            data=contribution_date,
            type="Взнос",
            contributor_name=contributor_name.strip(),
            user_id=current_user.id,
            screenshot_path=screenshot_path,
            is_approved=False,  # Требует модерации
            created_at=datetime.utcnow()
        )
        
        db.add(budget_entry)
        db.commit()
        db.refresh(budget_entry)
        
        return templates.TemplateResponse("add_contribution.html", {
            "request": request,
            "user": current_user,
            "user_name": contributor_name,
            "is_vk_user": bool(current_user.vk_id),
            "success": "Взнос отправлен на модерацию. После проверки администратором он будет добавлен в систему."
        })
        
    except HTTPException as e:
        return templates.TemplateResponse("add_contribution.html", {
            "request": request,
            "user": current_user,
            "user_name": contributor_name or "",
            "is_vk_user": bool(current_user.vk_id),
            "error": e.detail
        })
    except Exception as e:
        db.rollback()  # ДОБАВЛЯЕМ ROLLBACK при ошибке
        return templates.TemplateResponse("add_contribution.html", {
            "request": request,
            "user": current_user,
            "user_name": contributor_name or "",
            "is_vk_user": bool(current_user.vk_id),
            "error": f"Произошла ошибка: {str(e)}"
        })

@router.get("/moderation", response_class=HTMLResponse)
async def moderation_page(
    request: Request, 
    current_user: User = Depends(get_admin_user), 
    db: Session = Depends(get_db)
):
    """Страница модерации взносов (только для админов)"""
    pending_contributions = db.query(Budget).filter(
        Budget.is_approved == False
    ).order_by(Budget.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/moderation.html", {
        "request": request,
        "user": current_user,
        "pending_contributions": pending_contributions
    })

@router.post("/moderation/approve/{contribution_id}")
async def approve_contribution(
    contribution_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Одобрить взнос"""
    contribution = db.query(Budget).filter(Budget.id == contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Взнос не найден")
    
    contribution.is_approved = True
    contribution.approved_at = datetime.utcnow()
    contribution.approved_by = current_user.id
    
    db.commit()
    return RedirectResponse(url="/moderation", status_code=302)

@router.post("/moderation/reject/{contribution_id}")
async def reject_contribution(
    contribution_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Отклонить взнос"""
    contribution = db.query(Budget).filter(Budget.id == contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Взнос не найден")
    
    # Удаляем скриншот если есть
    if contribution.screenshot_path:
        file_manager.delete_file(contribution.screenshot_path)
    
    db.delete(contribution)
    db.commit()
    return RedirectResponse(url="/moderation", status_code=302)

@router.get("/reports", response_class=HTMLResponse)
async def reports(
    request: Request, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db),
    start_date: str = None,
    end_date: str = None,
    report_type: str = None,
    contributor: str = None
):
    # Базовые условия для фильтрации (только утвержденные)
    where_conditions = ["is_approved = :is_approved"]
    params = {"is_approved": True}
    
    # Добавляем фильтры с параметрами (ИСПРАВЛЕНИЕ SQL ИНЪЕКЦИИ)
    if start_date:
        where_conditions.append("data >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_conditions.append("data <= :end_date")
        params["end_date"] = end_date
    if report_type and report_type != "all":
        where_conditions.append("type = :report_type")
        params["report_type"] = report_type
    if contributor and contributor != "all":
        where_conditions.append("contributor_name = :contributor")
        params["contributor"] = contributor
    
    where_clause = " AND ".join(where_conditions)
    
    # Получаем данные из БД с фильтрацией (БЕЗОПАСНЫЕ ЗАПРОСЫ)
    summary_query = text(f'''
        SELECT 'Общий расход' as result_type, sum(price) as sum_value
        FROM budget 
        WHERE price < 0 AND type != 'Долг' AND {where_clause}
        UNION ALL
        SELECT 'Общий доход' as result_type, sum(price) as sum_value
        FROM budget 
        WHERE price > 0 AND type != 'Погашение Долга' AND {where_clause}
        UNION ALL
        SELECT 'Долг' as result_type, sum(price) as sum_value
        FROM budget 
        WHERE type IN ('Погашение Долга', 'Долг') AND {where_clause}
        UNION ALL
        SELECT 'Баланс' as result_type, sum(price) as sum_value
        FROM budget 
        WHERE {where_clause}
    ''')
    
    summary_results = db.execute(summary_query, params).fetchall()
    
    # Получаем данные помесячно с фильтрацией
    monthly_query = text(f'''
        SELECT 
            DATE_PART('year', data) as year,
            DATE_PART('month', data) as month,
            SUM(CASE WHEN price > 0 AND type != 'Погашение Долга' THEN price ELSE 0 END) as income,
            SUM(CASE WHEN price < 0 AND type != 'Долг' THEN price ELSE 0 END) as expenses,
            SUM(price) as total
        FROM budget 
        WHERE {where_clause}
        GROUP BY DATE_PART('year', data), DATE_PART('month', data)
        ORDER BY year DESC, month DESC
        LIMIT 24
    ''')
    
    monthly_results = db.execute(monthly_query, params).fetchall()
    
    # Получаем данные по участникам (используем contributor_name)
    contributors_query = text(f'''
        SELECT 
            COALESCE(contributor_name, description) as description,
            COUNT(*) as contribution_count,
            SUM(price) as total_amount,
            AVG(price) as avg_amount,
            MIN(data) as first_contribution,
            MAX(data) as last_contribution
        FROM budget 
        WHERE type = 'Взнос' AND {where_clause}
        GROUP BY COALESCE(contributor_name, description)
        ORDER BY total_amount DESC
    ''')
    
    contributors_results = db.execute(contributors_query, params).fetchall()
    
    # Получаем данные по типам операций
    types_query = text(f'''
        SELECT 
            type,
            COUNT(*) as operation_count,
            SUM(price) as total_amount
        FROM budget 
        WHERE {where_clause} AND type IS NOT NULL
        GROUP BY type
        ORDER BY total_amount DESC
    ''')
    
    types_results = db.execute(types_query, params).fetchall()
    
    # Получаем список уникальных участников и типов для фильтров (БЕЗОПАСНЫЕ ЗАПРОСЫ)
    contributors_list_query = text("""
        SELECT DISTINCT COALESCE(contributor_name, description) as contributor 
        FROM budget 
        WHERE type = :type 
        AND is_approved = :is_approved 
        AND COALESCE(contributor_name, description) IS NOT NULL
        AND TRIM(COALESCE(contributor_name, description)) != ''
        ORDER BY contributor
    """)
    contributors_list = db.execute(contributors_list_query, {
        "type": "Взнос",
        "is_approved": True
    }).fetchall()
    
    types_list_query = text("SELECT DISTINCT type FROM budget WHERE type IS NOT NULL AND is_approved = :is_approved ORDER BY type")
    types_list = db.execute(types_list_query, {"is_approved": True}).fetchall()
    
    # Получаем историю операций с фильтрацией и пагинацией
    operations_query = text(f'''
        SELECT id, description, price, data, type, contributor_name, screenshot_path
        FROM budget 
        WHERE {where_clause}
        ORDER BY data DESC, id DESC
        LIMIT 100
    ''')
    
    operations_history = db.execute(operations_query, params).fetchall()
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "user": current_user,
        "summary_results": summary_results,
        "monthly_results": monthly_results,
        "contributors_results": contributors_results,
        "types_results": types_results,
        "operations_history": operations_history,
        "contributors_list": contributors_list,
        "types_list": types_list,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "report_type": report_type,
            "contributor": contributor
        }
    })

@router.get("/contributors", response_class=HTMLResponse)
async def contributors(request: Request, current_user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    # Получаем сводную информацию по участникам (только утвержденные взносы)
    contributors_query = text('''
        SELECT 
            COALESCE(contributor_name, description) as description,
            COUNT(*) as contribution_count,
            SUM(price) as total_amount,
            MAX(data) as last_contribution
        FROM budget 
        WHERE type = :type AND is_approved = :is_approved
        GROUP BY COALESCE(contributor_name, description)
        ORDER BY total_amount DESC
    ''')
    
    contributors_results = db.execute(contributors_query, {
        "type": "Взнос",
        "is_approved": True
    }).fetchall()
    
    return templates.TemplateResponse("contributors.html", {
        "request": request,
        "user": current_user,
        "contributors": contributors_results
    }) 