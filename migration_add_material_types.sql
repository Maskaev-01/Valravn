-- Миграция: Добавление справочника материалов для инвентаря
-- Дата: 2025-01-01
-- Описание: Создаем справочник материалов для стандартизации данных

-- 1. Создаем таблицу справочника материалов
CREATE TABLE IF NOT EXISTS inventory_material_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),  -- Категория материала (металл, дерево, ткань и т.д.)
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 2. Добавляем индексы
CREATE INDEX idx_inventory_material_types_active ON inventory_material_types(is_active);
CREATE INDEX idx_inventory_material_types_category ON inventory_material_types(category);

-- 3. Заполняем базовыми материалами

-- Металлы
INSERT INTO inventory_material_types (name, category, description, sort_order) VALUES
('Железо', 'Металл', 'Черный металл, основа для оружия и инструментов', 100),
('Сталь', 'Металл', 'Углеродистая сталь для оружия', 101),
('Латунь', 'Металл', 'Сплав меди и цинка для украшений', 102),
('Бронза', 'Металл', 'Сплав меди и олова', 103),
('Серебро', 'Металл', 'Драгоценный металл для украшений', 104),
('Медь', 'Металл', 'Цветной металл', 105),
('Олово', 'Металл', 'Мягкий металл для сплавов', 106),
('Свинец', 'Металл', 'Тяжелый металл', 107),
('Золото', 'Металл', 'Драгоценный металл', 108),
('Металл', 'Металл', 'Неопределенный металл', 199);

-- Дерево
INSERT INTO inventory_material_types (name, category, description, sort_order) VALUES
('Дуб', 'Дерево', 'Твердая порода для щитов и рукоятей', 200),
('Ясень', 'Дерево', 'Гибкая древесина для древков копий', 201),
('Береза', 'Дерево', 'Легкая древесина', 202),
('Сосна', 'Дерево', 'Хвойная древесина', 203),
('Ель', 'Дерево', 'Хвойная древесина', 204),
('Липа', 'Дерево', 'Мягкая древесина для резьбы', 205),
('Клен', 'Дерево', 'Твердая древесина', 206),
('Орех', 'Дерево', 'Ценная древесина', 207),
('Дерево', 'Дерево', 'Неопределенная древесина', 299);

-- Ткани
INSERT INTO inventory_material_types (name, category, description, sort_order) VALUES
('Лён', 'Ткань', 'Натуральная растительная ткань', 300),
('Шерсть', 'Ткань', 'Натуральная животная ткань', 301),
('Шелк', 'Ткань', 'Дорогая импортная ткань', 302),
('Хлопок', 'Ткань', 'Растительная ткань', 303),
('Конопля', 'Ткань', 'Грубая растительная ткань', 304),
('Крапива', 'Ткань', 'Ткань из крапивы', 305),
('Ткань', 'Ткань', 'Неопределенная ткань', 399);

-- Кожа и мех
INSERT INTO inventory_material_types (name, category, description, sort_order) VALUES
('Кожа', 'Кожа', 'Выделанная кожа', 400),
('Замша', 'Кожа', 'Мягкая кожа', 401),
('Сыромять', 'Кожа', 'Невыделанная кожа', 402),
('Мех', 'Кожа', 'Мех животных', 403),
('Пергамент', 'Кожа', 'Тонкая кожа для письма', 404);

-- Прочие материалы
INSERT INTO inventory_material_types (name, category, description, sort_order) VALUES
('Кость', 'Органика', 'Кость животных', 500),
('Рог', 'Органика', 'Рог животных', 501),
('Янтарь', 'Органика', 'Окаменевшая смола', 502),
('Стекло', 'Минерал', 'Стеклянные изделия', 600),
('Керамика', 'Минерал', 'Глиняные изделия', 601),
('Камень', 'Минерал', 'Природный камень', 602),
('Глина', 'Минерал', 'Необожженная глина', 603);

-- Комбинированные материалы
INSERT INTO inventory_material_types (name, category, description, sort_order) VALUES
('Железо/Дерево', 'Комбинированный', 'Сочетание железа и дерева', 700),
('Кожа/Металл', 'Комбинированный', 'Сочетание кожи и металла', 701),
('Дерево/Кожа', 'Комбинированный', 'Сочетание дерева и кожи', 702),
('Стекло/Янтарь', 'Комбинированный', 'Сочетание стекла и янтаря', 703);

-- 4. Добавляем поле material_type_id в таблицу inventory
ALTER TABLE inventory 
ADD COLUMN material_type_id INTEGER REFERENCES inventory_material_types(id) ON DELETE SET NULL;

-- 5. Создаем индекс
CREATE INDEX idx_inventory_material_type_id ON inventory(material_type_id);

-- 6. Проверяем результат
SELECT category, COUNT(*) as materials_count 
FROM inventory_material_types 
GROUP BY category 
ORDER BY category; 