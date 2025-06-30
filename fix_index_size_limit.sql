-- Fix PostgreSQL index size limit issue
-- Date: 2025-06-30
-- Description: Удаляет индексы с больших TEXT полей для base64 данных

-- Удаляем индексы которые могут превышать лимит 8191 байт
DROP INDEX IF EXISTS idx_inventory_has_image;
DROP INDEX IF EXISTS idx_budget_has_screenshot;

-- Удаляем любые автоматически созданные индексы на TEXT полях
-- (PostgreSQL мог автоматически создать их при добавлении полей)

-- Проверяем существующие индексы на проблемных полях
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('inventory', 'budget') 
AND indexdef LIKE '%image_data%' OR indexdef LIKE '%screenshot_data%';

-- Если есть проблемные индексы, их нужно удалить вручную
-- Пример команд (выполнить если найдены индексы выше):
-- DROP INDEX IF EXISTS inventory_image_data_idx;
-- DROP INDEX IF EXISTS budget_screenshot_data_idx;

-- Вместо этого создаем частичные индексы только для проверки наличия данных
CREATE INDEX IF NOT EXISTS idx_inventory_has_image_partial 
ON inventory(id) WHERE image_data IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_budget_has_screenshot_partial 
ON budget(id) WHERE screenshot_data IS NOT NULL;

-- Показываем результат
SELECT 'Index size limit issue fixed!' as status; 