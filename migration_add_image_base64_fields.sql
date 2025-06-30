-- Migration: Add base64 image storage fields
-- Date: 2025-01-27
-- Description: Добавляет поля для хранения изображений в base64 формате в БД для решения проблемы с очисткой папки uploads при редеплое

-- Добавляем поля для хранения изображений инвентаря в base64
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS image_data TEXT;
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS image_filename VARCHAR(255);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS image_size INTEGER;

-- НЕ создаем индекс на image_data - он может превышать лимит PostgreSQL 8191 байт
-- Вместо этого создаем частичный индекс только на ID для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_inventory_has_image_partial ON inventory(id) WHERE image_data IS NOT NULL;

-- Добавляем поля для хранения скриншотов бюджета в base64
ALTER TABLE budget ADD COLUMN IF NOT EXISTS screenshot_data TEXT;
ALTER TABLE budget ADD COLUMN IF NOT EXISTS screenshot_filename VARCHAR(255);
ALTER TABLE budget ADD COLUMN IF NOT EXISTS screenshot_size INTEGER;

-- НЕ создаем индекс на screenshot_data - он может превышать лимит PostgreSQL 8191 байт
-- Вместо этого создаем частичный индекс только на ID для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_budget_has_screenshot_partial ON budget(id) WHERE screenshot_data IS NOT NULL;

-- Добавляем комментарии к полям
COMMENT ON COLUMN inventory.image_data IS 'Base64 encoded image data (WebP format)';
COMMENT ON COLUMN inventory.image_filename IS 'Original filename of uploaded image';
COMMENT ON COLUMN inventory.image_size IS 'Size of image in bytes';

COMMENT ON COLUMN budget.screenshot_data IS 'Base64 encoded screenshot data (WebP format)';
COMMENT ON COLUMN budget.screenshot_filename IS 'Original filename of uploaded screenshot';
COMMENT ON COLUMN budget.screenshot_size IS 'Size of screenshot in bytes';

-- Создаем функцию для получения размера base64 данных
CREATE OR REPLACE FUNCTION get_base64_size(base64_data TEXT) 
RETURNS INTEGER AS $$
BEGIN
    IF base64_data IS NULL OR base64_data = '' THEN
        RETURN 0;
    END IF;
    -- Base64 увеличивает размер примерно на 33%
    RETURN LENGTH(base64_data) * 3 / 4;
END;
$$ LANGUAGE plpgsql;

-- Создаем view для статистики по изображениям
CREATE OR REPLACE VIEW image_storage_stats AS
SELECT 
    'inventory' as table_name,
    COUNT(*) as total_records,
    COUNT(image_data) as records_with_base64,
    COUNT(image_path) as records_with_files,
    SUM(CASE WHEN image_data IS NOT NULL THEN get_base64_size(image_data) ELSE 0 END) as total_base64_bytes,
    AVG(CASE WHEN image_data IS NOT NULL THEN get_base64_size(image_data) ELSE NULL END) as avg_base64_bytes
FROM inventory
UNION ALL
SELECT 
    'budget' as table_name,
    COUNT(*) as total_records,
    COUNT(screenshot_data) as records_with_base64,
    COUNT(screenshot_path) as records_with_files,
    SUM(CASE WHEN screenshot_data IS NOT NULL THEN get_base64_size(screenshot_data) ELSE 0 END) as total_base64_bytes,
    AVG(CASE WHEN screenshot_data IS NOT NULL THEN get_base64_size(screenshot_data) ELSE NULL END) as avg_base64_bytes
FROM budget;

-- Показываем информацию о миграции
SELECT 'Migration completed successfully!' as status,
       'Added base64 image storage fields to inventory and budget tables' as description,
       NOW() as completed_at; 