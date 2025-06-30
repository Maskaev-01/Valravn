# VK OAuth Integration Rules

## 🔐 VK ID SDK - Современная авторизация VK

### ⚠️ КРИТИЧНО: Старый OAuth2 НЕ РАБОТАЕТ
VK полностью перешла на VK ID SDK. Используй ТОЛЬКО новую систему.

---

## 🏗️ АРХИТЕКТУРА VK ИНТЕГРАЦИИ

### Компоненты системы:
1. **VK ID SDK** (клиентская часть) - в `login.html`
2. **VKOAuth класс** - в `app/vk_oauth.py`
3. **VK Whitelist** - система разрешений
4. **Account Linking** - связывание аккаунтов

### Поток авторизации:
```
1. Пользователь → VK ID виджет
2. VK возвращает данные → JavaScript
3. JavaScript → POST /auth/vk/process
4. Сервер проверяет whitelist
5. Создание/обновление пользователя
6. JWT токен → cookie
```

---

## 🔑 КОНФИГУРАЦИЯ

### Обязательные переменные:
```env
VK_APP_ID=53804218                    # ID приложения VK
VK_APP_SECRET=tKe2RFL8sqLhDsHfTRs9   # Секретный ключ
VK_REDIRECT_URI=https://domain.com/auth/login  # НЕ /callback!
```

### Опциональные переменные:
```env
VK_SERVICE_TOKEN=your_service_token   # Для получения данных пользователей
```

### Настройка VK приложения:
- **Тип**: Веб-сайт
- **Redirect URI**: `https://domain.com/auth/login` (НЕ callback!)
- **Домен**: `domain.com`

---

## 🛡️ WHITELIST СИСТЕМА

### Принцип работы:
- **Таблица `vk_whitelist`** содержит разрешенные VK ID
- **Проверка при каждой авторизации**
- **Админы могут добавлять пользователей**

### Добавление в whitelist:
```python
# ВСЕГДА проверяй права админа
@router.post("/admin/vk-whitelist/add")
async def add_to_vk_whitelist(
    current_user: User = Depends(get_admin_user),  # ОБЯЗАТЕЛЬНО!
    db: Session = Depends(get_db)
):
    # Получение данных из VK API (если есть сервисный токен)
    if vk_oauth.has_service_token():
        user_info = await vk_oauth.get_user_info(vk_id)
```

### Структура whitelist:
```sql
CREATE TABLE vk_whitelist (
    id SERIAL PRIMARY KEY,
    vk_id VARCHAR UNIQUE,           -- VK ID пользователя
    username VARCHAR,               -- Имя из VK
    is_admin BOOLEAN DEFAULT FALSE, -- Админские права
    added_by INTEGER,               -- Кто добавил
    created_at TIMESTAMP
);
```

---

## 👤 СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ

### Функция `create_or_update_vk_user`:
```python
def create_or_update_vk_user(db, vk_id, first_name, last_name, avatar_url, email):
    # 1. ОБЯЗАТЕЛЬНАЯ проверка whitelist
    whitelist_entry = db.query(VKWhitelist).filter(VKWhitelist.vk_id == vk_id).first()
    if not whitelist_entry:
        raise HTTPException(status_code=403, detail="VK ID не в whitelist")
    
    # 2. Поиск существующего пользователя
    user = db.query(User).filter(User.vk_id == vk_id).first()
    
    # 3. Связывание по email (если есть)
    if not user and email:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user and not existing_user.vk_id:
            # Связываем аккаунты
            existing_user.vk_id = vk_id
            return existing_user
    
    # 4. Создание нового пользователя
    if not user:
        user = User(
            username=generate_username(first_name, last_name, vk_id),
            vk_id=vk_id,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            email=email,
            is_admin=1 if whitelist_entry.is_admin else 0,
            hashed_password=None  # VK пользователи без пароля
        )
```

---

## 🔄 VK API ИНТЕГРАЦИЯ

### VKOAuth класс методы:

#### `get_user_info(user_id)`:
```python
async def get_user_info(self, user_id: str) -> Optional[Dict]:
    """Получает данные пользователя из VK API"""
    if not self.has_service_token():
        return None
    
    # Преобразование псевдонима в числовой ID
    resolved_id = await self.resolve_screen_name(user_id)
    
    # Запрос к VK API
    params = {
        'user_ids': resolved_id,
        'fields': 'photo_100,screen_name',
        'access_token': self.service_token,
        'v': '5.131'
    }
```

#### `resolve_screen_name(screen_name)`:
```python
async def resolve_screen_name(self, screen_name: str) -> Optional[str]:
    """Преобразует псевдоним в числовой ID"""
    if screen_name.isdigit():
        return screen_name  # Уже числовой ID
    
    # Запрос к utils.resolveScreenName
```

---

## 🎨 FRONTEND ИНТЕГРАЦИЯ

### VK ID SDK в шаблоне:
```html
<!-- В login.html -->
<script src="https://unpkg.com/@vkid/sdk@<3.0.0/dist-sdk/umd/index.js"></script>
<script>
VKID.Config.init({
    app: {{ vk_app_id }},
    redirectUrl: '{{ vk_redirect_uri }}',
    responseMode: VKID.ConfigResponseMode.Callback,
    source: VKID.ConfigSource.LOWCODE,
});

const oneTap = new VKID.OneTap();
oneTap.render({
    container: document.getElementById('vk-auth-container'),
    showAlternativeLogin: false
})
.on(VKID.OneTapInternalEvents.LOGIN_SUCCESS, function(payload) {
    // Обработка успешной авторизации
    VKID.Auth.exchangeCode(payload.code, payload.device_id)
        .then(data => {
            // Отправка данных на сервер
            fetch('/auth/vk/process', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_id: data.user_id,
                    first_name: data.first_name,
                    last_name: data.last_name,
                    photo_100: data.photo_100
                })
            });
        });
});
</script>
```

### Кнопка поиска пользователя:
```html
<!-- В admin/vk_whitelist.html -->
<button type="button" id="fetch-user-btn" onclick="fetchUserInfo()">
    <i class="fas fa-search"></i>
</button>

<script>
async function fetchUserInfo() {
    const vkId = document.getElementById('vk_id').value;
    const response = await fetch(`/auth/api/vk-user-info?user_id=${vkId}`);
    const data = await response.json();
    
    if (data.success) {
        // Автозаполнение формы
        document.getElementById('username').value = data.user.full_name;
    }
}
</script>
```

---

## 🚨 ОБРАБОТКА ОШИБОК

### Типичные ошибки VK:

#### "VK ID не в whitelist":
```python
# В create_or_update_vk_user
if not whitelist_entry:
    raise HTTPException(status_code=403, detail="VK ID не в whitelist. Обратитесь к администратору.")
```

#### "Selected sign-in method not available":
- **Причина**: Старый OAuth2 код
- **Решение**: Используй только VK ID SDK

#### "Invalid redirect_uri":
- **Причина**: Неправильный URI в настройках VK
- **Решение**: Используй `/auth/login`, НЕ `/callback`

#### "Service token unauthorized":
```python
# Проверка сервисного токена
def has_service_token(self) -> bool:
    return bool(self.service_token)

# Graceful fallback без токена
if not vk_oauth.has_service_token():
    # Используем только базовые данные от VK ID SDK
    final_username = f"VK User {vk_id}"
```

---

## 🔧 ОТЛАДКА И ТЕСТИРОВАНИЕ

### Логирование VK процессов:
```python
print(f"VK Data received: {data}")                    # Входящие данные
print(f"Processing VK user: {user_id} - {first_name}") # Обработка
print(f"User created/updated: {user.username}")       # Результат
print(f"VK Auth Error: {str(e)}")                     # Ошибки
```

### Тестовые эндпоинты:
```python
@app.get("/test-routes")
async def test_routes():
    return {
        "vk_oauth_configured": vk_oauth.is_configured(),
        "has_service_token": vk_oauth.has_service_token(),
        "routes": {
            "vk_process": "/auth/vk/process",
            "vk_whitelist": "/auth/admin/vk-whitelist"
        }
    }
```

### Проверка конфигурации:
```bash
# Проверка переменных окружения
curl https://domain.com/test-routes

# Проверка VK API доступности
curl "https://api.vk.com/method/users.get?user_ids=1&v=5.131&access_token=TOKEN"
```

---

## 📋 ЧЕКЛИСТ VK ИНТЕГРАЦИИ

### При настройке нового VK приложения:
- [ ] Создано VK приложение типа "Веб-сайт"
- [ ] Настроен правильный Redirect URI (`/auth/login`)
- [ ] Получены APP_ID и APP_SECRET
- [ ] Переменные добавлены в окружение
- [ ] Получен сервисный токен (опционально)

### При добавлении VK пользователя:
- [ ] Пользователь добавлен в VK whitelist
- [ ] Проверены права доступа (is_admin)
- [ ] Протестирована авторизация
- [ ] Проверено автозаполнение данных

### При отладке проблем:
- [ ] Проверены логи сервера
- [ ] Проверена консоль браузера
- [ ] Проверены переменные окружения
- [ ] Проверена конфигурация VK приложения

---

## 🎯 ЛУЧШИЕ ПРАКТИКИ

### Безопасность:
- **НИКОГДА** не храни VK токены в localStorage
- **ВСЕГДА** проверяй whitelist перед созданием пользователя
- **ВСЕГДА** используй HTTPS для VK редиректов
- **Ограничивай** доступ к админским функциям

### Производительность:
- **Кешируй** данные пользователей из VK API
- **Используй** batch запросы для множественных операций
- **Ограничивай** частоту запросов к VK API

### UX:
- **Показывай** понятные ошибки пользователям
- **Автозаполняй** формы данными из VK
- **Предоставляй** альтернативные способы входа

---

**🔐 VK OAuth - критически важная часть системы. Тестируй каждое изменение!** 