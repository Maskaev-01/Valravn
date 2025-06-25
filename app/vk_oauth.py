import os
import httpx
import urllib.parse
from typing import Optional, Dict, Any
from fastapi import HTTPException

# VK OAuth settings
VK_APP_ID = os.getenv("VK_APP_ID")
VK_APP_SECRET = os.getenv("VK_APP_SECRET")
VK_REDIRECT_URI = os.getenv("VK_REDIRECT_URI", "https://valravn-budget.onrender.com/login")

class VKOAuth:
    def __init__(self):
        self.app_id = VK_APP_ID
        self.app_secret = VK_APP_SECRET
        self.redirect_uri = VK_REDIRECT_URI
        self.api_url = "https://api.vk.com/method"

    async def get_user_info_by_token(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """Получает информацию о пользователе по access token"""
        params = {
            "user_ids": user_id,
            "fields": "photo_100,first_name,last_name",
            "access_token": access_token,
            "v": "5.131"
        }
        
        # Добавляем заголовки для обхода проблем с IP
        headers = {
            "User-Agent": "VKAndroidApp/7.45-13627 (Android 11; SDK 30; arm64-v8a; samsung SM-G991B; ru; 2340x1080)"
        }
        
        async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
            try:
                response = await client.get(f"{self.api_url}/users.get", params=params)
                
                if response.status_code != 200:
                    print(f"VK API response status: {response.status_code}")
                    print(f"VK API response text: {response.text}")
                    raise HTTPException(status_code=400, detail="Failed to get user info from VK")
                    
                data = response.json()
                print(f"VK API response: {data}")  # Отладка
                
                if "error" in data:
                    error_msg = data['error'].get('error_msg', 'Unknown VK API error')
                    print(f"VK API error: {error_msg}")
                    raise HTTPException(status_code=400, detail=f"VK API error: {error_msg}")
                    
                if not data.get("response") or len(data["response"]) == 0:
                    raise HTTPException(status_code=400, detail="No user data received from VK")
                    
                return data["response"][0]
                
            except httpx.TimeoutException:
                raise HTTPException(status_code=400, detail="VK API timeout")
            except Exception as e:
                print(f"VK API exception: {str(e)}")
                raise HTTPException(status_code=400, detail=f"VK API request failed: {str(e)}")

    def is_configured(self) -> bool:
        """Проверяет, настроен ли VK OAuth"""
        return bool(self.app_id and self.app_secret)

# Глобальный экземпляр
vk_oauth = VKOAuth() 