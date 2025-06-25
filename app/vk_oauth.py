import os
import httpx
import urllib.parse
from typing import Optional, Dict, Any
from fastapi import HTTPException

# VK OAuth settings
VK_APP_ID = os.getenv("VK_APP_ID")
VK_APP_SECRET = os.getenv("VK_APP_SECRET")
VK_REDIRECT_URI = os.getenv("VK_REDIRECT_URI", "https://valravn-budget.onrender.com/login")
VK_SERVICE_TOKEN = os.getenv("VK_SERVICE_TOKEN")  # Сервисный токен для VK API

class VKOAuth:
    def __init__(self):
        self.app_id = VK_APP_ID
        self.app_secret = VK_APP_SECRET
        self.redirect_uri = VK_REDIRECT_URI
        self.service_token = VK_SERVICE_TOKEN
        self.api_url = "https://api.vk.com/method"

    def is_configured(self) -> bool:
        """Проверяет, настроен ли VK OAuth"""
        return bool(self.app_id and self.app_secret)
    
    def has_service_token(self) -> bool:
        """Проверяет, есть ли сервисный токен для VK API"""
        return bool(self.service_token)
    
    async def resolve_screen_name(self, screen_name: str) -> Optional[str]:
        """
        Определяет числовой ID пользователя по псевдониму или ID
        Возвращает числовой ID или None если не найден
        """
        if not self.has_service_token():
            # Если нет сервисного токена, попробуем определить числовой ID
            if screen_name.isdigit():
                return screen_name
            # Если не числовой и нет токена - возвращаем как есть
            return screen_name
        
        # Если уже числовой ID, возвращаем как есть
        if screen_name.isdigit():
            return screen_name
        
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    'screen_name': screen_name,
                    'access_token': self.service_token,
                    'v': '5.131'
                }
                
                response = await client.get(f"{self.api_url}/utils.resolveScreenName", params=params)
                response.raise_for_status()
                
                data = response.json()
                if data.get('response') and data['response'].get('type') == 'user':
                    return str(data['response']['object_id'])
                    
        except Exception as e:
            print(f"Error resolving screen name {screen_name}: {e}")
        
        return None
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о пользователе по VK ID
        """
        if not self.has_service_token():
            return None
            
        try:
            # Сначала получаем числовой ID если передан псевдоним
            resolved_id = await self.resolve_screen_name(user_id)
            if not resolved_id:
                return None
                
            async with httpx.AsyncClient() as client:
                params = {
                    'user_ids': resolved_id,
                    'fields': 'photo_100,screen_name,contacts',  # Добавляем contacts для получения email
                    'access_token': self.service_token,
                    'v': '5.131'
                }
                
                response = await client.get(f"{self.api_url}/users.get", params=params)
                response.raise_for_status()
                
                data = response.json()
                if data.get('response') and len(data['response']) > 0:
                    user_data = data['response'][0]
                    return {
                        'id': str(user_data['id']),
                        'first_name': user_data.get('first_name', ''),
                        'last_name': user_data.get('last_name', ''),
                        'photo_100': user_data.get('photo_100'),
                        'screen_name': user_data.get('screen_name'),
                        'email': user_data.get('email'),  # Email если доступен
                        'is_closed': user_data.get('is_closed', False),
                        'can_access_closed': user_data.get('can_access_closed', True)
                    }
                    
        except Exception as e:
            print(f"Error getting user info for {user_id}: {e}")
        
        return None

# Глобальный экземпляр
vk_oauth = VKOAuth() 