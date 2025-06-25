-- Миграция базы данных Valravn: добавление VK полей и других обновлений
-- Выполнить в Render.com PostgreSQL Database

-- 1. Добавляем новые поля для VK OAuth в таблицу users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS vk_id BIGINT,
ADD COLUMN IF NOT EXISTS first_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS is_whitelisted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 2. Создаем таблицу VK whitelist
CREATE TABLE IF NOT EXISTS vk_whitelist (
    id SERIAL PRIMARY KEY,
    vk_id BIGINT NOT NULL UNIQUE,
    full_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    added_by_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Добавляем поля для системы взносов с модерацией
ALTER TABLE budget 
ADD COLUMN IF NOT EXISTS screenshot_path VARCHAR(500),
ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS contributor_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(id);

-- 4. Добавляем поля для системы инвентаря
ALTER TABLE inventory 
ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS image_path VARCHAR(500),
ADD COLUMN IF NOT EXISTS is_club_item BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 5. Создаем индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_vk_id ON users(vk_id);
CREATE INDEX IF NOT EXISTS idx_vk_whitelist_vk_id ON vk_whitelist(vk_id);
CREATE INDEX IF NOT EXISTS idx_budget_is_approved ON budget(is_approved);
CREATE INDEX IF NOT EXISTS idx_budget_user_id ON budget(user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_created_by ON inventory(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_is_club_item ON inventory(is_club_item);

-- 6. Обновляем существующие записи в budget
-- Устанавливаем is_approved = TRUE для всех существующих взносов (считаем их уже одобренными)
UPDATE budget 
SET is_approved = TRUE, 
    approved_at = NOW(),
    contributor_name = description  -- Переносим описание в contributor_name для старых записей
WHERE is_approved IS NULL OR is_approved = FALSE;

-- 7. Комментарии к таблицам
COMMENT ON COLUMN users.vk_id IS 'VK user ID for OAuth authentication';
COMMENT ON COLUMN users.is_whitelisted IS 'Whether user is whitelisted for VK OAuth';
COMMENT ON TABLE vk_whitelist IS 'Whitelist of VK users allowed to access admin functions';
COMMENT ON COLUMN budget.screenshot_path IS 'Path to payment screenshot image';
COMMENT ON COLUMN budget.is_approved IS 'Whether the contribution is approved by admin';
COMMENT ON COLUMN budget.contributor_name IS 'Name of the contributor (from VK or manual)';
COMMENT ON COLUMN inventory.is_club_item IS 'Whether the item belongs to the club';
COMMENT ON COLUMN inventory.image_path IS 'Path to item image file';

-- Показываем результат миграции
SELECT 'Migration completed successfully!' as status;

-- Показываем обновленную структуру основных таблиц
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('users', 'budget', 'inventory', 'vk_whitelist')
ORDER BY table_name, ordinal_position; 