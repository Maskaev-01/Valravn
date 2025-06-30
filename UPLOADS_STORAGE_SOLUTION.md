# 🗂️ РЕШЕНИЕ ПРОБЛЕМЫ ОЧИСТКИ ПАПКИ UPLOADS

**Дата:** 27 января 2025  
**Проблема:** Папка `/uploads` очищается при каждом редеплое на Render и других платформах  
**Статус:** ✅ РЕШЕНО

## 🎯 Проблема

На платформах вроде Render, Heroku и других PaaS-сервисах файловая система является **эфемерной** (ephemeral). Это означает, что:

- ✅ Файлы, включенные в репозиторий, сохраняются
- ❌ Файлы, загруженные пользователями во время работы приложения, **удаляются** при каждом редеплое
- ❌ Папка `app/static/uploads/` очищается при каждом деплое

## 💡 Решения

### 1. **Хранение в БД в формате Base64** ⭐ (Выбранное решение)

**Преимущества:**
- ✅ Простота реализации
- ✅ Не требует дополнительных сервисов
- ✅ Изображения всегда доступны
- ✅ Автоматическое сжатие в WebP
- ✅ Работает на любой платформе

**Недостатки:**
- ❌ Увеличивает размер БД
- ❌ Подходит для небольшого количества изображений

### 2. **Persistent Disk на Render** 💰

**Преимущества:**
- ✅ Простая настройка
- ✅ Автоматические бэкапы
- ✅ Высокая производительность

**Недостатки:**
- ❌ Требует платный план ($7+/месяц)
- ❌ Отключает zero-downtime deploys
- ❌ Только один инстанс приложения

### 3. **Внешнее хранилище (S3/Cloudinary)** 🌐

**Преимущества:**
- ✅ Неограниченная масштабируемость
- ✅ CDN для быстрой загрузки
- ✅ Дополнительные возможности обработки

**Недостатки:**
- ❌ Дополнительная сложность
- ❌ Дополнительные расходы
- ❌ Зависимость от внешнего сервиса

## 🔧 Реализованное решение

### База данных

Добавлены новые поля для хранения изображений в base64:

```sql
-- Инвентарь
ALTER TABLE inventory ADD COLUMN image_data TEXT;
ALTER TABLE inventory ADD COLUMN image_filename VARCHAR(255);
ALTER TABLE inventory ADD COLUMN image_size INTEGER;

-- Бюджет (скриншоты)
ALTER TABLE budget ADD COLUMN screenshot_data TEXT;
ALTER TABLE budget ADD COLUMN screenshot_filename VARCHAR(255);
ALTER TABLE budget ADD COLUMN screenshot_size INTEGER;
```

### Обработка изображений

**Новые методы в `FileManager`:**
- `save_inventory_image_to_base64()` - сохраняет изображение в base64
- `save_screenshot_to_base64()` - сохраняет скриншот в base64
- `get_image_data_url()` - создает data URL для отображения
- `get_image_size_mb()` - вычисляет размер base64 изображения

**Оптимизация:**
- Автоматическое сжатие в WebP формат
- Изменение размера: 800x600 для инвентаря, 1920x1080 для скриншотов
- Качество: 90% для инвентаря, 85% для скриншотов

### Обратная совместимость

Система поддерживает как новый (base64), так и старый (файлы) формат:

```html
{% set has_image = item.image_data or item.image_path %}
{% if has_image %}
    {% if item.image_data %}
        <!-- Новый формат: base64 из БД -->
        <img src="data:image/webp;base64,{{ item.image_data }}">
    {% elif item.image_path %}
        <!-- Старый формат: файл -->
        <img src="{{ item.image_path }}">
    {% endif %}
{% endif %}
```

## 📊 Статистика и мониторинг

Создан VIEW для мониторинга использования хранилища:

```sql
SELECT * FROM image_storage_stats;
```

Показывает:
- Общее количество записей
- Количество записей с base64 данными
- Количество записей с файлами
- Общий размер base64 данных
- Средний размер изображения

## 🚀 Инструкции по развертыванию

### 1. Применить миграцию

```bash
# Подключиться к БД и выполнить
psql $DATABASE_URL -f migration_add_image_base64_fields.sql
```

### 2. Деплой кода

```bash
git add .
git commit -m "feat: Add base64 image storage to solve uploads cleanup issue"
git push origin main
```

### 3. Проверить работу

1. Добавить новый предмет с изображением
2. Добавить новый взнос со скриншотом
3. Проверить, что изображения отображаются корректно
4. Выполнить редеплой и убедиться, что изображения не пропали

## 📈 Производительность

**Размеры изображений после оптимизации:**
- Фото инвентаря: ~50-150 KB (WebP, 800x600, 90%)
- Скриншоты: ~100-300 KB (WebP, 1920x1080, 85%)

**Влияние на БД:**
- Base64 увеличивает размер на ~33%
- Типичное изображение: 100 KB → 133 KB в base64
- 100 изображений ≈ 13 MB дополнительно в БД

## 🔄 Миграция существующих файлов

Если нужно перенести существующие файлы в БД:

```python
# Скрипт для миграции (выполнить один раз)
import base64
from app.database import SessionLocal
from app.models.models import Inventory, Budget
from app.file_manager import FileManager

db = SessionLocal()
file_manager = FileManager()

# Миграция изображений инвентаря
for item in db.query(Inventory).filter(Inventory.image_path.isnot(None)).all():
    try:
        # Читаем файл и конвертируем в base64
        with open(f"app/static{item.image_path}", "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            item.image_data = image_data
            item.image_filename = item.image_path.split('/')[-1]
        db.commit()
        print(f"Migrated: {item.item_name}")
    except Exception as e:
        print(f"Error migrating {item.item_name}: {e}")

db.close()
```

## 🎉 Результат

✅ **Проблема решена!** Теперь изображения:
- Сохраняются в базе данных
- Не удаляются при редеплое
- Автоматически оптимизируются
- Быстро загружаются
- Поддерживают обратную совместимость

**Все новые изображения будут автоматически сохраняться в БД в формате base64.** 