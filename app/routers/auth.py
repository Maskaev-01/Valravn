from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.models.schemas import UserCreate, UserLogin
from app.auth import authenticate_user, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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
            "error": "Неверное имя пользователя или пароль"
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

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response 