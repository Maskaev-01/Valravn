-- Исправление ограничения NOT NULL для поля hashed_password
-- Выполнить в Render.com PostgreSQL Database для исправления ошибки синхронизации

-- 1. Снимаем ограничение NOT NULL с поля hashed_password
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;

-- 2. Исправляем тип данных vk_id если нужно (с BIGINT на VARCHAR)
-- Сначала проверяем текущий тип
DO $$
BEGIN
    -- Если тип BIGINT, меняем на VARCHAR
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'vk_id' 
        AND data_type = 'bigint'
    ) THEN
        ALTER TABLE users ALTER COLUMN vk_id TYPE VARCHAR(255);
    END IF;
END $$;

-- 3. Аналогично для таблицы vk_whitelist
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vk_whitelist' 
        AND column_name = 'vk_id' 
        AND data_type = 'bigint'
    ) THEN
        ALTER TABLE vk_whitelist ALTER COLUMN vk_id TYPE VARCHAR(255);
    END IF;
END $$;

-- 4. Создаем уникальный индекс для vk_id в users (исключая NULL) если его нет
DROP INDEX IF EXISTS idx_users_vk_id;  -- Удаляем старый индекс если есть
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_vk_id_unique ON users(vk_id) WHERE vk_id IS NOT NULL;

-- 5. Обновляем комментарий к полю
COMMENT ON COLUMN users.hashed_password IS 'Password hash, nullable for VK users';

-- Проверяем результат
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('hashed_password', 'vk_id')
ORDER BY column_name;

SELECT 'Fix applied successfully! VK users can now be synced.' as status; 