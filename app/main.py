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
from app.routers import auth, budget, admin
from app.auth import get_current_user_from_cookie

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    try:
        user = await get_current_user_from_cookie(request, db)
        return RedirectResponse(url="/dashboard")
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 