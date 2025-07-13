"""
Роутер для личного кабинета пользователя
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from app.database import get_db
from app.models.models import User, Budget, Inventory, UserStats, UserAchievement, UserActivityLog
from app.auth import get_current_user_from_cookie
from app.permissions import (
    require_permission, 
    check_user_permission, 
    update_user_activity,
    get_user_permissions,
    get_role_display_name,
    get_role_description
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Главная страница личного кабинета"""
    
    # Получаем статистику пользователя
    user_stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()
    
    # Если статистики нет, создаем её
    if not user_stats:
        user_stats = UserStats(user_id=current_user.id)
        db.add(user_stats)
        db.commit()
        db.refresh(user_stats)
    
    # Получаем последние взносы пользователя
    recent_contributions = db.query(Budget).filter(
        Budget.created_by_user_id == current_user.id,
        Budget.is_approved == True
    ).order_by(desc(Budget.data)).limit(5).all()
    
    # Получаем последние предметы инвентаря
    recent_inventory = db.query(Inventory).filter(
        Inventory.created_by_user_id == current_user.id
    ).order_by(desc(Inventory.created_at)).limit(5).all()
    
    # Получаем достижения пользователя
    achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id,
        UserAchievement.is_active == True
    ).order_by(desc(UserAchievement.earned_at)).limit(10).all()
    
    # Получаем последнюю активность
    recent_activity = db.query(UserActivityLog).filter(
        UserActivityLog.user_id == current_user.id
    ).order_by(desc(UserActivityLog.created_at)).limit(10).all()
    
    # Получаем разрешения пользователя
    permissions = get_user_permissions(current_user)
    
    # Обновляем активность
    update_user_activity(current_user, db, "viewed_dashboard")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "user_stats": user_stats,
        "recent_contributions": recent_contributions,
        "recent_inventory": recent_inventory,
        "achievements": achievements,
        "recent_activity": recent_activity,
        "permissions": permissions,
        "role_display_name": get_role_display_name(current_user.role),
        "role_description": get_role_description(current_user.role)
    })

@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API для получения статистики дашборда"""
    
    # Получаем статистику за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Статистика взносов
    contributions_stats = db.query(
        func.count(Budget.id).label('count'),
        func.sum(Budget.price).label('total')
    ).filter(
        Budget.created_by_user_id == current_user.id,
        Budget.is_approved == True,
        Budget.data >= thirty_days_ago.date()
    ).first()
    
    # Статистика инвентаря
    inventory_stats = db.query(
        func.count(Inventory.id).label('total'),
        func.count(Inventory.id).filter(Inventory.is_club_item == True).label('club_items')
    ).filter(
        Inventory.created_by_user_id == current_user.id
    ).first()
    
    # Статистика активности
    activity_stats = db.query(
        func.count(UserActivityLog.id).label('actions_count')
    ).filter(
        UserActivityLog.user_id == current_user.id,
        UserActivityLog.created_at >= thirty_days_ago
    ).first()
    
    return {
        "contributions": {
            "count": contributions_stats.count or 0,
            "total": float(contributions_stats.total or 0)
        },
        "inventory": {
            "total": inventory_stats.total or 0,
            "club_items": inventory_stats.club_items or 0
        },
        "activity": {
            "actions_count": activity_stats.actions_count or 0
        }
    }

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    success: str = Query(None),
    error: str = Query(None)
):
    """Страница профиля пользователя"""
    
    # Получаем статистику
    user_stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()
    
    # Получаем достижения
    achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id,
        UserAchievement.is_active == True
    ).order_by(desc(UserAchievement.earned_at)).all()
    
    # Получаем разрешения
    permissions = get_user_permissions(current_user)
    
    # Парсим настройки профиля
    profile_settings = current_user.profile_settings or {}
    if isinstance(profile_settings, str):
        try:
            profile_settings = json.loads(profile_settings)
        except:
            profile_settings = {}
    
    # Парсим настройки уведомлений
    notification_settings = current_user.notification_settings or {}
    if isinstance(notification_settings, str):
        try:
            notification_settings = json.loads(notification_settings)
        except:
            notification_settings = {}
    
    update_user_activity(current_user, db, "viewed_profile")
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "user_stats": user_stats,
        "achievements": achievements,
        "permissions": permissions,
        "profile_settings": profile_settings,
        "notification_settings": notification_settings,
        "role_display_name": get_role_display_name(current_user.role),
        "role_description": get_role_description(current_user.role),
        "success_message": success,
        "error_message": error
    })

@router.post("/profile/update-settings")
async def update_profile_settings(
    request: Request,
    theme: str = Form(...),
    language: str = Form(...),
    email_notifications: bool = Form(False),
    vk_notifications: bool = Form(False),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Обновление настроек профиля"""
    
    try:
        # Обновляем настройки профиля
        profile_settings = {
            "theme": theme,
            "language": language
        }
        current_user.profile_settings = profile_settings
        
        # Обновляем настройки уведомлений
        notification_settings = {
            "email_notifications": email_notifications,
            "vk_notifications": vk_notifications
        }
        current_user.notification_settings = notification_settings
        
        db.commit()
        
        update_user_activity(current_user, db, "updated_profile_settings", {
            "theme": theme,
            "language": language
        })
        
        return RedirectResponse(url="/profile?success=Настройки обновлены", status_code=302)
        
    except Exception as e:
        return RedirectResponse(url="/profile?error=Ошибка обновления настроек", status_code=302)

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Страница аналитики пользователя"""
    
    # Получаем данные для графиков
    # Взносы по месяцам за последний год
    year_ago = datetime.utcnow() - timedelta(days=365)
    
    monthly_contributions = db.query(
        func.date_trunc('month', Budget.data).label('month'),
        func.sum(Budget.price).label('total'),
        func.count(Budget.id).label('count')
    ).filter(
        Budget.created_by_user_id == current_user.id,
        Budget.is_approved == True,
        Budget.data >= year_ago.date()
    ).group_by(func.date_trunc('month', Budget.data)).order_by('month').all()
    
    # Активность по дням за последний месяц
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_activity = db.query(
        func.date_trunc('day', UserActivityLog.created_at).label('day'),
        func.count(UserActivityLog.id).label('actions')
    ).filter(
        UserActivityLog.user_id == current_user.id,
        UserActivityLog.created_at >= month_ago
    ).group_by(func.date_trunc('day', UserActivityLog.created_at)).order_by('day').all()
    
    # Статистика инвентаря по типам
    inventory_by_type = db.query(
        Inventory.item_type,
        func.count(Inventory.id).label('count')
    ).filter(
        Inventory.created_by_user_id == current_user.id
    ).group_by(Inventory.item_type).all()
    
    update_user_activity(current_user, db, "viewed_analytics")
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": current_user,
        "monthly_contributions": monthly_contributions,
        "daily_activity": daily_activity,
        "inventory_by_type": inventory_by_type
    })

@router.get("/api/analytics/contributions-chart")
async def get_contributions_chart(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """API для графика взносов"""
    
    # Получаем данные за последние 12 месяцев
    year_ago = datetime.utcnow() - timedelta(days=365)
    
    monthly_data = db.query(
        func.date_trunc('month', Budget.data).label('month'),
        func.sum(Budget.price).label('total')
    ).filter(
        Budget.created_by_user_id == current_user.id,
        Budget.is_approved == True,
        Budget.data >= year_ago.date()
    ).group_by(func.date_trunc('month', Budget.data)).order_by('month').all()
    
    chart_data = {
        "labels": [row.month.strftime("%B %Y") for row in monthly_data],
        "data": [float(row.total or 0) for row in monthly_data]
    }
    
    return chart_data

@router.get("/achievements", response_class=HTMLResponse)
async def achievements_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Страница достижений пользователя"""
    
    # Получаем все достижения пользователя
    achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id
    ).order_by(desc(UserAchievement.earned_at)).all()
    
    # Группируем по типам
    achievements_by_type = {}
    for achievement in achievements:
        if achievement.achievement_type not in achievements_by_type:
            achievements_by_type[achievement.achievement_type] = []
        achievements_by_type[achievement.achievement_type].append(achievement)
    
    update_user_activity(current_user, db, "viewed_achievements")
    
    return templates.TemplateResponse("achievements.html", {
        "request": request,
        "user": current_user,
        "achievements": achievements,
        "achievements_by_type": achievements_by_type
    })

@router.get("/activity", response_class=HTMLResponse)
async def activity_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    action_filter: str = Query(None)
):
    """Страница активности пользователя"""
    
    # Получаем логи активности с пагинацией
    page_size = 20
    offset = (page - 1) * page_size
    
    query = db.query(UserActivityLog).filter(UserActivityLog.user_id == current_user.id)
    
    if action_filter:
        query = query.filter(UserActivityLog.action.ilike(f"%{action_filter}%"))
    
    total_count = query.count()
    activity_logs = query.order_by(desc(UserActivityLog.created_at)).offset(offset).limit(page_size).all()
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + page_size - 1) // page_size
    
    update_user_activity(current_user, db, "viewed_activity")
    
    return templates.TemplateResponse("activity.html", {
        "request": request,
        "user": current_user,
        "activity_logs": activity_logs,
        "current_page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "action_filter": action_filter
    }) 