-- Миграция для добавления справочников и изменения структуры inventory
-- Дата: $(date)

-- 1. Создаем справочник типов операций бюджета
CREATE TABLE IF NOT EXISTS budget_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 2. Создаем справочник типов предметов инвентаря
CREATE TABLE IF NOT EXISTS inventory_item_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 3. Заполняем справочник типов операций бюджета базовыми значениями
INSERT INTO budget_types (name, description, sort_order) VALUES
('Взнос', 'Взносы участников клуба', 1),
('Расход', 'Расходы клуба', 2),
('Доход', 'Прочие доходы', 3),
('Долг', 'Долговые обязательства', 4),
('Погашение Долга', 'Погашение долгов', 5),
('Возврат', 'Возврат средств', 6)
ON CONFLICT (name) DO NOTHING;

-- 4. Заполняем справочник типов предметов инвентаря базовыми значениями
INSERT INTO inventory_item_types (name, description, sort_order) VALUES
('Оружие', 'Мечи, топоры, копья и другое оружие', 1),
('Доспехи', 'Кольчуги, шлемы, щиты', 2),
('Украшения', 'Браслеты, кольца, подвески', 3),
('Бытовые предметы', 'Посуда, инструменты, утварь', 4),
('Одежда', 'Элементы костюма', 5),
('Аксессуары', 'Ремни, сумки, прочие аксессуары', 6),
('Прочее', 'Другие предметы', 99)
ON CONFLICT (name) DO NOTHING;

-- 5. Изменяем структуру таблицы inventory
-- Добавляем новое поле owner_user_id
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS owner_user_id INTEGER;

-- Создаем внешний ключ на users
ALTER TABLE inventory ADD CONSTRAINT fk_inventory_owner_user 
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- 6. Мигрируем данные из старого поля owner в новое owner_user_id
-- Сначала пытаемся найти пользователей по username
UPDATE inventory 
SET owner_user_id = (
    SELECT u.id 
    FROM users u 
    WHERE u.username = inventory.owner 
    LIMIT 1
)
WHERE owner_user_id IS NULL 
AND EXISTS (
    SELECT 1 FROM users u WHERE u.username = inventory.owner
);

-- Затем пытаемся найти по имени и фамилии для VK пользователей
UPDATE inventory 
SET owner_user_id = (
    SELECT u.id 
    FROM users u 
    WHERE CONCAT(u.first_name, ' ', u.last_name) = inventory.owner 
    AND u.vk_id IS NOT NULL
    LIMIT 1
)
WHERE owner_user_id IS NULL 
AND EXISTS (
    SELECT 1 FROM users u 
    WHERE CONCAT(u.first_name, ' ', u.last_name) = inventory.owner 
    AND u.vk_id IS NOT NULL
);

-- 7. Создаем индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_inventory_owner_user_id ON inventory(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_budget_types_active ON budget_types(is_active);
CREATE INDEX IF NOT EXISTS idx_inventory_item_types_active ON inventory_item_types(is_active);

-- 8. Комментарии к изменениям
COMMENT ON COLUMN inventory.owner_user_id IS 'Владелец предмета (ссылка на пользователя)';
COMMENT ON TABLE budget_types IS 'Справочник типов операций бюджета';
COMMENT ON TABLE inventory_item_types IS 'Справочник типов предметов инвентаря';

-- ВНИМАНИЕ: Поле owner в таблице inventory оставляем для совместимости
-- После проверки работы системы его можно будет удалить:
-- ALTER TABLE inventory DROP COLUMN owner; 