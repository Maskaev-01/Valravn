-- Fix updated_at fields to have DEFAULT NOW()
-- Date: 2025-06-30
-- Description: Добавляет DEFAULT NOW() для поля updated_at во всех таблицах

-- Исправляем таблицу inventory
ALTER TABLE inventory ALTER COLUMN updated_at SET DEFAULT NOW();

-- Исправляем таблицу budget
ALTER TABLE budget ALTER COLUMN updated_at SET DEFAULT NOW();

-- Исправляем справочники
ALTER TABLE budget_types ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE inventory_item_types ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE inventory_material_types ALTER COLUMN updated_at SET DEFAULT NOW();

-- Показываем результат
SELECT 'updated_at defaults fixed successfully!' as status; 