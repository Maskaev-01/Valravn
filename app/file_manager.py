import os
import aiofiles
import uuid
import base64
from typing import Optional, Tuple
from PIL import Image
from fastapi import UploadFile, HTTPException
import io

class FileManager:
    def __init__(self):
        self.upload_dir = "app/static/uploads"
        self.screenshots_dir = f"{self.upload_dir}/screenshots"
        self.inventory_images_dir = f"{self.upload_dir}/inventory"
        
        # Создаем директории если их нет
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.inventory_images_dir, exist_ok=True)
        
        # Разрешенные форматы изображений
        self.allowed_image_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        self.max_file_size = 20 * 1024 * 1024  # 20MB
        
    async def save_screenshot_to_base64(self, file: UploadFile) -> Tuple[str, str, int]:
        """Конвертирует скриншот в base64 для хранения в БД"""
        # Валидация файла
        if file.content_type not in self.allowed_image_types:
            raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены: JPEG, PNG, WebP")
        
        # Читаем содержимое файла
        content = await file.read()
        
        if len(content) > self.max_file_size:
            raise HTTPException(status_code=400, detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB")
        
        try:
            # Открываем изображение с помощью Pillow
            image = Image.open(io.BytesIO(content))
            
            # Максимальный размер для скриншотов
            max_size = (1920, 1080)
            
            # Изменяем размер если нужно
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Конвертируем в WebP для экономии места
            output_buffer = io.BytesIO()
            image.save(output_buffer, "WEBP", quality=85, optimize=True)
            webp_data = output_buffer.getvalue()
            
            # Кодируем в base64
            base64_data = base64.b64encode(webp_data).decode('utf-8')
            
            # Возвращаем base64 строку, имя файла и размер
            return base64_data, file.filename, len(webp_data)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка обработки изображения: {str(e)}")
    
    async def save_inventory_image_to_base64(self, file: UploadFile) -> Tuple[str, str, int]:
        """Конвертирует изображение предмета в base64 для хранения в БД"""
        # Валидация файла
        if file.content_type not in self.allowed_image_types:
            raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены: JPEG, PNG, WebP")
        
        # Читаем содержимое файла
        content = await file.read()
        
        if len(content) > self.max_file_size:
            raise HTTPException(status_code=400, detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB")
        
        try:
            # Открываем изображение с помощью Pillow
            image = Image.open(io.BytesIO(content))
            
            # Максимальный размер для изображений инвентаря
            max_size = (800, 600)
            
            # Изменяем размер если нужно
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Конвертируем в WebP для экономии места
            output_buffer = io.BytesIO()
            image.save(output_buffer, "WEBP", quality=90, optimize=True)
            webp_data = output_buffer.getvalue()
            
            # Кодируем в base64
            base64_data = base64.b64encode(webp_data).decode('utf-8')
            
            # Возвращаем base64 строку, имя файла и размер
            return base64_data, file.filename, len(webp_data)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка обработки изображения: {str(e)}")
    
    def get_image_data_url(self, base64_data: str) -> str:
        """Создает data URL для отображения изображения"""
        if not base64_data:
            return ""
        return f"data:image/webp;base64,{base64_data}"
    
    def get_image_size_mb(self, base64_data: str) -> float:
        """Возвращает размер base64 изображения в MB"""
        if not base64_data:
            return 0.0
        try:
            # Размер base64 строки примерно на 33% больше оригинального размера
            size_bytes = len(base64_data) * 3 / 4
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
    
    async def save_screenshot(self, file: UploadFile) -> str:
        """Сохраняет скриншот перевода (старый метод для обратной совместимости)"""
        # Валидация файла
        if file.content_type not in self.allowed_image_types:
            raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены: JPEG, PNG, WebP")
        
        # Читаем содержимое файла
        content = await file.read()
        
        if len(content) > self.max_file_size:
            raise HTTPException(status_code=400, detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB")
        
        # Генерируем уникальное имя файла
        file_extension = file.filename.split('.')[-1].lower()
        filename = f"screenshot_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(self.screenshots_dir, filename)
        
        # Конвертируем в WebP для экономии места
        webp_filename = f"screenshot_{uuid.uuid4().hex}.webp"
        webp_file_path = os.path.join(self.screenshots_dir, webp_filename)
        
        try:
            # Открываем изображение с помощью Pillow
            image = Image.open(io.BytesIO(content))
            
            # Максимальный размер для скриншотов
            max_size = (1920, 1080)
            
            # Изменяем размер если нужно
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем в WebP формате с качеством 85%
            image.save(webp_file_path, "WEBP", quality=85, optimize=True)
            
            # Возвращаем относительный путь для БД
            return f"/static/uploads/screenshots/{webp_filename}"
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка обработки изображения: {str(e)}")
    
    async def save_inventory_image(self, file: UploadFile) -> str:
        """Сохраняет изображение предмета инвентаря (старый метод для обратной совместимости)"""
        # Валидация файла
        if file.content_type not in self.allowed_image_types:
            raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены: JPEG, PNG, WebP")
        
        # Читаем содержимое файла
        content = await file.read()
        
        if len(content) > self.max_file_size:
            raise HTTPException(status_code=400, detail=f"Файл слишком большой. Максимальный размер: {self.max_file_size // (1024*1024)}MB")
        
        # Генерируем уникальное имя файла
        webp_filename = f"item_{uuid.uuid4().hex}.webp"
        webp_file_path = os.path.join(self.inventory_images_dir, webp_filename)
        
        try:
            # Открываем изображение с помощью Pillow
            image = Image.open(io.BytesIO(content))
            
            # Максимальный размер для изображений инвентаря
            max_size = (800, 600)
            
            # Изменяем размер если нужно
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем в WebP формате с качеством 90%
            image.save(webp_file_path, "WEBP", quality=90, optimize=True)
            
            # Возвращаем относительный путь для БД
            return f"/static/uploads/inventory/{webp_filename}"
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка обработки изображения: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """Удаляет файл"""
        try:
            # Убираем /static из пути для получения реального пути
            real_path = file_path.replace("/static/", "app/static/")
            
            if os.path.exists(real_path):
                os.remove(real_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Возвращает размер файла в MB"""
        try:
            real_path = file_path.replace("/static/", "app/static/")
            if os.path.exists(real_path):
                size_bytes = os.path.getsize(real_path)
                return size_bytes / (1024 * 1024)
            return 0.0
        except Exception:
            return 0.0

# Глобальный экземпляр
file_manager = FileManager() 