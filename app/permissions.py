"""
Система разрешений для расширенной ролевой модели
"""

from functools import wraps
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.auth import get_current_user_from_cookie
import json

# Константы разрешений
class Permissions:
    # Базовые разрешения
    VIEW_DASHBOARD = "view_dashboard"
    MANAGE_OWN_INVENTORY = "manage_own_inventory"
    MAKE_CONTRIBUTIONS = "make_contributions"
    
    # Модерация
    MODERATE_BUDGET = "moderate_budget"
    VIEW_REPORTS = "view_reports"
    
    # Администрирование
    MANAGE_USERS = "manage_users"
    MANAGE_INVENTORY = "manage_inventory"
    POST_NEWS = "post_news"
    
    # Системные
    MANAGE_ADMINS = "manage_admins"
    SYSTEM_SETTINGS = "system_settings"

# Роли и их разрешения
ROLE_PERMISSIONS = {
    'guest': [
        Permissions.VIEW_DASHBOARD,
    ],
    'member': [
        Permissions.VIEW_DASHBOARD,
        Permissions.MANAGE_OWN_INVENTORY,
        Permissions.MAKE_CONTRIBUTIONS,
    ],
    'moderator': [
        Permissions.VIEW_DASHBOARD,
        Permissions.MANAGE_OWN_INVENTORY,
        Permissions.MAKE_CONTRIBUTIONS,
        Permissions.MODERATE_BUDGET,
        Permissions.VIEW_REPORTS,
    ],
    'admin': [
        Permissions.VIEW_DASHBOARD,
        Permissions.MANAGE_OWN_INVENTORY,
        Permissions.MAKE_CONTRIBUTIONS,
        Permissions.MODERATE_BUDGET,
        Permissions.VIEW_REPORTS,
        Permissions.MANAGE_USERS,
        Permissions.MANAGE_INVENTORY,
        Permissions.POST_NEWS,
    ],
    'superadmin': [
        Permissions.VIEW_DASHBOARD,
        Permissions.MANAGE_OWN_INVENTORY,
        Permissions.MAKE_CONTRIBUTIONS,
        Permissions.MODERATE_BUDGET,
        Permissions.VIEW_REPORTS,
        Permissions.MANAGE_USERS,
        Permissions.MANAGE_INVENTORY,
        Permissions.POST_NEWS,
        Permissions.MANAGE_ADMINS,
        Permissions.SYSTEM_SETTINGS,
    ]
}

def has_permission(permission: str) -> bool:
    """
    Проверяет, есть ли у пользователя указанное разрешение
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем пользователя из kwargs или args
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise HTTPException(status_code=403, detail="Пользователь не найден")
            
            # Проверяем разрешение
            if not check_user_permission(user, permission):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Недостаточно прав для выполнения действия: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: str):
    """
    Декоратор для FastAPI роутов - проверяет разрешение пользователя
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            request: Request,
            db: Session = Depends(get_db),
            *args, **kwargs
        ):
            # Получаем пользователя из kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            # Если не нашли в kwargs, ищем в args
            if not current_user:
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            # Если всё ещё не нашли, получаем через dependency
            if not current_user:
                current_user = await get_current_user_from_cookie(request, db)
            
            # Принудительно обновляем объект из базы данных
            db.refresh(current_user)
            
            print(f"DEBUG DECORATOR: User {current_user.username}, role: {getattr(current_user, 'role', 'NOT_FOUND')}")
            
            if not check_user_permission(current_user, permission):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Недостаточно прав для выполнения действия: {permission}"
                )
            
            # Обновляем активность пользователя
            update_user_activity(current_user, db, f"accessed_{permission}")
            
            return await func(request, db, *args, **kwargs)
        return wrapper
    return decorator

def require_role(role: str):
    """
    Декоратор для проверки роли пользователя
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            request: Request,
            current_user: User = Depends(get_current_user_from_cookie),
            db: Session = Depends(get_db),
            *args, **kwargs
        ):
            if not check_user_role(current_user, role):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Требуется роль: {role}"
                )
            
            return await func(request, current_user, db, *args, **kwargs)
        return wrapper
    return decorator

def check_user_permission(user: User, permission: str) -> bool:
    """
    Проверяет, есть ли у пользователя указанное разрешение
    """
    # Проверяем, что user является объектом User
    if not hasattr(user, 'role'):
        print(f"DEBUG PERM: User object has no 'role' attribute")
        return False
    
    print(f"DEBUG PERM: Checking permission '{permission}' for user '{user.username}' with role '{user.role}'")
    
    # Суперадмины имеют все права
    if user.role == 'superadmin':
        print(f"DEBUG PERM: User is superadmin, granting permission '{permission}'")
        return True
    
    # Проверяем роль пользователя
    if user.role not in ROLE_PERMISSIONS:
        print(f"DEBUG PERM: User role '{user.role}' not found in ROLE_PERMISSIONS")
        return False
    
    # Проверяем разрешения роли
    if permission not in ROLE_PERMISSIONS[user.role]:
        print(f"DEBUG PERM: Permission '{permission}' not found in role '{user.role}' permissions")
        return False
    
    # Проверяем индивидуальные разрешения пользователя
    if user.permissions:
        try:
            user_perms = user.permissions if isinstance(user.permissions, dict) else json.loads(user.permissions)
            print(f"DEBUG PERM: User permissions: {user_perms}")
            if permission in user_perms and not user_perms[permission]:
                print(f"DEBUG PERM: Permission '{permission}' explicitly denied in user permissions")
                return False
        except (json.JSONDecodeError, TypeError) as e:
            print(f"DEBUG PERM: Error parsing user permissions: {e}")
            # Если не удается распарсить permissions, игнорируем их
            pass
    
    print(f"DEBUG PERM: Permission '{permission}' granted")
    return True

def check_user_role(user: User, required_role: str) -> bool:
    """
    Проверяет, соответствует ли роль пользователя требуемой
    """
    # Проверяем, что user является объектом User
    if not hasattr(user, 'role'):
        return False
    
    role_hierarchy = {
        'guest': 0,
        'member': 1,
        'moderator': 2,
        'admin': 3,
        'superadmin': 4
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def get_user_permissions(user: User) -> List[str]:
    """
    Возвращает список всех разрешений пользователя
    """
    # Проверяем, что user является объектом User
    if not hasattr(user, 'role'):
        return []
    
    if user.role not in ROLE_PERMISSIONS:
        return []
    
    permissions = ROLE_PERMISSIONS[user.role].copy()
    
    # Применяем индивидуальные настройки пользователя
    if user.permissions:
        user_perms = user.permissions if isinstance(user.permissions, dict) else json.loads(user.permissions)
        for perm, enabled in user_perms.items():
            if not enabled and perm in permissions:
                permissions.remove(perm)
    
    return permissions

def update_user_activity(user: User, db: Session, action: str, details: Optional[Dict[str, Any]] = None):
    """
    Обновляет активность пользователя и логирует действие
    """
    from app.models.models import UserActivityLog
    from datetime import datetime
    
    try:
        # Обновляем last_activity
        user.last_activity = datetime.utcnow()
        
        # Логируем действие
        activity_log = UserActivityLog(
            user_id=user.id,
            action=action,
            details=details or {}
        )
        
        db.add(activity_log)
        db.commit()
        
    except Exception as e:
        # Игнорируем ошибки логирования
        db.rollback()
        print(f"Error logging user activity: {e}")

def get_role_display_name(role: str) -> str:
    """
    Возвращает отображаемое имя роли
    """
    role_names = {
        'guest': 'Гость',
        'member': 'Участник',
        'moderator': 'Модератор',
        'admin': 'Администратор',
        'superadmin': 'Суперадминистратор'
    }
    return role_names.get(role, role)

def get_role_description(role: str) -> str:
    """
    Возвращает описание роли
    """
    role_descriptions = {
        'guest': 'Может только просматривать публичную информацию',
        'member': 'Может управлять своим инвентарём и делать взносы',
        'moderator': 'Может модерировать взносы и просматривать отчёты',
        'admin': 'Полный доступ к управлению системой',
        'superadmin': 'Полный контроль над системой, включая управление администраторами'
    }
    return role_descriptions.get(role, '')

# Dependency для получения пользователя с проверкой разрешений
async def get_user_with_permission(
    permission: str,
    current_user: User = Depends(get_current_user_from_cookie)
) -> User:
    """
    Dependency для получения пользователя с проверкой разрешения
    """
    if not check_user_permission(current_user, permission):
        raise HTTPException(
            status_code=403,
            detail=f"Недостаточно прав: {permission}"
        )
    return current_user

# Dependency для получения пользователя с проверкой роли
async def get_user_with_role(
    role: str,
    current_user: User = Depends(get_current_user_from_cookie)
) -> User:
    """
    Dependency для получения пользователя с проверкой роли
    """
    if not check_user_role(current_user, role):
        raise HTTPException(
            status_code=403,
            detail=f"Требуется роль: {role}"
        )
    return current_user 