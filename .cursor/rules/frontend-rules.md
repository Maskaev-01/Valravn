# Frontend Development Rules

## 🎨 ТЕХНОЛОГИЧЕСКИЙ СТЕК

### Основные технологии:
- **Jinja2** - шаблонизатор Python
- **Tailwind CSS** - utility-first CSS фреймворк
- **Alpine.js** - легкий JavaScript фреймворк
- **Font Awesome** - иконки
- **Custom Valravn Theme** - брендинг клуба

---

## 🏗️ АРХИТЕКТУРА ШАБЛОНОВ

### Структура директории templates:
```
templates/
├── base.html           # Базовый шаблон
├── login.html          # Авторизация
├── register.html       # Регистрация
├── dashboard.html      # Главная страница
├── profile.html        # Профиль пользователя
├── reports.html        # Отчеты
├── contributors.html   # Участники
├── add_contribution.html # Добавление взноса
├── admin/              # Админ панель
│   ├── dashboard.html
│   ├── users.html
│   ├── budget.html
│   ├── inventory.html
│   ├── moderation.html
│   └── vk_whitelist.html
└── inventory/          # Инвентарь
    ├── list.html
    ├── add.html
    ├── edit.html
    ├── detail.html
    └── summary.html
```

---

## 📐 БАЗОВЫЙ ШАБЛОН (base.html)

### Структура base.html:
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Valravn{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'valravn': {
                            50: '#f0f9ff',
                            500: '#0ea5e9',
                            600: '#0284c7',
                            900: '#0c4a6e'
                        }
                    }
                }
            }
        }
    </script>
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-50">
    <!-- Навигация -->
    {% include 'partials/navigation.html' %}
    
    <!-- Основной контент -->
    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Футер -->
    {% include 'partials/footer.html' %}
</body>
</html>
```

### Правила наследования:
- **ВСЕГДА** наследуй от `base.html`
- **ВСЕГДА** определяй блоки `title` и `content`
- **Используй** дополнительные блоки для специфических стилей/скриптов

```html
{% extends "base.html" %}

{% block title %}Название страницы - Valravn{% endblock %}

{% block content %}
<!-- Контент страницы -->
{% endblock %}
```

---

## 🎨 TAILWIND CSS СТИЛИЗАЦИЯ

### Цветовая схема Valravn:
```css
/* Основные цвета */
bg-valravn-50    /* Очень светлый голубой */
bg-valravn-500   /* Основной голубой */
bg-valravn-600   /* Темнее основного */
bg-valravn-900   /* Темно-синий */

/* Использование */
text-valravn-600 hover:text-valravn-700
bg-valravn-500 hover:bg-valravn-600
border-valravn-300
```

### Стандартные компоненты:

#### Кнопки:
```html
<!-- Основная кнопка -->
<button class="bg-valravn-600 hover:bg-valravn-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
    Действие
</button>

<!-- Вторичная кнопка -->
<button class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition duration-200">
    Отмена
</button>

<!-- Опасная кнопка -->
<button class="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
    Удалить
</button>
```

#### Формы:
```html
<!-- Поле ввода -->
<div class="mb-4">
    <label for="field" class="block text-sm font-medium text-gray-700 mb-2">
        Название поля
    </label>
    <input type="text" id="field" name="field" required
           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-valravn-500 focus:border-valravn-500">
</div>

<!-- Селект -->
<select class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-valravn-500">
    <option value="">Выберите...</option>
    <option value="1">Вариант 1</option>
</select>

<!-- Textarea -->
<textarea class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-valravn-500 resize-none" rows="4"></textarea>
```

#### Карточки:
```html
<div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Заголовок</h3>
    <p class="text-gray-600">Содержимое карточки</p>
</div>
```

#### Таблицы:
```html
<div class="overflow-x-auto">
    <table class="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Колонка
                </th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Данные
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

---

## ⚡ ALPINE.JS ИНТЕРАКТИВНОСТЬ

### Основные директивы:

#### x-data - состояние компонента:
```html
<div x-data="{ 
    showModal: false, 
    loading: false,
    formData: {
        name: '',
        email: ''
    }
}">
    <!-- Компонент -->
</div>
```

#### x-show/x-if - условное отображение:
```html
<!-- x-show: элемент остается в DOM -->
<div x-show="showModal" class="fixed inset-0 bg-gray-600 bg-opacity-50">
    Модальное окно
</div>

<!-- x-if: элемент удаляется из DOM -->
<template x-if="items.length === 0">
    <p>Нет элементов</p>
</template>
```

#### x-on - обработка событий:
```html
<button x-on:click="showModal = true">Открыть</button>
<button @click="showModal = true">Открыть (сокращенно)</button>

<!-- Предотвращение стандартного поведения -->
<form @submit.prevent="submitForm()">
    <button type="submit">Отправить</button>
</form>
```

#### x-model - двустороннее связывание:
```html
<input x-model="formData.name" type="text" placeholder="Имя">
<p x-text="'Привет, ' + formData.name"></p>
```

### Типичные паттерны:

#### Модальное окно:
```html
<div x-data="{ showModal: false }">
    <!-- Кнопка открытия -->
    <button @click="showModal = true" class="bg-valravn-600 text-white px-4 py-2 rounded">
        Открыть модальное окно
    </button>
    
    <!-- Модальное окно -->
    <div x-show="showModal" 
         x-transition:enter="ease-out duration-300"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
        
        <div @click.away="showModal = false" 
             class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 class="text-lg font-semibold mb-4">Заголовок</h3>
            <p class="text-gray-600 mb-4">Содержимое модального окна</p>
            
            <div class="flex justify-end space-x-2">
                <button @click="showModal = false" 
                        class="bg-gray-300 text-gray-700 px-4 py-2 rounded">
                    Отмена
                </button>
                <button class="bg-valravn-600 text-white px-4 py-2 rounded">
                    Подтвердить
                </button>
            </div>
        </div>
    </div>
</div>
```

---

**🎨 Frontend - лицо приложения. Делай его красивым, быстрым и удобным!** 