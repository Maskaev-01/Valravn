import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models.models import User
from app.models import models
from app.routers import auth, budget, admin, inventory
from app.auth import get_current_user_from_cookie
from sqlalchemy import text
from fastapi.exception_handlers import http_exception_handler
from starlette.requests import Request as StarletteRequest

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

# Добавляем недостающие таблицы, если их нет
try:
    with engine.connect() as connection:
        # Проверяем и создаем таблицу account_link_requests если нужно
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS account_link_requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                processed_by INTEGER REFERENCES users(id),
                
                -- Предотвращает дубликаты активных запросов
                UNIQUE(user_id, target_user_id, status)
            );
        """))
        
        # Создаем индексы если их нет
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_account_link_requests_user_id ON account_link_requests(user_id);
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_account_link_requests_target_user_id ON account_link_requests(target_user_id);
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_account_link_requests_status ON account_link_requests(status);
        """))
        
        connection.commit()
        print("✅ Account link requests table and indexes created/verified")
except Exception as e:
    print(f"⚠️  Database migration warning: {e}")

app = FastAPI(title="Valravn Budget Management", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене настройте конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(budget.router)
app.include_router(admin.router)
app.include_router(inventory.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user_from_cookie(request, db)
        return RedirectResponse(url="/dashboard")
    except HTTPException:
        return RedirectResponse(url="/auth/login")

# Редирект для VK ID SDK совместимости
@app.get("/login")
async def login_redirect():
    return RedirectResponse(url="/auth/login", status_code=302)

# Редирект для старой ссылки logout
@app.get("/logout")
async def logout_redirect():
    return RedirectResponse(url="/auth/logout", status_code=302)

# Редирект для старой ссылки VK whitelist
@app.get("/admin/vk-whitelist")
async def vk_whitelist_redirect():
    return RedirectResponse(url="/auth/admin/vk-whitelist", status_code=302)

# Тестовая страница для проверки роутов
@app.get("/test-routes")
async def test_routes():
    return {
        "routes": {
            "login": "/auth/login",
            "register": "/auth/register", 
            "logout": "/auth/logout",
            "vk_process": "/auth/vk/process",
            "vk_whitelist": "/auth/admin/vk-whitelist"
        },
        "status": "all routes configured"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: StarletteRequest, exc: HTTPException):
    if exc.status_code == 401:
        # Редиректим на страницу логина для неавторизованных
        return RedirectResponse(url="/auth/login", status_code=302)
    # Для остальных ошибок используем стандартный обработчик
    return await http_exception_handler(request, exc)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 