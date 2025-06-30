-- Отладочные запросы для проверки фильтра участников

-- 1. Проверяем все записи в таблице budget
SELECT 'Всего записей в budget:' as info, COUNT(*) as count FROM budget;

-- 2. Проверяем записи по типам
SELECT 'Записи по типам:' as info, type, COUNT(*) as count 
FROM budget 
GROUP BY type;

-- 3. Проверяем статус одобрения
SELECT 'Статус одобрения:' as info, is_approved, COUNT(*) as count 
FROM budget 
GROUP BY is_approved;

-- 4. Проверяем взносы с одобрением
SELECT 'Одобренные взносы:' as info, COUNT(*) as count 
FROM budget 
WHERE type = 'Взнос' AND is_approved = true;

-- 5. Проверяем contributor_name
SELECT 'Contributor names:' as info, 
       COALESCE(contributor_name, description) as contributor, 
       COUNT(*) as count
FROM budget 
WHERE type = 'Взнос' AND is_approved = true
GROUP BY COALESCE(contributor_name, description);

-- 6. Проверяем актуальный запрос фильтра
SELECT DISTINCT COALESCE(contributor_name, description) as contributor 
FROM budget 
WHERE type = 'Взнос' 
AND is_approved = true 
AND COALESCE(contributor_name, description) IS NOT NULL
AND TRIM(COALESCE(contributor_name, description)) != ''
ORDER BY contributor;

-- 7. Проверяем все взносы (включая неодобренные)
SELECT 'Все взносы (включая неодобренные):' as info,
       COALESCE(contributor_name, description) as contributor,
       is_approved,
       COUNT(*) as count
FROM budget 
WHERE type = 'Взнос'
GROUP BY COALESCE(contributor_name, description), is_approved
ORDER BY contributor; 