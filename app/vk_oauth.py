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

    def is_configured(self) -> bool:
        """Проверяет, настроен ли VK OAuth"""
        return bool(self.app_id and self.app_secret)

# Глобальный экземпляр
vk_oauth = VKOAuth() 