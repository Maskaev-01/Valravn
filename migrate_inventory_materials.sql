-- Миграция материалов инвентаря
-- Обновляет поле material_type_id на основе существующих текстовых значений в поле material
-- Дата: 2025-01-01

-- 1. Сначала покажем статистику по материалам
SELECT 
    'Статистика материалов в инвентаре:' as info,
    '' as material,
    '' as count,
    '' as with_type_id
UNION ALL
SELECT 
    '--------------------------------------------',
    '',
    '',
    ''
UNION ALL
SELECT 
    'Материал' as info,
    'Кол-во' as material,
    'С типом' as count,
    '' as with_type_id
UNION ALL
SELECT 
    '--------------------------------------------',
    '',
    '',
    ''
UNION ALL
SELECT 
    material as info,
    COUNT(*)::text as material,
    COUNT(material_type_id)::text as count,
    '' as with_type_id
FROM inventory 
WHERE material IS NOT NULL AND material != ''
GROUP BY material
ORDER BY material;

-- 2. Обновляем материалы по категориям

-- Металлы
UPDATE inventory 
SET material_type_id = 1, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'железо' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 2, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'сталь' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 3, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'латунь' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 4, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'бронза' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 5, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'серебро' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 6, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'медь' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 7, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'олово' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 8, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'свинец' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 9, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'золото' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 10, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'металл' 
AND material_type_id IS NULL;

-- Дерево
UPDATE inventory 
SET material_type_id = 11, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'дуб' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 12, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'ясень' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 13, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('береза', 'берёза') 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 14, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'сосна' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 15, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'ель' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 16, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'липа' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 17, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('клен', 'клён') 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 18, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'орех' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 19, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'дерево' 
AND material_type_id IS NULL;

-- Ткани
UPDATE inventory 
SET material_type_id = 20, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('лён', 'лен') 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 21, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'шерсть' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 22, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('шелк', 'шёлк') 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 23, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'хлопок' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 24, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'конопля' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 25, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'крапива' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 26, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'ткань' 
AND material_type_id IS NULL;

-- Кожа и мех
UPDATE inventory 
SET material_type_id = 27, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'кожа' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 28, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'замша' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 29, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'сыромять' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 30, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'мех' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 31, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'пергамент' 
AND material_type_id IS NULL;

-- Прочие материалы
UPDATE inventory 
SET material_type_id = 32, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'кость' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 33, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'рог' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 34, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'янтарь' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 35, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'стекло' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 36, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'керамика' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 37, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'камень' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 38, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'глина' 
AND material_type_id IS NULL;

-- Комбинированные материалы
UPDATE inventory 
SET material_type_id = 39, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('железо/дерево', 'железо, ясень', 'железо, дерево', 'металл/дерево') 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 40, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) = 'кожа/металл' 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 41, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('дерево/кожа', 'дерево\/кожа') 
AND material_type_id IS NULL;

UPDATE inventory 
SET material_type_id = 42, updated_at = CURRENT_TIMESTAMP
WHERE LOWER(TRIM(material)) IN ('стекло/янтарь', 'стекло\/янтарь') 
AND material_type_id IS NULL;

-- 3. Показываем результаты миграции
SELECT 
    'Результаты миграции:' as info,
    '' as material,
    '' as count
UNION ALL
SELECT 
    '--------------------------------------------',
    '',
    ''
UNION ALL
SELECT 
    'Обновлено записей:' as info,
    COUNT(*)::text as material,
    '' as count
FROM inventory 
WHERE material_type_id IS NOT NULL
UNION ALL
SELECT 
    'Пропущено записей:' as info,
    COUNT(*)::text as material,
    '' as count
FROM inventory 
WHERE material IS NOT NULL 
AND material != ''
AND material_type_id IS NULL;

-- 4. Показываем детальную статистику по обновленным материалам
SELECT 
    imt.name as "Материал из справочника",
    COUNT(i.id) as "Количество предметов",
    STRING_AGG(DISTINCT i.material, ', ') as "Исходные названия"
FROM inventory i
JOIN inventory_material_types imt ON i.material_type_id = imt.id
GROUP BY imt.id, imt.name, imt.sort_order
ORDER BY imt.sort_order, imt.name;

-- 5. Показываем материалы, которые не удалось сопоставить
SELECT 
    'Не сопоставленные материалы:' as info,
    '' as material,
    '' as count
UNION ALL
SELECT 
    '--------------------------------------------',
    '',
    ''
UNION ALL
SELECT 
    CONCAT('ID: ', id::text, ' - "', material, '"') as info,
    '' as material,
    '' as count
FROM inventory 
WHERE material IS NOT NULL 
AND material != ''
AND material_type_id IS NULL
ORDER BY id; 