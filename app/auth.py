import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, VKWhitelist

SECRET_KEY = os.getenv("SECRET_KEY", "valravn-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        return False
    return user

def create_or_update_vk_user(db: Session, vk_id: str, first_name: str, last_name: str, avatar_url: Optional[str] = None, email: Optional[str] = None):
    """Создает или обновляет пользователя VK с проверкой дублирования"""
    # Проверяем, есть ли пользователь в whitelist
    whitelist_entry = db.query(VKWhitelist).filter(VKWhitelist.vk_id == vk_id).first()
    if not whitelist_entry:
        raise HTTPException(status_code=403, detail="VK ID не в whitelist. Обратитесь к администратору.")
    
    # Сначала ищем существующего пользователя по vk_id
    user = db.query(User).filter(User.vk_id == vk_id).first()
    
    if user:
        # Обновляем данные существующего VK пользователя
        # Обновляем имена только если они не пустые (приоритет русским именам)
        if first_name and first_name.strip():
            user.first_name = first_name
        if last_name and last_name.strip():
            user.last_name = last_name
        if avatar_url:
            user.avatar_url = avatar_url
        if email and not user.email:
            user.email = email
        user.is_admin = 1 if whitelist_entry.is_admin else 0
        user.is_whitelisted = True
        db.commit()
        db.refresh(user)
        return user
    
    # Если пользователя по vk_id нет, проверяем есть ли пользователь с таким email
    existing_user_by_email = None
    if email:
        existing_user_by_email = db.query(User).filter(
            User.email == email,
            User.vk_id.is_(None)  # Только пользователи без VK ID
        ).first()
    
    if existing_user_by_email:
        # Найден пользователь с таким email - связываем аккаунты
        existing_user_by_email.vk_id = vk_id
        existing_user_by_email.first_name = first_name
        existing_user_by_email.last_name = last_name
        existing_user_by_email.avatar_url = avatar_url
        existing_user_by_email.is_admin = max(existing_user_by_email.is_admin, 1 if whitelist_entry.is_admin else 0)
        existing_user_by_email.is_whitelisted = True
        db.commit()
        db.refresh(existing_user_by_email)
        return existing_user_by_email
    
    # Создаем нового пользователя
    # Сначала пытаемся использовать username из whitelist, если он подходящий
    whitelist_username = whitelist_entry.username
    if whitelist_username and not whitelist_username.startswith("VK User"):
        # Преобразуем имя в username: убираем пробелы, приводим к нижнему регистру
        username = whitelist_username.replace(" ", "_").lower()
        # Убираем специальные символы
        import re
        username = re.sub(r'[^a-zA-Z0-9_а-яё]', '', username, flags=re.IGNORECASE)
        if len(username) < 3:
            username = f"vk_{vk_id}"
    else:
        username = f"vk_{vk_id}"
    
    # Проверяем уникальность username
    counter = 1
    base_username = username
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1
    
    new_user = User(
        username=username,
        vk_id=vk_id,
        first_name=first_name,
        last_name=last_name,
        avatar_url=avatar_url,
        email=email,
        is_admin=1 if whitelist_entry.is_admin else 0,
        is_whitelisted=True,
        hashed_password=None  # Для VK users пароль не нужен
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def is_vk_user_whitelisted(db: Session, vk_id: str) -> bool:
    """Проверяет, есть ли VK пользователь в whitelist"""
    whitelist_entry = db.query(VKWhitelist).filter(VKWhitelist.vk_id == vk_id).first()
    return whitelist_entry is not None

def add_vk_user_to_whitelist(db: Session, vk_id: str, username: str, is_admin: bool = False, added_by: Optional[int] = None):
    """Добавляет VK пользователя в whitelist"""
    existing = db.query(VKWhitelist).filter(VKWhitelist.vk_id == vk_id).first()
    if existing:
        # Обновляем существующую запись
        existing.username = username
        existing.is_admin = is_admin
        existing.added_by = added_by
    else:
        # Создаем новую запись
        whitelist_entry = VKWhitelist(
            vk_id=vk_id,
            username=username,
            is_admin=is_admin,
            added_by=added_by
        )
        db.add(whitelist_entry)
    
    db.commit()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
    
    # Получаем токен из cookie
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    
    # Убираем префикс "Bearer " если есть
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    # Принудительно обновляем объект из базы данных
    db.refresh(user)
    
    # Проверяем, что поля загружены
    print(f"DEBUG AUTH: User {user.username}, role: {getattr(user, 'role', 'NOT_FOUND')}, permissions: {getattr(user, 'permissions', 'NOT_FOUND')}")
    
    return user

async def get_admin_user(current_user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    # Принудительно обновляем объект из базы данных
    db.refresh(current_user)
    
    # Проверяем права администратора (используем новую ролевую систему)
    if current_user.role not in ['admin', 'superadmin'] and current_user.is_admin != 1:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    print(f"DEBUG ADMIN: User {current_user.username}, role: {getattr(current_user, 'role', 'NOT_FOUND')}, is_admin: {current_user.is_admin}")
    
    return current_user

async def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """Получает текущего пользователя, но не требует аутентификации"""
    try:
        return await get_current_user_from_cookie(request, db)
    except HTTPException:
        return None 