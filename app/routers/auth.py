from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database import get_db
from app.models.models import User, VKWhitelist, AccountLinkRequest
from app.models.schemas import UserCreate, UserLogin
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_or_update_vk_user,
    add_vk_user_to_whitelist,
    get_admin_user,
    get_current_user_from_cookie,
    get_current_user
)
from app.vk_oauth import vk_oauth

router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # VK ID SDK всегда доступен (работает на клиентской стороне)
    vk_auth_url = True
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "vk_auth_url": vk_auth_url
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/login")
async def login_for_access_token(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Неверное имя пользователя или пароль",
            "vk_auth_url": True  # VK ID SDK всегда доступен
        })
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    secret_code: str = Form(...),
    db: Session = Depends(get_db)
):
    # Простая защита регистрации секретным кодом
    if secret_code != "valravn2024":
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Неверный секретный код"
        })
    
    # Проверяем, существует ли пользователь с таким именем
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пользователь с таким именем уже существует"
        })
    
    # Преобразуем пустую строку email в None для корректной работы с unique constraint
    email_value = email if email and email.strip() else None
    
    # Проверяем уникальность email, если он предоставлен
    if email_value:
        existing_email_user = db.query(User).filter(User.email == email_value).first()
        if existing_email_user:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пользователь с таким email уже существует"
            })
    
    # Создаем нового пользователя
    hashed_password = get_password_hash(password)
    db_user = User(username=username, email=email_value, hashed_password=hashed_password)
    
    # Первый пользователь становится админом
    users_count = db.query(User).count()
    if users_count == 0:
        db_user.is_admin = 1
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return templates.TemplateResponse("register.html", {
        "request": request,
        "success": "Регистрация успешна! Теперь вы можете войти в систему."
    })

# API роут для получения данных пользователя VK
@router.get("/api/vk-user-info")
async def get_vk_user_info(
    user_id: str = Query(..., description="VK ID или псевдоним пользователя"),
    current_user: User = Depends(get_admin_user)
):
    """Получает информацию о пользователе VK по ID или псевдониму"""
    try:
        user_info = await vk_oauth.get_user_info(user_id)
        if user_info:
            return {
                "success": True,
                "user": {
                    "vk_id": user_info["id"],
                    "first_name": user_info["first_name"],
                    "last_name": user_info["last_name"],
                    "full_name": f"{user_info['first_name']} {user_info['last_name']}".strip(),
                    "photo_100": user_info["photo_100"],
                    "screen_name": user_info.get("screen_name"),
                    "is_closed": user_info.get("is_closed", False)
                }
            }
        else:
            return {
                "success": False,
                "error": "Пользователь не найден или профиль недоступен"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка получения данных: {str(e)}"
        }

# Админские роуты для управления VK whitelist
@router.get("/admin/vk-whitelist", response_class=HTMLResponse)
async def vk_whitelist_page(
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Страница управления VK whitelist"""
    whitelist = db.query(VKWhitelist).all()
    return templates.TemplateResponse("admin/vk_whitelist.html", {
        "request": request,
        "whitelist": whitelist,
        "has_vk_service_token": vk_oauth.has_service_token()
    })

@router.post("/admin/vk-whitelist/add")
async def add_to_vk_whitelist(
    request: Request,
    vk_id: str = Form(...),
    username: str = Form(None),  # Теперь опционально
    is_admin: bool = Form(False),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Добавляет пользователя в VK whitelist"""
    try:
        final_vk_id = vk_id.strip()
        final_username = username.strip() if username else ""
        
        # Если имя не указано, пытаемся получить из VK API
        if not final_username and vk_oauth.has_service_token():
            user_info = await vk_oauth.get_user_info(final_vk_id)
            if user_info:
                final_vk_id = user_info["id"]  # Используем числовой ID
                final_username = f"{user_info['first_name']} {user_info['last_name']}".strip()
                if not final_username:
                    final_username = f"VK User {final_vk_id}"
            else:
                # Не удалось получить данные из VK
                if not final_username:
                    final_username = f"VK User {final_vk_id}"
        elif not final_username:
            # Нет сервисного токена и не указано имя
            final_username = f"VK User {final_vk_id}"
        
        # Преобразуем псевдоним в числовой ID если возможно
        if not final_vk_id.isdigit() and vk_oauth.has_service_token():
            resolved_id = await vk_oauth.resolve_screen_name(final_vk_id)
            if resolved_id:
                final_vk_id = resolved_id
        
        add_vk_user_to_whitelist(
            db=db,
            vk_id=final_vk_id,
            username=final_username,
            is_admin=is_admin,
            added_by=current_user.id
        )
        
        whitelist = db.query(VKWhitelist).all()
        return templates.TemplateResponse("admin/vk_whitelist.html", {
            "request": request,
            "whitelist": whitelist,
            "has_vk_service_token": vk_oauth.has_service_token(),
            "success": f"Пользователь {final_username} (ID: {final_vk_id}) добавлен в whitelist"
        })
    except Exception as e:
        whitelist = db.query(VKWhitelist).all()
        return templates.TemplateResponse("admin/vk_whitelist.html", {
            "request": request,
            "whitelist": whitelist,
            "has_vk_service_token": vk_oauth.has_service_token(),
            "error": f"Ошибка: {str(e)}"
        })

@router.post("/admin/vk-whitelist/remove/{whitelist_id}")
async def remove_from_vk_whitelist(
    whitelist_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Удаляет пользователя из VK whitelist"""
    whitelist_entry = db.query(VKWhitelist).filter(VKWhitelist.id == whitelist_id).first()
    if whitelist_entry:
        db.delete(whitelist_entry)
        db.commit()
    
    return RedirectResponse(url="/auth/admin/vk-whitelist", status_code=302)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

# НОВЫЙ роут для VK ID авторизации
@router.post("/vk/process")
async def vk_id_process(
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработка авторизации через VK ID SDK"""
    try:
        # Получаем готовые данные пользователя от VK ID SDK
        data = await request.json()
        print(f"VK Data received: {data}")  # Отладка
        
        user_id = str(data.get("user_id"))
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        photo_100 = data.get("photo_100")
        email = data.get("email")  # Email из VK ID SDK
        
        if not user_id:
            print(f"Missing user_id: {user_id}")  # Отладка
            raise HTTPException(status_code=400, detail="Нет VK user_id")
        
        # Пытаемся получить полные данные пользователя из VK API
        if vk_oauth.has_service_token():
            try:
                user_info = await vk_oauth.get_user_info(user_id)
                if user_info:
                    first_name = user_info["first_name"] or first_name
                    last_name = user_info["last_name"] or last_name
                    photo_100 = user_info["photo_100"] or photo_100
                    user_id = user_info["id"]  # Используем числовой ID
                    # Если email не был получен из SDK, пробуем из API
                    if not email:
                        email = user_info.get("email")
            except Exception as e:
                print(f"Failed to get additional user info: {e}")
        
        # Fallback для пустых имен только если не удалось получить из API
        if not first_name and not last_name:
            first_name = "VK"
            last_name = f"User {user_id[-4:]}"  # Последние 4 цифры ID
        elif not first_name:
            first_name = "VK"
        elif not last_name:
            last_name = "User"
        
        print(f"Processing VK user: {user_id} - {first_name} {last_name} ({email})")  # Отладка
        
        # Создаем или обновляем пользователя с передачей email
        user = create_or_update_vk_user(
            db=db,
            vk_id=user_id,
            first_name=first_name,
            last_name=last_name,
            avatar_url=photo_100,
            email=email  # Передаем email для связывания аккаунтов
        )
        print(f"User created/updated: {user.username}")  # Отладка
        
        # Создаем JWT токен
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Возвращаем успешный ответ (без redirect, так как это AJAX)
        response = JSONResponse({"status": "success", "redirect": "/dashboard"})
        response.set_cookie(key="access_token", value=f"Bearer {jwt_token}", httponly=True)
        return response
        
    except Exception as e:
        print(f"VK Auth Error: {str(e)}")  # Отладка
        raise HTTPException(status_code=400, detail=f"Ошибка VK авторизации: {str(e)}")

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, current_user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Профиль пользователя с возможностью связывания аккаунтов"""
    
    # Ищем возможные дубликаты для этого пользователя
    potential_matches = []
    
    # Если у пользователя есть email - ищем других с таким же email
    if current_user.email:
        email_matches = db.query(User).filter(
            User.email == current_user.email,
            User.id != current_user.id
        ).all()
        
        for match in email_matches:
            potential_matches.append({
                'user': match,
                'match_type': 'email',
                'confidence': 'high',
                'description': f'Одинаковый email: {current_user.email}'
            })
    
    # Если у пользователя есть имя - ищем похожие имена
    if current_user.first_name and current_user.last_name:
        full_name = f"{current_user.first_name} {current_user.last_name}".lower()
        
        # Точные совпадения
        exact_matches = db.query(User).filter(
            func.lower(func.concat(User.first_name, ' ', User.last_name)) == full_name,
            User.id != current_user.id,
            # Показываем только если у одного есть VK, у другого нет
            or_(
                and_(User.vk_id.is_(None), current_user.vk_id.is_not(None)),
                and_(User.vk_id.is_not(None), current_user.vk_id.is_(None))
            )
        ).all()
        
        for match in exact_matches:
            potential_matches.append({
                'user': match,
                'match_type': 'name',
                'confidence': 'high',
                'description': f'Точное совпадение имени: {full_name.title()}'
            })
    
    # Проверяем есть ли уже запросы на связывание
    link_requests = db.query(AccountLinkRequest).filter(
        or_(
            AccountLinkRequest.user_id == current_user.id,
            AccountLinkRequest.target_user_id == current_user.id
        ),
        AccountLinkRequest.status == 'pending'
    ).all()
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
        "potential_matches": potential_matches,
        "link_requests": link_requests
    })

@router.post("/request-account-link")
async def request_account_link(
    request: Request,
    target_user_id: int = Form(...),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Запрос на связывание аккаунтов"""
    
    # Проверяем что цель существует
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем что нет уже такого запроса
    existing_request = db.query(AccountLinkRequest).filter(
        AccountLinkRequest.user_id == current_user.id,
        AccountLinkRequest.target_user_id == target_user_id,
        AccountLinkRequest.status == 'pending'
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="Запрос уже отправлен")
    
    # Создаем запрос
    link_request = AccountLinkRequest(
        user_id=current_user.id,
        target_user_id=target_user_id,
        status='pending',
        created_at=datetime.utcnow()
    )
    
    db.add(link_request)
    db.commit()
    
    return RedirectResponse(url="/auth/profile", status_code=302)

@router.post("/confirm-account-link")
async def confirm_account_link(
    request: Request,
    request_id: int = Form(...),
    action: str = Form(...),  # 'approve' или 'reject'
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Подтверждение или отклонение запроса на связывание"""
    
    # Находим запрос
    link_request = db.query(AccountLinkRequest).filter(
        AccountLinkRequest.id == request_id,
        AccountLinkRequest.target_user_id == current_user.id,  # Только тот, кому адресован запрос
        AccountLinkRequest.status == 'pending'
    ).first()
    
    if not link_request:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    
    if action == 'approve':
        # Связываем аккаунты
        requester = db.query(User).filter(User.id == link_request.user_id).first()
        
        if requester and current_user:
            # Если у одного есть VK, у другого нет - объединяем
            if requester.vk_id and not current_user.vk_id:
                current_user.vk_id = requester.vk_id
                current_user.is_whitelisted = requester.is_whitelisted
                # Удаляем дубликат
                db.delete(requester)
            elif current_user.vk_id and not requester.vk_id:
                requester.vk_id = current_user.vk_id
                requester.is_whitelisted = current_user.is_whitelisted
                # Удаляем дубликат
                db.delete(current_user)
            
            link_request.status = 'approved'
            link_request.processed_at = datetime.utcnow()
    else:
        link_request.status = 'rejected'
        link_request.processed_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url="/auth/profile", status_code=302) 