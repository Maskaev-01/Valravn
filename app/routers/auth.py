from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, VKWhitelist
from app.models.schemas import UserCreate, UserLogin
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_or_update_vk_user,
    add_vk_user_to_whitelist,
    get_admin_user,
    get_current_user_from_cookie
)

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
        "whitelist": whitelist
    })

@router.post("/admin/vk-whitelist/add")
async def add_to_vk_whitelist(
    request: Request,
    vk_id: str = Form(...),
    username: str = Form(...),
    is_admin: bool = Form(False),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Добавляет пользователя в VK whitelist"""
    try:
        add_vk_user_to_whitelist(
            db=db,
            vk_id=vk_id,
            username=username,
            is_admin=is_admin,
            added_by=current_user.id
        )
        
        whitelist = db.query(VKWhitelist).all()
        return templates.TemplateResponse("admin/vk_whitelist.html", {
            "request": request,
            "whitelist": whitelist,
            "success": f"Пользователь {username} добавлен в whitelist"
        })
    except Exception as e:
        whitelist = db.query(VKWhitelist).all()
        return templates.TemplateResponse("admin/vk_whitelist.html", {
            "request": request,
            "whitelist": whitelist,
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
    
    return RedirectResponse(url="/admin/vk-whitelist", status_code=302)

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
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        photo_100 = data.get("photo_100")
        
        if not user_id:
            print(f"Missing user_id: {user_id}")  # Отладка
            raise HTTPException(status_code=400, detail="Нет VK user_id")
        
        print(f"Processing VK user: {user_id} - {first_name} {last_name}")  # Отладка
        
        # Создаем или обновляем пользователя
        user = create_or_update_vk_user(
            db=db,
            vk_id=user_id,
            first_name=first_name,
            last_name=last_name,
            avatar_url=photo_100
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