-- Миграция для расширенной ролевой модели
-- Добавляем новые поля в таблицу users

-- 1. Добавляем поле role (enum)
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('guest', 'member', 'moderator', 'admin', 'superadmin'));

-- 2. Добавляем поле permissions (JSON)
ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}';

-- 3. Добавляем поле last_activity для отслеживания активности
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 4. Добавляем поле profile_settings для настроек профиля
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_settings JSONB DEFAULT '{}';

-- 5. Добавляем поле notification_settings для настроек уведомлений
ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_settings JSONB DEFAULT '{}';

-- 6. Мигрируем существующих админов
UPDATE users SET role = 'admin' WHERE is_admin = 1;

-- 7. Создаем первого суперадмина (если есть админы)
UPDATE users SET role = 'superadmin' WHERE id = (SELECT MIN(id) FROM users WHERE is_admin = 1);

-- 8. Создаем индексы для новых полей
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);

-- 9. Создаем таблицу для логирования действий пользователей
CREATE TABLE IF NOT EXISTS user_activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Создаем индексы для логов
CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_action ON user_activity_log(action);
CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at ON user_activity_log(created_at);

-- 11. Создаем таблицу для достижений пользователей
CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    badge_color VARCHAR(20),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE
);

-- 12. Создаем индексы для достижений
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_type ON user_achievements(achievement_type);
CREATE INDEX IF NOT EXISTS idx_user_achievements_earned_at ON user_achievements(earned_at);

-- 13. Создаем таблицу для статистики пользователей
CREATE TABLE IF NOT EXISTS user_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_contributions DECIMAL(12,2) DEFAULT 0,
    contributions_count INTEGER DEFAULT 0,
    inventory_count INTEGER DEFAULT 0,
    club_inventory_count INTEGER DEFAULT 0,
    achievements_count INTEGER DEFAULT 0,
    last_contribution_date DATE,
    last_inventory_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Создаем уникальный индекс для статистики
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id);

-- 15. Создаем функцию для обновления статистики
CREATE OR REPLACE FUNCTION update_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем статистику при изменении взносов
    IF TG_TABLE_NAME = 'budget' THEN
        INSERT INTO user_stats (user_id, total_contributions, contributions_count, last_contribution_date)
        VALUES (
            NEW.created_by_user_id,
            COALESCE(NEW.price, 0),
            1,
            NEW.data
        )
        ON CONFLICT (user_id) DO UPDATE SET
            total_contributions = user_stats.total_contributions + COALESCE(NEW.price, 0),
            contributions_count = user_stats.contributions_count + 1,
            last_contribution_date = GREATEST(user_stats.last_contribution_date, NEW.data),
            updated_at = CURRENT_TIMESTAMP;
    END IF;
    
    -- Обновляем статистику при изменении инвентаря
    IF TG_TABLE_NAME = 'inventory' THEN
        INSERT INTO user_stats (user_id, inventory_count, club_inventory_count, last_inventory_date)
        VALUES (
            NEW.created_by_user_id,
            1,
            CASE WHEN NEW.is_club_item THEN 1 ELSE 0 END,
            CURRENT_DATE
        )
        ON CONFLICT (user_id) DO UPDATE SET
            inventory_count = user_stats.inventory_count + 1,
            club_inventory_count = user_stats.club_inventory_count + CASE WHEN NEW.is_club_item THEN 1 ELSE 0 END,
            last_inventory_date = CURRENT_DATE,
            updated_at = CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 16. Создаем триггеры для автоматического обновления статистики
DROP TRIGGER IF EXISTS trigger_update_user_stats_budget ON budget;
CREATE TRIGGER trigger_update_user_stats_budget
    AFTER INSERT ON budget
    FOR EACH ROW
    EXECUTE FUNCTION update_user_stats();

DROP TRIGGER IF EXISTS trigger_update_user_stats_inventory ON inventory;
CREATE TRIGGER trigger_update_user_stats_inventory
    AFTER INSERT ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_user_stats();

-- 17. Инициализируем статистику для существующих пользователей
INSERT INTO user_stats (user_id, total_contributions, contributions_count, inventory_count, club_inventory_count)
SELECT 
    u.id,
    COALESCE(SUM(b.price), 0) as total_contributions,
    COUNT(b.id) as contributions_count,
    COUNT(i.id) as inventory_count,
    COUNT(CASE WHEN i.is_club_item THEN 1 END) as club_inventory_count
FROM users u
LEFT JOIN budget b ON u.id = b.created_by_user_id
LEFT JOIN inventory i ON u.id = i.created_by_user_id
GROUP BY u.id
ON CONFLICT (user_id) DO NOTHING;

-- 18. Добавляем комментарии к таблицам
COMMENT ON TABLE user_activity_log IS 'Лог активности пользователей для аналитики';
COMMENT ON TABLE user_achievements IS 'Достижения пользователей';
COMMENT ON TABLE user_stats IS 'Статистика пользователей для дашборда';

-- 19. Обновляем существующих пользователей с базовыми разрешениями
UPDATE users SET 
    permissions = '{"view_dashboard": true, "manage_own_inventory": true, "make_contributions": true}',
    profile_settings = '{"theme": "auto", "language": "ru"}',
    notification_settings = '{"email_notifications": true, "vk_notifications": true}'
WHERE role = 'member';

UPDATE users SET 
    permissions = '{"view_dashboard": true, "manage_own_inventory": true, "make_contributions": true, "moderate_budget": true, "view_reports": true}',
    profile_settings = '{"theme": "auto", "language": "ru"}',
    notification_settings = '{"email_notifications": true, "vk_notifications": true, "moderation_notifications": true}'
WHERE role = 'moderator';

UPDATE users SET 
    permissions = '{"view_dashboard": true, "manage_own_inventory": true, "make_contributions": true, "moderate_budget": true, "view_reports": true, "manage_users": true, "manage_inventory": true, "post_news": true}',
    profile_settings = '{"theme": "auto", "language": "ru"}',
    notification_settings = '{"email_notifications": true, "vk_notifications": true, "moderation_notifications": true, "admin_notifications": true}'
WHERE role = 'admin';

UPDATE users SET 
    permissions = '{"view_dashboard": true, "manage_own_inventory": true, "make_contributions": true, "moderate_budget": true, "view_reports": true, "manage_users": true, "manage_inventory": true, "post_news": true, "manage_admins": true, "system_settings": true}',
    profile_settings = '{"theme": "auto", "language": "ru"}',
    notification_settings = '{"email_notifications": true, "vk_notifications": true, "moderation_notifications": true, "admin_notifications": true, "system_notifications": true}'
WHERE role = 'superadmin';

-- 20. Создаем представление для удобного просмотра пользователей с ролями
CREATE OR REPLACE VIEW users_with_roles AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.role,
    u.is_admin,
    u.vk_id,
    u.first_name,
    u.last_name,
    u.avatar_url,
    u.is_whitelisted,
    u.created_at,
    u.last_activity,
    u.permissions,
    u.profile_settings,
    u.notification_settings,
    us.total_contributions,
    us.contributions_count,
    us.inventory_count,
    us.club_inventory_count,
    us.achievements_count,
    us.last_contribution_date,
    us.last_inventory_date
FROM users u
LEFT JOIN user_stats us ON u.id = us.user_id;

COMMENT ON VIEW users_with_roles IS 'Представление пользователей с полной информацией о ролях и статистике'; 