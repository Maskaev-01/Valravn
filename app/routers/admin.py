from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from app.database import get_db
from app.models.models import Budget, User, Inventory, VKWhitelist
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
                            existing_user.first_name = entry.username.split()[0] if entry.username.split() else "VK"
                            existing_user.last_name = " ".join(entry.username.split()[1:]) if len(entry.username.split()) > 1 else "User"
                            existing_user.is_whitelisted = True
                            existing_user.is_admin = 1 if entry.is_admin else 0
                            updated_count += 1
                        else:
                            # У пользователя уже есть другой vk_id - пропускаем
                            errors.append(f"Пользователь {username} уже имеет VK ID {existing_user.vk_id}")
                            continue
                    else:
                        # Создаем нового пользователя
                        new_user = User(
                            username=username,
                            vk_id=entry.vk_id,
                            first_name=entry.username.split()[0] if entry.username.split() else "VK",
                            last_name=" ".join(entry.username.split()[1:]) if len(entry.username.split()) > 1 else "User",
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