-- Простая миграция материалов инвентаря
-- Обновляет поле material_type_id на основе существующих текстовых значений
-- Дата: 2025-01-01

-- Металлы
UPDATE inventory SET material_type_id = 1, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'железо' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 2, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'сталь' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 3, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'латунь' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 4, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'бронза' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 5, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'серебро' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 6, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'медь' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 7, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'олово' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 8, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'свинец' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 9, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'золото' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 10, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'металл' AND material_type_id IS NULL;

-- Дерево
UPDATE inventory SET material_type_id = 11, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'дуб' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 12, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'ясень' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 13, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('береза', 'берёза') AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 14, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'сосна' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 15, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'ель' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 16, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'липа' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 17, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('клен', 'клён') AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 18, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'орех' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 19, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'дерево' AND material_type_id IS NULL;

-- Ткани
UPDATE inventory SET material_type_id = 20, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('лён', 'лен') AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 21, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'шерсть' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 22, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('шелк', 'шёлк') AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 23, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'хлопок' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 24, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'конопля' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 25, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'крапива' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 26, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'ткань' AND material_type_id IS NULL;

-- Кожа и мех
UPDATE inventory SET material_type_id = 27, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'кожа' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 28, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'замша' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 29, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'сыромять' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 30, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'мех' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 31, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'пергамент' AND material_type_id IS NULL;

-- Прочие материалы
UPDATE inventory SET material_type_id = 32, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'кость' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 33, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'рог' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 34, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'янтарь' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 35, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'стекло' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 36, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'керамика' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 37, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'камень' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 38, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'глина' AND material_type_id IS NULL;

-- Комбинированные материалы
UPDATE inventory SET material_type_id = 39, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('железо/дерево', 'железо, ясень', 'железо, дерево', 'металл/дерево') AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 40, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) = 'кожа/металл' AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 41, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('дерево/кожа', 'дерево\/кожа') AND material_type_id IS NULL;
UPDATE inventory SET material_type_id = 42, updated_at = CURRENT_TIMESTAMP WHERE LOWER(TRIM(material)) IN ('стекло/янтарь', 'стекло\/янтарь') AND material_type_id IS NULL;

-- Показать результат
SELECT 
    'Миграция завершена. Обновлено записей:' as message,
    COUNT(*) as count
FROM inventory 
WHERE material_type_id IS NOT NULL; 