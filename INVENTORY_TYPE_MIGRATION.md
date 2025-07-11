# 🔄 МИГРАЦИЯ ТИПОВ ПРЕДМЕТОВ ИНВЕНТАРЯ

**Дата:** $(date)  
**Статус:** ✅ ГОТОВО К ПРИМЕНЕНИЮ

## 🎯 Цель миграции

Заменить текстовое поле `item_type` на внешний ключ к таблице `inventory_item_types` для:
- Нормализации данных
- Исправления проблем с фильтрацией
- Улучшения производительности
- Централизованного управления типами

## 📊 Анализ текущих данных

### Текущие типы в инвентаре:
- `оружие` → Оружие (id=1)
- `украшения` → Украшения (id=3)  
- `одежда` → Одежда (id=5)
- `аксессуары` → Аксессуары (id=6)
- `обувь` → Одежда (id=5)
- `инструменты` → Бытовые предметы (id=4)
- `артефакты` → Бытовые предметы (id=4)

### Справочник типов:
```sql
1 | Оружие          | Мечи, топоры, копья и другое оружие
2 | Доспехи         | Кольчуги, шлемы, щиты  
3 | Украшения       | Браслеты, кольца, подвески
4 | Бытовые предметы| Посуда, инструменты, утварь
5 | Одежда          | Элементы костюма
6 | Аксессуары      | Ремни, сумки, прочие аксессуары
7 | Прочее          | Другие предметы
```

## 🔧 Изменения в коде

### 1. Модель Inventory (models.py)
```python
class Inventory(Base):
    # Старое поле - оставляем для совместимости
    item_type = Column(Text)  
    
    # Новое поле - внешний ключ
    item_type_id = Column(Integer, ForeignKey("inventory_item_types.id", ondelete="SET NULL"), nullable=True)
    
    # Связь с таблицей типов
    item_type_ref = relationship("InventoryItemType", foreign_keys=[item_type_id])
```

### 2. Роутер inventory.py
```python
# Фильтрация по новому полю
if item_type and item_type != "all":
    try:
        item_type_id = int(item_type)
        query = query.filter(Inventory.item_type_id == item_type_id)
    except ValueError:
        # Обратная совместимость со старым полем
        query = query.filter(Inventory.item_type == item_type)

# Получение списка типов из справочника
types_list_query = text('''
    SELECT DISTINCT iit.id, iit.name, iit.sort_order
    FROM inventory_item_types iit
    INNER JOIN inventory i ON i.item_type_id = iit.id
    WHERE iit.is_active = true
    ORDER BY iit.sort_order, iit.name
''')
```

### 3. Шаблон list.html
```html
<!-- Фильтр по типам теперь использует ID -->
<option value="{{ type_item[0] }}">{{ type_item[1] }}</option>
```

## 📋 Пошаговая миграция

### Шаг 1: Применить SQL миграцию
```bash
psql -d valravn -f migration_inventory_item_type_fk.sql
```

### Шаг 2: Проверить результат
```sql
-- Проверить количество записей по типам
SELECT 
    iit.name as type_name,
    COUNT(i.id) as items_count
FROM inventory i
LEFT JOIN inventory_item_types iit ON i.item_type_id = iit.id
GROUP BY iit.id, iit.name
ORDER BY iit.sort_order;

-- Проверить записи без типа
SELECT COUNT(*) FROM inventory WHERE item_type_id IS NULL AND item_type IS NOT NULL;
```

### Шаг 3: Обновить код приложения
- ✅ Модель обновлена
- ✅ Роутер обновлен  
- ✅ Шаблон обновлен

### Шаг 4: Тестирование
1. Проверить фильтрацию по типам в `/inventory`
2. Убедиться что отображаются правильные названия
3. Проверить добавление новых предметов
4. Проверить редактирование существующих

## 🔄 Обратная совместимость

- Старое поле `item_type` сохраняется
- Фильтрация работает с обоими полями
- Постепенный переход на новое поле
- Возможность отката изменений

## ✅ Ожидаемый результат

После миграции:
1. **Фильтр типов работает корректно** - показывает только типы из справочника
2. **Производительность улучшена** - JOIN по индексированному полю быстрее
3. **Данные нормализованы** - нет дублирования названий типов
4. **Централизованное управление** - типы управляются через справочник

## 🚨 Важные замечания

1. **НЕ удалять старое поле** `item_type` до полного перехода
2. **Проверить все формы** добавления/редактирования инвентаря
3. **Обновить API** если используется внешний доступ
4. **Создать резервную копию** перед применением миграции

## 🎉 После успешной миграции

Фильтр типов предметов будет:
- ✅ Показывать только активные типы из справочника
- ✅ Отображать правильные названия типов
- ✅ Работать быстро и стабильно
- ✅ Поддерживать централизованное управление 