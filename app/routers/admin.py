from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
from app.database import get_db
from app.models.models import Budget, User, Inventory, VKWhitelist, AccountLinkRequest, BudgetType, InventoryItemType, InventoryMaterialType
from app.auth import get_admin_user, get_password_hash
from app.permissions import require_permission, check_user_permission, update_user_activity, get_role_display_name, get_role_description
from app.vk_oauth import vk_oauth

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

# Редирект для исправления неправильных ссылок
@router.get("/admin/dashboard")
async def admin_dashboard_redirect():
    return RedirectResponse(url="/admin", status_code=301)

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
async def admin_users(
    request: Request, 
    admin_user: User = Depends(get_admin_user), 
    db: Session = Depends(get_db),
    success: str = Query(None),
    error: str = Query(None)
):
    # Проверяем разрешение на управление пользователями
    from app.permissions import check_user_permission
    if not check_user_permission(admin_user, "manage_users"):
        raise HTTPException(status_code=403, detail="Недостаточно прав для управления пользователями")
    # Получаем пользователей с их статистикой
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    # Обновляем объекты пользователей из базы данных
    for user in users:
        db.refresh(user)
    
    # Получаем статистику для каждого пользователя
    from app.models.models import UserStats, Budget, Inventory, UserAchievement
    user_stats = {}
    for user in users:
        stats = db.query(UserStats).filter(UserStats.user_id == user.id).first()
        if not stats:
            # Создаем новую статистику если её нет
            stats = UserStats(user_id=user.id)
            db.add(stats)
            db.commit()
            db.refresh(stats)
        
        # Обновляем статистику пользователя
        # Ищем взносы по contributor_name (для старых записей) и created_by_user_id (для новых)
        user_contributions = db.query(Budget).filter(
            (Budget.created_by_user_id == user.id) | 
            (Budget.contributor_name == user.username),
            Budget.price > 0
        ).all()
        
        # Также проверяем одобренные записи отдельно
        approved_contributions = db.query(Budget).filter(
            (Budget.created_by_user_id == user.id) | 
            (Budget.contributor_name == user.username),
            Budget.is_approved == True,
            Budget.price > 0
        ).all()
        

        

        
        # Используем все записи для отображения, но считаем только одобренные
        stats.total_contributions = sum([c.price for c in approved_contributions])
        stats.contributions_count = len(approved_contributions)
        stats.inventory_count = db.query(Inventory).filter(Inventory.owner_user_id == user.id).count()
        stats.club_inventory_count = db.query(Inventory).filter(Inventory.is_club_item == True).count()
        stats.achievements_count = db.query(UserAchievement).filter(
            UserAchievement.user_id == user.id,
            UserAchievement.is_active == True
        ).count()
        
        db.commit()
        user_stats[user.id] = stats
    
    # Получаем разрешения для отображения
    from app.permissions import get_user_permissions
    user_permissions = {}
    for user in users:
        user_permissions[user.id] = get_user_permissions(user)
    
    update_user_activity(admin_user, db, "viewed_users_management")
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": admin_user,
        "users": users,
        "user_stats": user_stats,
        "user_permissions": user_permissions,
        "success_message": success,
        "error_message": error
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
    
    # Определяем тип операции
    is_vk_user_setting_password = user_to_update.vk_id and not user_to_update.hashed_password
    
    # Обновляем пароль
    user_to_update.hashed_password = get_password_hash(new_password)
    db.commit()
    
    # Формируем сообщение об успехе
    if is_vk_user_setting_password:
        success_message = "password_set_for_vk_user"
    else:
        success_message = "password_changed"
    
    return RedirectResponse(url=f"/admin/users?success={success_message}", status_code=302)

@router.post("/admin/users/update-role")
async def update_user_role(
    request: Request,
    user_id: int = Form(...),
    new_role: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Обновляет роль пользователя"""
    # Проверяем разрешение на управление пользователями
    from app.permissions import check_user_permission
    if not check_user_permission(admin_user, "manage_users"):
        raise HTTPException(status_code=403, detail="Недостаточно прав для управления пользователями")
    
    try:
        # Проверяем, что роль валидна
        valid_roles = ['guest', 'member', 'moderator', 'admin', 'superadmin']
        if new_role not in valid_roles:
            return RedirectResponse(url="/admin/users?error=invalid_role", status_code=302)
        
        # Находим пользователя
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update:
            return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)
        
        # Проверяем права на изменение роли
        if admin_user.role != 'superadmin':
            # Обычные админы не могут назначать роли admin и superadmin
            if new_role in ['admin', 'superadmin']:
                return RedirectResponse(url="/admin/users?error=insufficient_permissions", status_code=302)
            
            # Обычные админы не могут изменять роли других админов
            if user_to_update.role in ['admin', 'superadmin']:
                return RedirectResponse(url="/admin/users?error=cannot_modify_admin", status_code=302)
        
        # Суперадмины не могут понижать других суперадминов
        if admin_user.role == 'superadmin' and user_to_update.role == 'superadmin' and new_role != 'superadmin':
            return RedirectResponse(url="/admin/users?error=cannot_demote_superadmin", status_code=302)
        
        # Сохраняем старую роль для логирования
        old_role = user_to_update.role
        
        # Обновляем роль
        user_to_update.role = new_role
        
        # Обновляем поле is_admin для обратной совместимости
        if new_role in ['admin', 'superadmin']:
            user_to_update.is_admin = 1
        else:
            user_to_update.is_admin = 0
        
        # Обновляем разрешения в соответствии с новой ролью
        from app.permissions import ROLE_PERMISSIONS
        if new_role in ROLE_PERMISSIONS:
            user_to_update.permissions = ROLE_PERMISSIONS[new_role]
        
        db.commit()
        
        # Логируем изменение
        update_user_activity(admin_user, db, "updated_user_role", {
            "target_user_id": user_id,
            "target_username": user_to_update.username,
            "old_role": old_role,
            "new_role": new_role
        })
        
        return RedirectResponse(
            url=f"/admin/users?success=role_updated&user={user_to_update.username}&old_role={old_role}&new_role={new_role}", 
            status_code=302
        )
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/users?error=update_failed&message={str(e)}", status_code=302)

@router.post("/admin/users/update-permissions")
async def update_user_permissions(
    request: Request,
    user_id: int = Form(...),
    permissions: str = Form(...),  # JSON строка с разрешениями
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Обновляет индивидуальные разрешения пользователя"""
    # Проверяем разрешение на управление пользователями
    from app.permissions import check_user_permission
    if not check_user_permission(admin_user, "manage_users"):
        raise HTTPException(status_code=403, detail="Недостаточно прав для управления пользователями")
    
    try:
        import json
        
        # Находим пользователя
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update:
            return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)
        
        # Проверяем права на изменение разрешений
        if admin_user.role != 'superadmin':
            # Обычные админы не могут изменять разрешения админов
            if user_to_update.role in ['admin', 'superadmin']:
                return RedirectResponse(url="/admin/users?error=cannot_modify_admin_permissions", status_code=302)
        
        # Парсим JSON с разрешениями
        try:
            permissions_dict = json.loads(permissions)
        except json.JSONDecodeError:
            return RedirectResponse(url="/admin/users?error=invalid_permissions_format", status_code=302)
        
        # Обновляем разрешения
        user_to_update.permissions = permissions_dict
        db.commit()
        
        # Логируем изменение
        update_user_activity(admin_user, db, "updated_user_permissions", {
            "target_user_id": user_id,
            "target_username": user_to_update.username,
            "permissions": permissions_dict
        })
        
        return RedirectResponse(
            url=f"/admin/users?success=permissions_updated&user={user_to_update.username}", 
            status_code=302
        )
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/users?error=permissions_update_failed&message={str(e)}", status_code=302)

@router.post("/admin/users/deactivate")
async def deactivate_user(
    request: Request,
    user_id: int = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Деактивирует пользователя (устанавливает роль guest)"""
    # Проверяем разрешение на управление пользователями
    from app.permissions import check_user_permission
    if not check_user_permission(admin_user, "manage_users"):
        raise HTTPException(status_code=403, detail="Недостаточно прав для управления пользователями")
    
    try:
        # Находим пользователя
        user_to_update = db.query(User).filter(User.id == user_id).first()
        if not user_to_update:
            return RedirectResponse(url="/admin/users?error=user_not_found", status_code=302)
        
        # Проверяем права на деактивацию
        if admin_user.role != 'superadmin':
            # Обычные админы не могут деактивировать админов
            if user_to_update.role in ['admin', 'superadmin']:
                return RedirectResponse(url="/admin/users?error=cannot_deactivate_admin", status_code=302)
        
        # Нельзя деактивировать самого себя
        if user_to_update.id == admin_user.id:
            return RedirectResponse(url="/admin/users?error=cannot_deactivate_self", status_code=302)
        
        # Сохраняем старую роль для логирования
        old_role = user_to_update.role
        
        # Деактивируем пользователя
        user_to_update.role = 'guest'
        user_to_update.is_admin = 0
        user_to_update.permissions = {}
        
        db.commit()
        
        # Логируем изменение
        update_user_activity(admin_user, db, "deactivated_user", {
            "target_user_id": user_id,
            "target_username": user_to_update.username,
            "old_role": old_role
        })
        
        return RedirectResponse(
            url=f"/admin/users?success=user_deactivated&user={user_to_update.username}", 
            status_code=302
        )
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/users?error=deactivation_failed&message={str(e)}", status_code=302)

# Новый роут для синхронизации данных VK пользователей
@router.post("/admin/sync-vk-users")
async def sync_vk_users(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Синхронизирует данные между таблицами vk_whitelist и users"""
    try:
        # Получаем всех пользователей из whitelist
        whitelist_entries = db.query(VKWhitelist).all()
        synced_count = 0
        updated_count = 0
        errors = []
        
        for entry in whitelist_entries:
            try:
                # Сначала ищем пользователя по vk_id
                user = db.query(User).filter(User.vk_id == entry.vk_id).first()
                
                if user:
                    # Пользователь найден по vk_id - обновляем флаги
                    if not user.is_whitelisted or user.is_admin != (1 if entry.is_admin else 0):
                        user.is_whitelisted = True
                        user.is_admin = 1 if entry.is_admin else 0
                        updated_count += 1
                else:
                    # Пользователь не найден по vk_id
                    # Проверяем, нет ли уже пользователя с таким username
                    username = f"vk_{entry.vk_id}"
                    existing_user = db.query(User).filter(User.username == username).first()
                    
                    if existing_user:
                        # Пользователь с таким username уже есть - обновляем его vk_id
                        if not existing_user.vk_id:
                            existing_user.vk_id = entry.vk_id
                            # Получаем данные из VK API если доступно
                            if vk_oauth.has_service_token():
                                user_info = await vk_oauth.get_user_info(entry.vk_id)
                                if user_info:
                                    existing_user.first_name = user_info['first_name']
                                    existing_user.last_name = user_info['last_name']
                                    existing_user.username = f"{user_info['first_name']} {user_info['last_name']}".strip()
                                    if user_info.get('avatar_url'):
                                        existing_user.avatar_url = user_info['avatar_url']
                                else:
                                    # Используем данные из whitelist
                                    name_parts = entry.username.split()
                                    existing_user.first_name = name_parts[0] if name_parts else "VK"
                                    existing_user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"
                                    existing_user.username = entry.username
                            else:
                                # Используем данные из whitelist
                                name_parts = entry.username.split()
                                existing_user.first_name = name_parts[0] if name_parts else "VK"
                                existing_user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"
                                existing_user.username = entry.username
                            existing_user.is_whitelisted = True
                            existing_user.is_admin = 1 if entry.is_admin else 0
                            updated_count += 1
                        else:
                            # У пользователя уже есть другой vk_id - пропускаем
                            errors.append(f"Пользователь {username} уже имеет VK ID {existing_user.vk_id}")
                            continue
                    else:
                        # Создаем нового пользователя
                        # Получаем данные из VK API если доступно
                        first_name = "VK"
                        last_name = "User"
                        username = f"vk_{entry.vk_id}"
                        avatar_url = None
                        
                        if vk_oauth.has_service_token():
                            user_info = await vk_oauth.get_user_info(entry.vk_id)
                            if user_info:
                                first_name = user_info['first_name']
                                last_name = user_info['last_name']
                                username = f"{first_name} {last_name}".strip()
                                avatar_url = user_info.get('photo_100')
                            else:
                                # Используем данные из whitelist
                                name_parts = entry.username.split()
                                first_name = name_parts[0] if name_parts else "VK"
                                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"
                                username = entry.username
                        else:
                            # Используем данные из whitelist
                            name_parts = entry.username.split()
                            first_name = name_parts[0] if name_parts else "VK"
                            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"
                            username = entry.username
                        
                        # Проверяем уникальность username
                        counter = 1
                        base_username = username
                        while db.query(User).filter(User.username == username).first():
                            username = f"{base_username}_{counter}"
                            counter += 1
                        
                        new_user = User(
                            username=username,
                            vk_id=entry.vk_id,
                            first_name=first_name,
                            last_name=last_name,
                            avatar_url=avatar_url,
                            is_admin=1 if entry.is_admin else 0,
                            is_whitelisted=True,
                            hashed_password=None,  # Explicitly set to None for VK users
                            email=None
                        )
                        db.add(new_user)
                        synced_count += 1
                        
            except Exception as e:
                errors.append(f"Ошибка для VK ID {entry.vk_id}: {str(e)}")
                continue
        
        # Коммитим все изменения
        db.commit()
        
        # Формируем сообщение о результате
        success_message = f"sync_complete&synced={synced_count}&updated={updated_count}"
        if errors:
            error_message = "; ".join(errors[:3])  # Показываем только первые 3 ошибки
            success_message += f"&warnings={len(errors)}"
            
        return RedirectResponse(
            url=f"/admin/users?success={success_message}", 
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/users?error=sync_failed&message={str(e)}", 
            status_code=302
        )

# Новые роуты для управления связыванием аккаунтов
@router.get("/admin/user-accounts", response_class=HTMLResponse)
async def manage_user_accounts(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Страница управления связыванием аккаунтов"""
    # Находим потенциальные дубликаты
    potential_duplicates = []
    
    # Получаем всех пользователей
    all_users = db.query(User).all()
    
    # 1. Пользователи с одинаковыми email
    users_by_email = {}
    for user in all_users:
        if user.email:
            email = user.email.lower()
            if email not in users_by_email:
                users_by_email[email] = []
            users_by_email[email].append(user)
    
    for email, users in users_by_email.items():
        if len(users) > 1:
            potential_duplicates.append({
                'type': 'email_match',
                'email': email,
                'users': users,
                'confidence': 'high'
            })
    
    # 2. Пользователи с точно одинаковыми именами (высокая вероятность)
    users_by_exact_name = {}
    for user in all_users:
        if user.first_name and user.last_name:
            full_name = f"{user.first_name} {user.last_name}".strip().lower()
            if full_name not in users_by_exact_name:
                users_by_exact_name[full_name] = []
            users_by_exact_name[full_name].append(user)
    
    for name, users in users_by_exact_name.items():
        if len(users) > 1:
            # Проверяем что в группе есть VK и обычные пользователи
            vk_users = [u for u in users if u.vk_id]
            regular_users = [u for u in users if not u.vk_id]
            
            if vk_users and regular_users:
                potential_duplicates.append({
                    'type': 'exact_name_match',
                    'name': name,
                    'users': users,
                    'vk_users': vk_users,
                    'regular_users': regular_users,
                    'confidence': 'high'
                })
    
    # 3. Пользователи с похожими именами (средняя вероятность)
    def normalize_name(name):
        """Нормализует имя для сравнения"""
        import re
        # Убираем лишние символы и приводим к нижнему регистру
        name = re.sub(r'[^\w\s]', '', name.lower())
        # Заменяем английские буквы на русские и наоборот для транслита
        translite_map = {
            'nikita': 'никита', 'ivan': 'иван', 'petr': 'петр', 'pavel': 'павел',
            'alexander': 'александр', 'dmitry': 'дмитрий', 'sergey': 'сергей',
            'yakimov': 'якимов', 'petrov': 'петров', 'ivanov': 'иванов'
        }
        for eng, rus in translite_map.items():
            name = name.replace(eng, rus)
            name = name.replace(rus, eng)
        return name.strip()
    
    users_by_normalized_name = {}
    for user in all_users:
        # Проверяем разные варианты имен
        name_variants = []
        
        if user.first_name and user.last_name:
            # Полное имя из профиля
            name_variants.append(f"{user.first_name} {user.last_name}")
        
        if user.username and not user.username.startswith('vk_'):
            # Username (если не автоматический vk_)
            name_variants.append(user.username)
        
        for variant in name_variants:
            normalized = normalize_name(variant)
            if len(normalized) > 3:  # Игнорируем слишком короткие имена
                if normalized not in users_by_normalized_name:
                    users_by_normalized_name[normalized] = []
                users_by_normalized_name[normalized].append(user)
    
    for name, users in users_by_normalized_name.items():
        if len(users) > 1:
            # Убираем уже найденные точные совпадения
            already_found = False
            for duplicate in potential_duplicates:
                if duplicate['type'] in ['email_match', 'exact_name_match']:
                    if set(u.id for u in users) == set(u.id for u in duplicate['users']):
                        already_found = True
                        break
            
            if not already_found:
                vk_users = [u for u in users if u.vk_id]
                regular_users = [u for u in users if not u.vk_id]
                
                if vk_users and regular_users:
                    potential_duplicates.append({
                        'type': 'similar_name_match',
                        'name': name,
                        'users': users,
                        'vk_users': vk_users,
                        'regular_users': regular_users,
                        'confidence': 'medium'
                    })
    
    # 4. Пользователи без email с VK аккаунтами (низкая вероятность, но стоит проверить)
    vk_users_no_link = []
    regular_users_no_email = []
    
    for user in all_users:
        if user.vk_id and not user.email:
            vk_users_no_link.append(user)
        elif not user.vk_id and not user.email:
            regular_users_no_email.append(user)
    
    if vk_users_no_link and regular_users_no_email:
        potential_duplicates.append({
            'type': 'no_email_check',
            'users': vk_users_no_link + regular_users_no_email,
            'vk_users': vk_users_no_link,
            'regular_users': regular_users_no_email,
            'confidence': 'low'
        })
    
    # Сортируем по уровню уверенности
    confidence_order = {'high': 1, 'medium': 2, 'low': 3}
    potential_duplicates.sort(key=lambda x: confidence_order.get(x['confidence'], 4))
    
    return templates.TemplateResponse("admin/user_accounts.html", {
        "request": request,
        "user": admin_user,
        "potential_duplicates": potential_duplicates,
        "all_users": all_users
    })

@router.post("/admin/link-accounts")
async def link_user_accounts(
    request: Request,
    primary_user_id: int = Form(...),
    secondary_user_id: int = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Связывает два аккаунта пользователя"""
    try:
        primary_user = db.query(User).filter(User.id == primary_user_id).first()
        secondary_user = db.query(User).filter(User.id == secondary_user_id).first()
        
        if not primary_user or not secondary_user:
            return RedirectResponse(
                url="/admin/user-accounts?error=users_not_found", 
                status_code=302
            )
        
        # ИСПРАВЛЕНИЕ: Сначала обновляем все связанные записи ПЕРЕД удалением пользователя
        # Обновляем записи бюджета
        budget_update_count = db.query(Budget).filter(Budget.user_id == secondary_user.id).update({"user_id": primary_user.id})
        
        # Обновляем записи инвентаря
        inventory_update_count = db.query(Inventory).filter(Inventory.created_by_user_id == secondary_user.id).update({"created_by_user_id": primary_user.id})
        
        # Обновляем записи account_link_requests если есть
        try:
            db.execute(text("UPDATE account_link_requests SET user_id = :primary_id WHERE user_id = :secondary_id"), 
                      {"primary_id": primary_user.id, "secondary_id": secondary_user.id})
            db.execute(text("UPDATE account_link_requests SET target_user_id = :primary_id WHERE target_user_id = :secondary_id"), 
                      {"primary_id": primary_user.id, "secondary_id": secondary_user.id})
            db.execute(text("UPDATE account_link_requests SET processed_by = :primary_id WHERE processed_by = :secondary_id"), 
                      {"primary_id": primary_user.id, "secondary_id": secondary_user.id})
        except Exception as e:
            # Таблица может не существовать, игнорируем
            pass
        
        # Коммитим обновления связанных записей
        db.commit()
        
        # Сохраняем данные вторичного аккаунта в переменные
        secondary_vk_id = secondary_user.vk_id
        secondary_avatar_url = secondary_user.avatar_url
        secondary_is_whitelisted = secondary_user.is_whitelisted
        secondary_email = secondary_user.email
        secondary_first_name = secondary_user.first_name
        secondary_last_name = secondary_user.last_name
        secondary_is_admin = secondary_user.is_admin
        
        # Теперь БЕЗОПАСНО удаляем вторичный аккаунт
        db.delete(secondary_user)
        db.commit()
        
        # Переносим данные с вторичного аккаунта на основной
        if secondary_vk_id and not primary_user.vk_id:
            primary_user.vk_id = secondary_vk_id
            primary_user.avatar_url = secondary_avatar_url or primary_user.avatar_url
            primary_user.is_whitelisted = secondary_is_whitelisted or primary_user.is_whitelisted
        
        if secondary_email and not primary_user.email:
            primary_user.email = secondary_email
            
        if secondary_first_name and not primary_user.first_name:
            primary_user.first_name = secondary_first_name
            
        if secondary_last_name and not primary_user.last_name:
            primary_user.last_name = secondary_last_name
        
        # Переносим права админа (берем максимальный уровень)
        primary_user.is_admin = max(primary_user.is_admin, secondary_is_admin)
        
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/user-accounts?success=accounts_linked&budget_updated={budget_update_count}&inventory_updated={inventory_update_count}", 
            status_code=302
        )
        
    except Exception as e:
        db.rollback()  # ДОБАВЛЯЕМ ROLLBACK при ошибке
        return RedirectResponse(
            url=f"/admin/user-accounts?error=link_failed&message={str(e)}", 
            status_code=302
        )

# БЫСТРОЕ ИСПРАВЛЕНИЕ: Одобрить все взносы
@router.post("/admin/approve-all-contributions")
async def approve_all_contributions(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """ВРЕМЕННЫЙ роут для быстрого одобрения всех взносов"""
    try:
        # Одобряем все неодобренные взносы
        pending_contributions = db.query(Budget).filter(
            Budget.type == "Взнос",
            Budget.is_approved == False
        ).all()
        
        approved_count = 0
        for contribution in pending_contributions:
            contribution.is_approved = True
            approved_count += 1
        
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/users?success=approved_all&count={approved_count}", 
            status_code=302
        )
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/admin/users?error=approve_failed&message={str(e)}", 
            status_code=302
        )

# СПРАВОЧНИКИ
@router.get("/admin/dictionaries", response_class=HTMLResponse)
async def dictionaries_page(
    request: Request, 
    current_user: User = Depends(get_admin_user), 
    db: Session = Depends(get_db)
):
    """Страница управления справочниками"""
    budget_types = db.query(BudgetType).order_by(BudgetType.sort_order, BudgetType.name).all()
    inventory_types = db.query(InventoryItemType).order_by(InventoryItemType.sort_order, InventoryItemType.name).all()
    
    # Добавляем материалы инвентаря
    material_types = db.query(InventoryMaterialType).order_by(InventoryMaterialType.sort_order, InventoryMaterialType.name).all()
    
    return templates.TemplateResponse("admin/dictionaries.html", {
        "request": request,
        "user": current_user,
        "budget_types": budget_types,
        "inventory_types": inventory_types,
        "material_types": material_types
    })

@router.post("/admin/dictionaries/budget-types/add")
async def add_budget_type(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    sort_order: int = Form(0),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Добавить тип операции бюджета"""
    try:
        budget_type = BudgetType(
            name=name.strip(),
            description=description.strip() if description else None,
            sort_order=sort_order
        )
        db.add(budget_type)
        db.commit()
        return RedirectResponse(url="/admin/dictionaries", status_code=302)
    except Exception as e:
        db.rollback()
        # Обработка ошибки дублирования
        return RedirectResponse(url="/admin/dictionaries?error=duplicate", status_code=302)

@router.post("/admin/dictionaries/inventory-types/add")
async def add_inventory_type(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    sort_order: int = Form(0),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Добавить тип предмета инвентаря"""
    try:
        inventory_type = InventoryItemType(
            name=name.strip(),
            description=description.strip() if description else None,
            sort_order=sort_order
        )
        db.add(inventory_type)
        db.commit()
        return RedirectResponse(url="/admin/dictionaries", status_code=302)
    except Exception as e:
        db.rollback()
        return RedirectResponse(url="/admin/dictionaries?error=duplicate", status_code=302)

@router.post("/admin/dictionaries/budget-types/{type_id}/toggle")
async def toggle_budget_type(
    type_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Активировать/деактивировать тип операции бюджета"""
    budget_type = db.query(BudgetType).filter(BudgetType.id == type_id).first()
    if budget_type:
        budget_type.is_active = not budget_type.is_active
        db.commit()
    return RedirectResponse(url="/admin/dictionaries", status_code=302)

@router.post("/admin/dictionaries/inventory-types/{type_id}/toggle")
async def toggle_inventory_type(
    type_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Активировать/деактивировать тип предмета инвентаря"""
    inventory_type = db.query(InventoryItemType).filter(InventoryItemType.id == type_id).first()
    if inventory_type:
        inventory_type.is_active = not inventory_type.is_active
        db.commit()
    return RedirectResponse(url="/admin/dictionaries", status_code=302)

@router.post("/admin/dictionaries/material-types/add")
async def add_material_type(
    request: Request,
    name: str = Form(...),
    category: str = Form(None),
    description: str = Form(None),
    sort_order: int = Form(0),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Добавить тип материала"""
    try:
        material_type = InventoryMaterialType(
            name=name.strip(),
            category=category.strip() if category else None,
            description=description.strip() if description else None,
            sort_order=sort_order
        )
        db.add(material_type)
        db.commit()
        return RedirectResponse(url="/admin/dictionaries", status_code=302)
    except Exception as e:
        db.rollback()
        return RedirectResponse(url="/admin/dictionaries?error=duplicate", status_code=302)

@router.post("/admin/dictionaries/material-types/{type_id}/toggle")
async def toggle_material_type(
    type_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Активировать/деактивировать тип материала"""
    material_type = db.query(InventoryMaterialType).filter(InventoryMaterialType.id == type_id).first()
    if material_type:
        material_type.is_active = not material_type.is_active
        db.commit()
    return RedirectResponse(url="/admin/dictionaries", status_code=302) 