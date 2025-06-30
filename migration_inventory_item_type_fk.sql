-- Миграция: Добавление внешнего ключа для типов предметов в инвентаре
-- Дата: 2025-01-01
-- Описание: Заменяем текстовое поле item_type на внешний ключ к таблице inventory_item_types

-- 1. Добавляем новое поле item_type_id
ALTER TABLE inventory 
ADD COLUMN item_type_id INTEGER REFERENCES inventory_item_types(id) ON DELETE SET NULL;

-- 2. Создаем маппинг текстовых типов к ID из справочника
-- Сначала обновляем существующие записи по соответствию

-- Оружие (id=1)
UPDATE inventory 
SET item_type_id = 1 
WHERE LOWER(item_type) = 'оружие';

-- Доспехи (id=2) - пока нет в данных, но готовим
UPDATE inventory 
SET item_type_id = 2 
WHERE LOWER(item_type) IN ('доспехи', 'броня', 'шлем', 'щит');

-- Украшения (id=3)
UPDATE inventory 
SET item_type_id = 3 
WHERE LOWER(item_type) = 'украшения';

-- Бытовые предметы (id=4)
UPDATE inventory 
SET item_type_id = 4 
WHERE LOWER(item_type) IN ('инструменты', 'артефакты');

-- Одежда (id=5)
UPDATE inventory 
SET item_type_id = 5 
WHERE LOWER(item_type) = 'одежда';

-- Аксессуары (id=6)
UPDATE inventory 
SET item_type_id = 6 
WHERE LOWER(item_type) = 'аксессуары';

-- Обувь - относим к одежде (id=5)
UPDATE inventory 
SET item_type_id = 5 
WHERE LOWER(item_type) = 'обувь';

-- Прочее (id=7) - для всех остальных
UPDATE inventory 
SET item_type_id = 7 
WHERE item_type IS NOT NULL AND item_type_id IS NULL;

-- 3. Создаем индекс для производительности
CREATE INDEX idx_inventory_item_type_id ON inventory(item_type_id);

-- 4. Проверяем результат миграции
SELECT 
    iit.name as type_name,
    COUNT(i.id) as items_count,
    STRING_AGG(DISTINCT i.item_type, ', ') as old_text_types
FROM inventory i
LEFT JOIN inventory_item_types iit ON i.item_type_id = iit.id
GROUP BY iit.id, iit.name
ORDER BY iit.sort_order;

-- 5. Показываем записи без типа
SELECT COUNT(*) as items_without_type
FROM inventory 
WHERE item_type_id IS NULL AND item_type IS NOT NULL;

-- ВАЖНО: После проверки результатов можно будет удалить старое поле:
-- ALTER TABLE inventory DROP COLUMN item_type;
-- Но пока оставляем для обратной совместимости 