-- Миграция для добавления таблицы запросов на связывание аккаунтов
-- Дата: 2024-01-20

CREATE TABLE IF NOT EXISTS account_link_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by INTEGER REFERENCES users(id),
    
    -- Индексы для оптимизации
    UNIQUE(user_id, target_user_id, status) -- Предотвращает дубликаты активных запросов
);

CREATE INDEX IF NOT EXISTS idx_account_link_requests_user_id ON account_link_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_account_link_requests_target_user_id ON account_link_requests(target_user_id);
CREATE INDEX IF NOT EXISTS idx_account_link_requests_status ON account_link_requests(status);

-- Комментарии для документации
COMMENT ON TABLE account_link_requests IS 'Запросы пользователей на связывание дублирующихся аккаунтов';
COMMENT ON COLUMN account_link_requests.user_id IS 'ID пользователя, который отправил запрос';
COMMENT ON COLUMN account_link_requests.target_user_id IS 'ID пользователя, которому отправлен запрос';
COMMENT ON COLUMN account_link_requests.status IS 'Статус запроса: pending, approved, rejected';
COMMENT ON COLUMN account_link_requests.message IS 'Опциональное сообщение от пользователя';
COMMENT ON COLUMN account_link_requests.processed_by IS 'ID пользователя или админа, который обработал запрос'; 