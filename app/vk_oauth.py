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
        """Получает информацию о пользователе по access token (для VK ID SDK)"""
        params = {
            "user_ids": user_id,
            "fields": "photo_100,first_name,last_name",
            "access_token": access_token,
            "v": "5.131"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}/users.get", params=params)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
                
            data = response.json()
            
            if "error" in data:
                raise HTTPException(status_code=400, detail=f"VK API error: {data['error']['error_msg']}")
                
            if not data.get("response"):
                raise HTTPException(status_code=400, detail="No user data received")
                
            return data["response"][0]

    def is_configured(self) -> bool:
        """Проверяет, настроен ли VK OAuth"""
        return bool(self.app_id and self.app_secret)

# Глобальный экземпляр
vk_oauth = VKOAuth() 