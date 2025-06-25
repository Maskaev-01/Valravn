# 🔧 Настройка VK OAuth - Решение проблемы авторизации

## ❌ Проблема
Ошибка: **"Выбранный способ авторизации не доступен для приложения. Попробуйте позже или обратитесь к администратору приложения"**

## ✅ Решение: Настройка VK приложения

### 1. Зайдите в VK Developers
🔗 https://dev.vk.com/

### 2. Создайте новое приложение
- Нажмите **"Мои приложения"**
- **"Создать приложение"**
- **Название**: "Valravn Budget"
- **Платформа**: "Веб-сайт"
- **Адрес сайта**: `https://valravn-budget.onrender.com`

### 3. ⚠️ КРИТИЧНО! Настройте OAuth
В настройках приложения:

#### **Настройки → OAuth настройки:**
- ✅ **Trusted redirect URI**: `https://valravn-budget.onrender.com/auth/vk/callback`
- ✅ **Включить OAuth для Open API**: ✓

#### **Настройки → Права доступа:**
- ✅ **Доступ к базовой информации**: ✓
- ❌ **НЕ включайте доступ к email** - это вызывает ошибку "invalid scope"

### 4. 🔑 Получите данные для .env
После создания приложения:
- **ID приложения** = `VK_APP_ID`
- **Защищённый ключ** = `VK_APP_SECRET`

### 5. 🌐 Настройте переменные в Render.com

Зайдите в панель Render.com → Environment:

```env
VK_APP_ID=ваш_реальный_id_приложения
VK_APP_SECRET=ваш_реальный_защищенный_ключ  
VK_REDIRECT_URI=https://valravn-budget.onrender.com/auth/vk/callback
```

### 6. ⚡ Перезапустите приложение
После добавления переменных в Render.com, приложение автоматически перезапустится.

---

## 🔍 Проверка настроек

### Проверьте эти пункты:

1. **✅ VK приложение создано** и имеет статус "Активно"
2. **✅ OAuth включен** в настройках приложения
3. **✅ Redirect URI точно совпадает**: `https://valravn-budget.onrender.com/auth/vk/callback`
4. **✅ Переменные добавлены в Render.com** и приложение перезапущено
5. **✅ ID и SECRET** скопированы правильно (без лишних пробелов)

### Тестирование:
1. Откройте https://valravn-budget.onrender.com/login
2. Должна появиться кнопка **"Войти через VK"**
3. При нажатии → перенаправление на VK
4. После авторизации → возврат в Valravn

---

## 🚨 Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| "Способ авторизации не доступен" | OAuth не включен в VK | Настройки → OAuth → Включить |
| "invalid scope" | Запрошен недоступный scope email | Убрать email из прав доступа |
| "Неверный redirect_uri" | URI не совпадает | Точно скопировать URL |
| "Кнопка VK не видна" | Переменные не установлены | Проверить в Render Environment |
| "Invalid client_id" | Неверный APP_ID | Скопировать правильный ID |

---

## 📝 Пример правильных настроек VK

**В панели VK:**
```
Название: Valravn Budget
Тип: Веб-сайт  
Домен: valravn-budget.onrender.com
OAuth: Включен
Redirect URI: https://valravn-budget.onrender.com/auth/vk/callback
Права: базовая информация
```

**В Render.com Environment:**
```
VK_APP_ID=12345678
VK_APP_SECRET=ABCdef123456789
VK_REDIRECT_URI=https://valravn-budget.onrender.com/auth/vk/callback
```

---

## ✅ После успешной настройки:

1. **VK кнопка появится** на странице входа
2. **Авторизация будет работать** без ошибок  
3. **Пользователи из whitelist** смогут войти
4. **Имена из VK** будут автоматически подставляться

**🎯 Если всё настроено правильно, VK OAuth заработает сразу!**

# 🆕 VK ID SDK - Новая система авторизации

## ⚠️ Важно: Старый OAuth больше не работает!

VK перешла на новую систему авторизации **VK ID SDK**. Старый OAuth2 flow выдает ошибку:
> **"Selected sign-in method not available for app"**

## ✅ Решение: Использование VK ID SDK

Теперь авторизация происходит через JavaScript виджет на странице входа.

### 1. 🔗 Настройте VK приложение в новой системе
**Используйте:** https://id.vk.com/about/business/

### 2. ✏️ Настройте Redirect URI
В настройках приложения установите:
```
https://valravn-budget.onrender.com/auth/login
```
**Обратите внимание:** теперь не `/callback`, а `/login`!

### 3. 🔑 Получите данные приложения
- **VK_APP_ID** = `53804218`
- **VK_APP_SECRET** = `tKe2RFL8sqLhDsHfTRs9` (защищённый ключ)

### 4. 🌐 Установите переменные в Render.com
```env
VK_APP_ID=53804218
VK_APP_SECRET=tKe2RFL8sqLhDsHfTRs9
VK_REDIRECT_URI=https://valravn-budget.onrender.com/auth/login
```

---

## 🎯 Как работает новая система:

### Старая система (НЕ работает):
```
1. Кнопка → Редирект на VK → Возврат с кодом → Обмен на токен
```

### Новая система VK ID SDK:
```
1. VK виджет на странице → Авторизация → JavaScript получает токен → Отправка на сервер
```

---

## 🚨 Обновленная таблица ошибок

| Ошибка | Причина | Решение |
|--------|---------|---------|
| "Selected sign-in method not available" | Старый OAuth не поддерживается | Перейти на VK ID SDK |
| "invalid scope" | Старые права доступа | Использовать пустой scope |
| "redirect_uri is incorrect" | Неправильный URI | Использовать `/auth/login` вместо `/callback` |
| "Кнопка VK не видна" | Переменные не установлены | Проверить Environment в Render |
| "Invalid client_id" | Неверный APP_ID | Использовать ID из новой системы VK ID |

---

## 📝 Правильные настройки

**В VK ID системе:**
```
Название: Valravn Budget
Тип: Веб-сайт  
Redirect URI: https://valravn-budget.onrender.com/auth/login
APP_ID: 53804218
```

**В Render.com:**
```
VK_APP_ID=53804218
VK_APP_SECRET=tKe2RFL8sqLhDsHfTRs9
VK_REDIRECT_URI=https://valravn-budget.onrender.com/auth/login
```

---

## ✅ После настройки:

1. ✅ **VK виджет появится** на странице входа
2. ✅ **Авторизация через JavaScript** работает сразу
3. ✅ **Пользователи из whitelist** могут войти
4. ✅ **Автозаполнение имен** из VK профилей

**🎯 VK ID SDK - современная и надежная авторизация!** 