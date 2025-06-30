# Database & SQLAlchemy Rules

## 🗄️ АРХИТЕКТУРА БАЗЫ ДАННЫХ

### Технологии:
- **PostgreSQL** - основная СУБД
- **SQLAlchemy ORM** - объектно-реляционное отображение
- **Alembic** - миграции (частично, в основном SQL скрипты)
- **psycopg2-binary** - драйвер PostgreSQL

---

## 📋 ОСНОВНЫЕ ТАБЛИЦЫ

### 1. **users** - Пользователи системы
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE,                    -- Может быть NULL
    hashed_password VARCHAR,                 -- NULL для VK пользователей
    is_admin INTEGER DEFAULT 0,             -- 0=обычный, 1=админ
    
    -- VK OAuth поля
    vk_id VARCHAR UNIQUE,                   -- VK User ID
    first_name VARCHAR,                     -- Имя из VK
    last_name VARCHAR,                      -- Фамилия из VK
    avatar_url VARCHAR,                     -- Аватар из VK
    is_whitelisted BOOLEAN DEFAULT FALSE,   -- Разрешен ли VK доступ
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. **budget** - Финансовые операции
```sql
CREATE TABLE budget (
    id SERIAL PRIMARY KEY,
    price FLOAT NOT NULL,
    description VARCHAR,
    data DATE,                              -- Дата операции
    type VARCHAR,                           -- "Взнос", "Расход", "Доход"
    
    -- Модерация
    screenshot_path VARCHAR,                -- Путь к скриншоту
    is_approved BOOLEAN DEFAULT FALSE,      -- Одобрено админом
    user_id INTEGER REFERENCES users(id),  -- Связь с пользователем
    contributor_name VARCHAR,               -- Имя участника
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by INTEGER REFERENCES users(id)
);
```

### 3. **inventory** - Инвентарь клуба
```sql
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    owner TEXT NOT NULL,                    -- Владелец предмета
    item_name TEXT NOT NULL,                -- Название предмета
    item_type TEXT,                         -- Тип предмета
    subtype TEXT,                           -- Подтип
    material TEXT,                          -- Материал
    color TEXT,                             -- Цвет
    size TEXT,                              -- Размер
    
    -- Археологические данные
    find_type TEXT,                         -- Тип находки
    region TEXT,                            -- Регион
    place TEXT,                             -- Место
    burial_number TEXT,                     -- Номер захоронения
    notes TEXT,                             -- Заметки
    
    -- Дополнительные поля
    image_path VARCHAR,                     -- Путь к изображению
    created_by_user_id INTEGER REFERENCES users(id),
    is_club_item BOOLEAN DEFAULT FALSE,     -- Клубный предмет
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 4. **vk_whitelist** - Разрешенные VK пользователи
```sql
CREATE TABLE vk_whitelist (
    id SERIAL PRIMARY KEY,
    vk_id VARCHAR UNIQUE NOT NULL,
    username VARCHAR NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    added_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. **account_link_requests** - Запросы связывания аккаунтов
```sql
CREATE TABLE account_link_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',   -- pending, approved, rejected
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by INTEGER REFERENCES users(id),
    
    UNIQUE(user_id, target_user_id, status)
);
```

---

## 🔧 SQLALCHEMY МОДЕЛИ

### Базовая структура модели:
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ModelName(Base):
    __tablename__ = "table_name"
    
    id = Column(Integer, primary_key=True, index=True)
    # ... другие поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Правила определения моделей:
- **ВСЕГДА** используй `Base` из `app.database`
- **ВСЕГДА** указывай `__tablename__`
- **ВСЕГДА** добавляй `id` как primary key
- **ВСЕГДА** добавляй `created_at` для аудита
- **Используй** `server_default=func.now()` для временных меток

### Связи между таблицами:
```python
# Внешние ключи
user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

# Отношения (relationships)
user = relationship("User", back_populates="budget_entries")

# В модели User
budget_entries = relationship("Budget", back_populates="user")
```

---

## 🔄 РАБОТА С СЕССИЯМИ

### Получение сессии БД:
```python
from sqlalchemy.orm import Session
from app.database import get_db

# В роутах ВСЕГДА используй dependency injection
@router.get("/endpoint")
async def endpoint(db: Session = Depends(get_db)):
    # Работа с БД
    pass
```

### Основные операции:

#### Создание записи:
```python
def create_user(db: Session, user_data: dict):
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()                    # ОБЯЗАТЕЛЬНО!
    db.refresh(db_user)            # Получить ID и другие поля
    return db_user
```

#### Получение записей:
```python
# Одна запись
user = db.query(User).filter(User.id == user_id).first()

# Множественные записи
users = db.query(User).filter(User.is_admin == 1).all()

# С пагинацией
users = db.query(User).offset(skip).limit(limit).all()

# С сортировкой
users = db.query(User).order_by(User.created_at.desc()).all()
```

#### Обновление записи:
```python
def update_user(db: Session, user_id: int, update_data: dict):
    db.query(User).filter(User.id == user_id).update(update_data)
    db.commit()
    
    # Или через объект
    user = db.query(User).filter(User.id == user_id).first()
    user.username = "new_username"
    db.commit()
    db.refresh(user)
```

#### Удаление записи:
```python
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
```

---

## 🚨 ОБРАБОТКА ОШИБОК

### Стандартный паттерн:
```python
try:
    # Операции с БД
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record
except Exception as e:
    db.rollback()                           # ВАЖНО!
    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
```

### Обработка уникальных ограничений:
```python
from sqlalchemy.exc import IntegrityError

try:
    db.add(user)
    db.commit()
except IntegrityError as e:
    db.rollback()
    if "unique constraint" in str(e).lower():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    raise HTTPException(status_code=500, detail="Ошибка базы данных")
```

---

## 🔄 МИГРАЦИИ

### Создание таблиц при запуске:
```python
# В main.py
from app.models import models
from app.database import engine

# Создаем все таблицы
models.Base.metadata.create_all(bind=engine)
```

### Сложные миграции через SQL:
```python
# В main.py для одноразовых миграций
try:
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS new_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL
            );
        """))
        connection.commit()
except Exception as e:
    print(f"Migration warning: {e}")
```

### Миграционные файлы:
- Создавай отдельные `.sql` файлы для сложных миграций
- Используй `CREATE TABLE IF NOT EXISTS` для безопасности
- Документируй изменения в `MIGRATION_INSTRUCTIONS.md`

---

## 🔍 ЗАПРОСЫ И ОПТИМИЗАЦИЯ

### Сложные запросы:
```python
# Джоины
results = db.query(Budget, User).join(User, Budget.user_id == User.id).all()

# Подзапросы
subquery = db.query(User.id).filter(User.is_admin == 1).subquery()
budgets = db.query(Budget).filter(Budget.user_id.in_(subquery)).all()

# Агрегация
from sqlalchemy import func
total = db.query(func.sum(Budget.price)).filter(Budget.type == "Взнос").scalar()

# Группировка
stats = db.query(
    Budget.type,
    func.count(Budget.id),
    func.sum(Budget.price)
).group_by(Budget.type).all()
```

### Оптимизация:
```python
# Eager loading для избежания N+1 проблемы
from sqlalchemy.orm import joinedload

users = db.query(User).options(joinedload(User.budget_entries)).all()

# Ограничение полей
users = db.query(User.id, User.username).all()

# Индексы (в SQL миграциях)
CREATE INDEX idx_budget_user_id ON budget(user_id);
CREATE INDEX idx_budget_type ON budget(type);
```

---

## 📊 СПЕЦИФИЧЕСКИЕ ЗАПРОСЫ ПРОЕКТА

### Статистика бюджета:
```python
def get_budget_stats(db: Session):
    return {
        "total_income": db.query(func.sum(Budget.price))
                         .filter(Budget.type.in_(["Взнос", "Доход"]))
                         .filter(Budget.is_approved == True)
                         .scalar() or 0,
        
        "total_expenses": db.query(func.sum(Budget.price))
                           .filter(Budget.type == "Расход")
                           .scalar() or 0,
        
        "pending_contributions": db.query(func.count(Budget.id))
                                  .filter(Budget.type == "Взнос")
                                  .filter(Budget.is_approved == False)
                                  .scalar() or 0
    }
```

### Топ участников:
```python
def get_top_contributors(db: Session, limit: int = 10):
    return db.query(
        Budget.contributor_name,
        func.sum(Budget.price).label('total'),
        func.count(Budget.id).label('count')
    ).filter(
        Budget.type == "Взнос",
        Budget.is_approved == True
    ).group_by(
        Budget.contributor_name
    ).order_by(
        func.sum(Budget.price).desc()
    ).limit(limit).all()
```

### Инвентарь пользователя:
```python
def get_user_inventory(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # Поиск по имени пользователя
    full_name = f"{user.first_name} {user.last_name}".strip()
    
    return db.query(Inventory).filter(
        or_(
            Inventory.owner == user.username,
            Inventory.owner == full_name,
            Inventory.created_by_user_id == user_id
        )
    ).all()
```

---

## 🔐 БЕЗОПАСНОСТЬ БД

### Предотвращение SQL инъекций:
```python
# ПРАВИЛЬНО - используй параметры
user = db.query(User).filter(User.username == username).first()

# НЕПРАВИЛЬНО - никогда не делай так
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

### Проверка прав доступа:
```python
def check_inventory_access(db: Session, user: User, inventory_id: int) -> bool:
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        return False
    
    # Админы могут всё
    if user.is_admin:
        return True
    
    # Владелец может редактировать свои предметы
    full_name = f"{user.first_name} {user.last_name}".strip()
    return (inventory.owner == user.username or 
            inventory.owner == full_name or
            inventory.created_by_user_id == user.id)
```

### Валидация данных:
```python
def validate_budget_entry(data: dict) -> dict:
    """Валидация данных бюджета перед сохранением"""
    if not data.get('price') or data['price'] <= 0:
        raise ValueError("Сумма должна быть положительной")
    
    if data.get('type') not in ['Взнос', 'Расход', 'Доход']:
        raise ValueError("Неверный тип операции")
    
    return data
```

---

## 🎯 ЛУЧШИЕ ПРАКТИКИ

### Производительность:
- **Используй** индексы для часто запрашиваемых полей
- **Ограничивай** количество возвращаемых записей
- **Используй** `select_related` для связанных объектов
- **Кешируй** тяжелые запросы

### Надежность:
- **ВСЕГДА** используй транзакции для связанных операций
- **ВСЕГДА** обрабатывай исключения БД
- **Делай** регулярные бэкапы
- **Тестируй** миграции на копии данных

### Поддерживаемость:
- **Документируй** сложные запросы
- **Используй** понятные имена для полей и таблиц
- **Группируй** связанные модели
- **Версионируй** схему БД

---

## ⚡ БЫСТРЫЕ КОМАНДЫ

### Локальная разработка:
```bash
# Подключение к PostgreSQL
psql -h localhost -U username -d database_name

# Бэкап БД
pg_dump database_name > backup.sql

# Восстановление БД
psql database_name < backup.sql

# Выполнение миграции
psql -d database_name -f migration.sql
```

### Полезные SQL запросы:
```sql
-- Размер таблиц
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size 
FROM pg_tables WHERE schemaname='public';

-- Активные соединения
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Индексы таблицы
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'users';
```

---

**🗄️ База данных - сердце системы. Проектируй схему тщательно и следи за производительностью!** 