import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, Response, FileResponse
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

@app.get("/robots.txt")
async def robots_txt():
    """Возвращает robots.txt для поисковых роботов"""
    return FileResponse("app/static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap_xml(request: Request, db: Session = Depends(get_db)):
    """Генерирует sitemap.xml для поисковых систем"""
    base_url = "https://valravn-budget.onrender.com"
    
    # Основные страницы
    pages = [
        {"url": "/", "priority": "1.0", "changefreq": "daily"},
        {"url": "/auth/login", "priority": "0.8", "changefreq": "monthly"},
        {"url": "/auth/register", "priority": "0.8", "changefreq": "monthly"},
        {"url": "/dashboard", "priority": "0.9", "changefreq": "daily"},
        {"url": "/inventory", "priority": "0.9", "changefreq": "weekly"},
        {"url": "/reports", "priority": "0.8", "changefreq": "weekly"},
    ]
    
    # Добавляем страницы инвентаря
    try:
        from app.models.models import Inventory
        inventory_items = db.query(Inventory).filter(Inventory.is_club_item == True).limit(100).all()
        for item in inventory_items:
            pages.append({
                "url": f"/inventory/{item.id}",
                "priority": "0.6",
                "changefreq": "monthly"
            })
    except Exception:
        pass  # Игнорируем ошибки при генерации sitemap
    
    # Генерируем XML
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        sitemap += f'  <url>\n'
        sitemap += f'    <loc>{base_url}{page["url"]}</loc>\n'
        sitemap += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap += f'    <priority>{page["priority"]}</priority>\n'
        sitemap += f'  </url>\n'
    
    sitemap += '</urlset>'
    
    return Response(content=sitemap, media_type="application/xml")

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