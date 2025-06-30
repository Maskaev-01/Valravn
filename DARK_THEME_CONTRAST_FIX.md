# Исправления контрастности темной темы

## Описание проблемы

В темной теме Valravn были обнаружены проблемы с контрастностью текста на красном фоне, что затрудняло чтение и ухудшало пользовательский опыт.

## Принцип исправления

Установлено четкое правило для темной темы:
**На красном фоне всегда должен быть белый или черный текст для максимального контраста**

## Внесенные изменения

### 1. Красные кнопки и элементы
```css
/* Красные кнопки - белый текст на красном фоне */
.dark .bg-red-500,
.dark .bg-red-600,
.dark .bg-red-700,
.dark .bg-red-800,
.dark .bg-red-900 {
  background-color: var(--raven-red) !important;
  color: var(--raven-white) !important;
}
```

### 2. Valravn брендовые кнопки
```css
/* Valravn кнопки - черный текст на красном фоне для лучшего контраста */
.dark .bg-valravn-600,
.dark .bg-valravn-700,
.dark .bg-valravn-500 {
  background-color: var(--raven-red) !important;
  color: var(--raven-black) !important;
}
```

### 3. Светлые красные фоны
```css
/* Светлые красные фоны - белый текст */
.dark .bg-valravn-50,
.dark .bg-valravn-100,
.dark .bg-valravn-200 {
  background-color: var(--raven-dark-red) !important;
  color: var(--raven-white) !important;
}
```

### 4. Красные уведомления и алерты
```css
/* Красные уведомления - белый текст */
.dark .bg-red-50.text-red-700,
.dark .bg-red-50.text-red-800 {
  background-color: var(--raven-dark-red) !important;
  color: var(--raven-white) !important;
}
```

### 5. Красные бейджи и теги
```css
/* Красные бейджи - белый текст на темно-красном фоне */
.dark .bg-red-100.text-red-800 {
  background-color: var(--raven-dark-red) !important;
  color: var(--raven-white) !important;
}
```

### 6. Hover эффекты
```css
/* Hover эффекты для красных элементов */
.dark .hover\:bg-red-50:hover,
.dark .hover\:bg-red-100:hover {
  background-color: var(--raven-red) !important;
  color: var(--raven-white) !important;
}
```

### 7. Специальные элементы
- Кнопки с красным фоном - всегда белый текст
- Спаны и теги с красным фоном - белый текст
- Ссылки в красных контейнерах - белый текст с hover эффектом

## Цветовая палитра

Используемые цвета из палитры Valravn:
- `--raven-red: #A4161A` - основной красный
- `--raven-bright-red: #BA181B` - яркий красный для hover
- `--raven-dark-red: #660708` - темно-красный для фонов
- `--raven-white: #FFFFFF` - белый текст
- `--raven-black: #0B090A` - черный текст

## Результат

✅ Все красные элементы в темной теме теперь имеют высокий контраст
✅ Текст легко читается на любом красном фоне
✅ Соблюдены принципы accessibility (доступности)
✅ Сохранена визуальная целостность дизайна

## Затронутые элементы

- Кнопки (bg-red-*, bg-valravn-*)
- Уведомления и алерты (bg-red-50, bg-red-100)
- Бейджи и теги администратора
- Hover эффекты
- Границы и рамки
- Ссылки в красных контейнерах
- JavaScript генерируемые элементы

## Совместимость

Изменения применяются только к темной теме (`.dark` класс) и не влияют на светлую тему. 