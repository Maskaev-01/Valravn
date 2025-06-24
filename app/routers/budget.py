from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from app.database import get_db
from app.models.models import Budget, User
from app.models.schemas import BudgetCreate
from app.auth import get_current_user_from_cookie, get_admin_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    # Получаем последние взносы
    recent_contributions = db.query(Budget).filter(Budget.type == "Взнос").order_by(Budget.data.desc()).limit(10).all()
    
    # Получаем сводную информацию
    total_income = db.query(Budget).filter(Budget.price > 0, Budget.type != "Погашение Долга").all()
    total_expenses = db.query(Budget).filter(Budget.price < 0, Budget.type != "Долг").all()
    
    income_sum = sum([b.price for b in total_income]) if total_income else 0
    expenses_sum = sum([b.price for b in total_expenses]) if total_expenses else 0
    balance = income_sum + expenses_sum
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "recent_contributions": recent_contributions,
        "income_sum": income_sum,
        "expenses_sum": abs(expenses_sum),
        "balance": balance
    })

@router.get("/add-contribution", response_class=HTMLResponse)
async def add_contribution_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("add_contribution.html", {
        "request": request,
        "user": current_user
    })

@router.post("/add-contribution")
async def add_contribution(
    request: Request,
    description: str = Form(...),
    price: float = Form(...),
    contribution_date: date = Form(...),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    # Создаем новый взнос
    budget_entry = Budget(
        description=description,
        price=price,
        data=contribution_date,
        type="Взнос"
    )
    
    db.add(budget_entry)
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=302)

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
    # Базовые условия для фильтрации
    where_conditions = ["1=1"]
    
    # Добавляем фильтры
    if start_date:
        where_conditions.append(f"data >= '{start_date}'")
    if end_date:
        where_conditions.append(f"data <= '{end_date}'")
    if report_type and report_type != "all":
        where_conditions.append(f"type = '{report_type}'")
    if contributor and contributor != "all":
        where_conditions.append(f"description = '{contributor}'")
    
    where_clause = " AND ".join(where_conditions)
    
    # Получаем данные из view "Итог" с фильтрацией
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
    
    summary_results = db.execute(summary_query).fetchall()
    
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
    
    monthly_results = db.execute(monthly_query).fetchall()
    
    # Получаем данные по участникам (для отчета "Сводная поимённо")
    contributors_query = text(f'''
        SELECT 
            description,
            COUNT(*) as contribution_count,
            SUM(price) as total_amount,
            AVG(price) as avg_amount,
            MIN(data) as first_contribution,
            MAX(data) as last_contribution
        FROM budget 
        WHERE type = 'Взнос' AND {where_clause}
        GROUP BY description
        ORDER BY total_amount DESC
    ''')
    
    contributors_results = db.execute(contributors_query).fetchall()
    
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
    
    types_results = db.execute(types_query).fetchall()
    
    # Получаем список уникальных участников и типов для фильтров
    contributors_list_query = text("SELECT DISTINCT description FROM budget WHERE type = 'Взнос' ORDER BY description")
    contributors_list = db.execute(contributors_list_query).fetchall()
    
    types_list_query = text("SELECT DISTINCT type FROM budget WHERE type IS NOT NULL ORDER BY type")
    types_list = db.execute(types_list_query).fetchall()
    
    # Получаем историю операций с фильтрацией и пагинацией
    operations_query = text(f'''
        SELECT id, description, price, data, type
        FROM budget 
        WHERE {where_clause}
        ORDER BY data DESC, id DESC
        LIMIT 100
    ''')
    
    operations_history = db.execute(operations_query).fetchall()
    
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
    # Получаем сводную информацию по участникам
    contributors_query = text('''
        SELECT 
            description,
            COUNT(*) as contribution_count,
            SUM(price) as total_amount,
            MAX(data) as last_contribution
        FROM budget 
        WHERE type = 'Взнос'
        GROUP BY description
        ORDER BY total_amount DESC
    ''')
    
    contributors_results = db.execute(contributors_query).fetchall()
    
    return templates.TemplateResponse("contributors.html", {
        "request": request,
        "user": current_user,
        "contributors": contributors_results
    }) 