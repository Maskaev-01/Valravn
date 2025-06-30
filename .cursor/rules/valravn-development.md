# Valravn Project Development Rules

## 🎯 ПРОЕКТ: Система управления бюджетом клуба "Valravn"
FastAPI + PostgreSQL + Jinja2 + Tailwind CSS + VK OAuth

---

## 📁 АРХИТЕКТУРА И СТРУКТУРА

### Основные компоненты:
- **Backend**: FastAPI с модульной структурой роутеров
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Frontend**: Jinja2 шаблоны + Tailwind CSS + Alpine.js
- **Auth**: JWT + bcrypt + VK OAuth (VK ID SDK)
- **Deployment**: Render.com + Docker

### Структура директорий:
```
app/
├── main.py              # Точка входа FastAPI
├── auth.py             # Система аутентификации  
├── database.py         # Конфигурация БД
├── vk_oauth.py         # VK OAuth интеграция
├── models/
│   ├── models.py       # SQLAlchemy модели
│   └── schemas.py      # Pydantic схемы
├── routers/            # Модульные роутеры
│   ├── auth.py        # Аутентификация
│   ├── admin.py       # Админ панель
│   ├── budget.py      # Бюджет
│   └── inventory.py   # Инвентарь
├── templates/          # Jinja2 шаблоны
│   ├── base.html      # Базовый шаблон
│   ├── admin/         # Админ шаблоны
│   └── inventory/     # Инвентарь шаблоны
└── static/            # Статические файлы
    ├── css/style.css  # Tailwind CSS
    ├── js/main.js     # Alpine.js + JS
    └── uploads/       # Загруженные файлы
```

---

## 🔐 СИСТЕМА АУТЕНТИФИКАЦИИ

### Методы авторизации:
1. **Стандартная регистрация**: username + password + секретный код
2. **VK OAuth**: через VK ID SDK с whitelist проверкой
3. **JWT токены**: в HTTP-only cookies

### Правила аутентификации:
- **ВСЕГДА** используй `get_current_user_from_cookie` для веб-страниц
- **ВСЕГДА** используй `get_admin_user` для админ функций
- **НИКОГДА** не храни пароли в открытом виде - только bcrypt hash
- **VK пользователи** могут иметь `hashed_password = NULL`

### VK OAuth интеграция:
```python
# Проверка VK whitelist ОБЯЗАТЕЛЬНА
def create_or_update_vk_user(db, vk_id, first_name, last_name, avatar_url, email):
    whitelist_entry = db.query(VKWhitelist).filter(VKWhitelist.vk_id == vk_id).first()
    if not whitelist_entry:
        raise HTTPException(status_code=403, detail="VK ID не в whitelist")
```

---

## 🗄️ БАЗА ДАННЫХ

### Основные таблицы:
- **users**: пользователи (обычные + VK)
- **budget**: доходы/расходы с модерацией
- **inventory**: инвентарь клуба
- **vk_whitelist**: разрешенные VK пользователи
- **account_link_requests**: запросы связывания аккаунтов

### Правила работы с БД:
- **ВСЕГДА** используй `Depends(get_db)` для получения сессии
- **ВСЕГДА** делай `db.commit()` после изменений
- **ВСЕГДА** используй `db.refresh(object)` после создания
- **НИКОГДА** не забывай `db.close()` (автоматически через dependency)

### Миграции:
- Создавай таблицы через `models.Base.metadata.create_all(bind=engine)`
- Сложные миграции выноси в отдельные SQL файлы
- Используй `CREATE TABLE IF NOT EXISTS` для безопасности

---

## 🎨 FRONTEND РАЗРАБОТКА

### Технологии:
- **Tailwind CSS**: для стилизации (кастомная тема `valravn`)
- **Alpine.js**: для интерактивности
- **Jinja2**: для шаблонизации
- **Font Awesome**: для иконок

### Цветовая схема Valravn:
```css
'valravn': {
    50: '#f0f9ff',
    500: '#0ea5e9', 
    600: '#0284c7',
    900: '#0c4a6e'
}
```

### Правила шаблонов:
- **ВСЕГДА** наследуй от `base.html`
- **ВСЕГДА** проверяй аутентификацию: `{% if current_user %}`
- **ВСЕГДА** используй CSRF защиту в формах
- **Мобильная адаптивность**: используй responsive классы Tailwind

### Компоненты интерфейса:
```html
<!-- Стандартная кнопка -->
<button class="bg-valravn-600 hover:bg-valravn-700 text-white px-4 py-2 rounded-lg">

<!-- Форма с валидацией -->
<form method="post" class="space-y-4" x-data="formHandler()">

<!-- Модальное окно -->
<div x-show="showModal" class="fixed inset-0 bg-gray-600 bg-opacity-50">
```

---

## 📊 БИЗНЕС-ЛОГИКА

### Модули системы:

#### 1. Бюджет (`budget.py`):
- **Типы записей**: "Взнос", "Расход", "Доход"
- **Модерация**: все взносы требуют подтверждения админом
- **Скриншоты**: загрузка подтверждающих документов
- **Связывание**: автоматическое связывание с пользователями

#### 2. Инвентарь (`inventory.py`):
- **Типы предметов**: личные и клубные
- **Фотографии**: загрузка изображений предметов
- **Археологические данные**: регион, место находки, захоронение
- **Права доступа**: владелец может редактировать свои предметы

#### 3. Администрирование (`admin.py`):
- **Управление пользователями**: смена паролей, права доступа
- **VK Whitelist**: добавление/удаление VK пользователей
- **Модерация**: одобрение взносов и записей
- **Аналитика**: отчеты и статистика

---

## 🔧 РАЗРАБОТКА И ДЕПЛОЙ

### Переменные окружения:
```env
# Обязательные
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
SECRET_REGISTRATION_CODE=valravn2024

# VK OAuth (опциональные)
VK_APP_ID=your_app_id
VK_APP_SECRET=your_app_secret
VK_SERVICE_TOKEN=your_service_token
VK_REDIRECT_URI=https://your-domain.com/auth/login

# Файлы
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=app/static/uploads
```

### Деплой на Render.com:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **PostgreSQL**: автоматическое создание через `render.yaml`

---

## 🚨 БЕЗОПАСНОСТЬ И BEST PRACTICES

### Безопасность:
- **Секретный код регистрации**: защита от нежелательных регистраций
- **VK Whitelist**: только разрешенные VK пользователи
- **JWT в HTTP-only cookies**: защита от XSS
- **Bcrypt hashing**: безопасное хранение паролей
- **CSRF защита**: во всех формах

### Обработка ошибок:
```python
try:
    # Операция с БД
    db.commit()
except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))
```

### Логирование:
```python
import logging
logging.info(f"User {user.username} performed action")
```

---

## 📝 CODING STANDARDS

### Python код:
- **PEP 8** стиль кодирования
- **Type hints** для всех функций
- **Docstrings** для сложных функций
- **Async/await** для I/O операций

### Именование:
- **Функции**: `snake_case`
- **Классы**: `PascalCase`  
- **Константы**: `UPPER_CASE`
- **Переменные**: `snake_case`

### Структура роутов:
```python
@router.get("/endpoint", response_class=HTMLResponse)
async def endpoint_name(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    return templates.TemplateResponse("template.html", {
        "request": request,
        "current_user": current_user
    })
```

---

## 🎯 СПЕЦИФИЧЕСКИЕ ПРАВИЛА ПРОЕКТА

### VK OAuth:
- **ТОЛЬКО VK ID SDK** (старый OAuth2 не работает)
- **Whitelist обязателен** для всех VK пользователей
- **Сервисный токен** для получения данных пользователей
- **Автоматическое связывание** по email при наличии

### Файловые загрузки:
- **Максимальный размер**: 10MB
- **Разрешенные типы**: изображения для инвентаря, документы для бюджета
- **Папки**: `app/static/uploads/inventory/`, `app/static/uploads/screenshots/`

### Локализация:
- **Русский язык** для всего интерфейса
- **Русские имена** из VK профилей приоритетны
- **Даты** в формате DD.MM.YYYY

### Права доступа:
- **Обычные пользователи**: добавление взносов, просмотр своего инвентаря
- **Администраторы**: полный доступ ко всем функциям
- **VK пользователи**: те же права + автоматическое заполнение данных

---

## 🔄 WORKFLOW РАЗРАБОТКИ

### При добавлении новой функции:
1. **Создай модель** в `models/models.py`
2. **Добавь роуты** в соответствующий файл `routers/`
3. **Создай шаблоны** в `templates/`
4. **Обнови навигацию** в `base.html`
5. **Протестируй** все сценарии использования

### При изменении БД:
1. **Создай миграцию** SQL файл
2. **Обнови модели** SQLAlchemy
3. **Проверь** на тестовых данных
4. **Документируй** изменения

### При деплое:
1. **Проверь** переменные окружения
2. **Выполни** миграции БД
3. **Протестируй** VK OAuth
4. **Проверь** загрузку файлов

---

## ⚡ БЫСТРЫЕ КОМАНДЫ

### Локальная разработка:
```bash
# Запуск сервера
uvicorn app.main:app --reload

# Миграция БД
psql -d database < migration.sql

# Установка зависимостей
pip install -r requirements.txt
```

### Отладка VK OAuth:
```bash
# Проверка конфигурации
curl https://your-domain.com/test-routes

# Логи VK авторизации
grep "VK Auth" logs/app.log
```

---

## 🎭 СПЕЦИАЛЬНЫЕ ФИЧИ

### Русификация имен:
- Автоматическая замена английских имен на русские
- Синхронизация между `users` и `vk_whitelist`
- Миграционные скрипты для массового обновления

### Связывание аккаунтов:
- Автоматическое связывание VK и обычных аккаунтов по email
- Таблица `account_link_requests` для ручных запросов
- Администраторы могут связывать аккаунты принудительно

### Модерация контента:
- Все взносы требуют подтверждения
- Скриншоты переводов для проверки
- История одобрений с указанием модератора

---

**🛡️ ПОМНИ: Это система управления финансами клуба - безопасность и точность данных критически важны!** 