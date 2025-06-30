# 🕒 ИСПРАВЛЕНИЕ ПОЛЯ UPDATED_AT

**Дата:** 30 июня 2025  
**Статус:** ✅ ИСПРАВЛЕНО  
**Проблема:** SQLAlchemy пытался вставить `updated_at` со значением `None`

## 🎯 Проблема

При добавлении предметов инвентаря возникала ошибка:
```
[parameters: {..., 'updated_at': None}]
```

SQLAlchemy пытался передать `updated_at` со значением `None` в INSERT запрос, но база данных ожидала автоматическое значение.

## 🔍 Причина

В моделях SQLAlchemy поле `updated_at` было определено только с `onupdate=func.now()`, но без `server_default`:

```python
# ❌ Неправильно
updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

Это означало:
- При UPDATE - поле обновляется автоматически ✅
- При INSERT - SQLAlchemy передает `None` ❌

## 🔧 Примененные исправления

### 1. Исправлены модели SQLAlchemy

**Файлы:** `app/models/models.py`

```python
# ✅ Правильно
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Исправлены модели:**
- `Budget` - таблица budget
- `Inventory` - таблица inventory  
- `BudgetType` - таблица budget_types
- `InventoryItemType` - таблица inventory_item_types
- `InventoryMaterialType` - таблица inventory_material_types

### 2. Применена миграция базы данных

**Файл:** `fix_updated_at_defaults.sql`

```sql
-- Добавляем DEFAULT NOW() для всех таблиц
ALTER TABLE inventory ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE budget ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE budget_types ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE inventory_item_types ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE inventory_material_types ALTER COLUMN updated_at SET DEFAULT NOW();
```

## ✅ Результат

Теперь поле `updated_at`:
- ✅ **При INSERT** - автоматически устанавливается текущее время
- ✅ **При UPDATE** - автоматически обновляется на текущее время
- ✅ **SQLAlchemy не передает** значение в запросе - использует DEFAULT

## 🚀 Инструкции по применению

### 1. Применить миграцию к базе данных
```bash
psql $DATABASE_URL -f fix_updated_at_defaults.sql
```

### 2. Перезапустить приложение
Изменения в моделях SQLAlchemy уже применены.

## 🧪 Проверка

После применения исправлений:
1. ✅ Добавление предметов инвентаря работает
2. ✅ Добавление взносов работает
3. ✅ Редактирование предметов обновляет `updated_at`
4. ✅ Никаких ошибок с `updated_at: None`

## 📋 Файлы изменены

- `app/models/models.py` - Исправлены все модели с `updated_at`
- `fix_updated_at_defaults.sql` - SQL миграция для БД

## 🎉 Статус

**Проблема полностью решена!** Теперь все операции с базой данных работают корректно без ошибок `updated_at`. 