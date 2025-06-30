-- Миграция для исправления Foreign Key Constraints
-- Исправляет ошибку при удалении пользователей

-- 1. Удаляем старые constraints если они существуют
ALTER TABLE budget DROP CONSTRAINT IF EXISTS budget_user_id_fkey;
ALTER TABLE budget DROP CONSTRAINT IF EXISTS budget_approved_by_fkey;
ALTER TABLE inventory DROP CONSTRAINT IF EXISTS inventory_created_by_user_id_fkey;
ALTER TABLE vk_whitelist DROP CONSTRAINT IF EXISTS vk_whitelist_added_by_fkey;

-- 2. Добавляем новые constraints с правильным поведением при удалении

-- Budget table constraints
ALTER TABLE budget 
ADD CONSTRAINT budget_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE budget 
ADD CONSTRAINT budget_approved_by_fkey 
FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;

-- Inventory table constraints  
ALTER TABLE inventory 
ADD CONSTRAINT inventory_created_by_user_id_fkey 
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- VK Whitelist table constraints
ALTER TABLE vk_whitelist 
ADD CONSTRAINT vk_whitelist_added_by_fkey 
FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL;

-- Account Link Requests constraints (если таблица существует)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'account_link_requests') THEN
        -- Удаляем старые constraints
        ALTER TABLE account_link_requests DROP CONSTRAINT IF EXISTS account_link_requests_user_id_fkey;
        ALTER TABLE account_link_requests DROP CONSTRAINT IF EXISTS account_link_requests_target_user_id_fkey;
        ALTER TABLE account_link_requests DROP CONSTRAINT IF EXISTS account_link_requests_processed_by_fkey;
        
        -- Добавляем новые constraints
        ALTER TABLE account_link_requests 
        ADD CONSTRAINT account_link_requests_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        
        ALTER TABLE account_link_requests 
        ADD CONSTRAINT account_link_requests_target_user_id_fkey 
        FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE;
        
        ALTER TABLE account_link_requests 
        ADD CONSTRAINT account_link_requests_processed_by_fkey 
        FOREIGN KEY (processed_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 3. Создаем индексы для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_budget_user_id ON budget(user_id);
CREATE INDEX IF NOT EXISTS idx_budget_approved_by ON budget(approved_by);
CREATE INDEX IF NOT EXISTS idx_inventory_created_by_user_id ON inventory(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_vk_whitelist_added_by ON vk_whitelist(added_by);

-- Выводим результат
SELECT 'Foreign key constraints fixed successfully!' as result; 