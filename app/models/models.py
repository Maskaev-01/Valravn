from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # Теперь может быть null для VK users
    is_admin = Column(Integer, default=0)  # 0 - обычный пользователь, 1 - админ
    
    # VK OAuth поля
    vk_id = Column(String, unique=True, index=True, nullable=True)  # VK User ID
    first_name = Column(String, nullable=True)  # Имя из VK
    last_name = Column(String, nullable=True)   # Фамилия из VK
    avatar_url = Column(String, nullable=True)  # Аватар из VK
    
    # Whitelist для админов
    is_whitelisted = Column(Boolean, default=False)  # Разрешен ли доступ через VK
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Budget(Base):
    __tablename__ = "budget"
    
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    data = Column(Date, nullable=False, index=True)
    type = Column(String(50), nullable=False, default="Взнос", index=True)
    contributor_name = Column(String(100), nullable=True, index=True)
    is_approved = Column(Boolean, default=False, nullable=False, index=True)
    screenshot_path = Column(String(500), nullable=True)  # Оставляем для обратной совместимости
    screenshot_data = Column(Text, nullable=True)  # Новое поле для хранения base64 скриншота
    screenshot_filename = Column(String(255), nullable=True)  # Оригинальное имя файла
    screenshot_size = Column(Integer, nullable=True)  # Размер скриншота в байтах
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by_user = relationship("User", back_populates="budget_entries")

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(100), nullable=False, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    item_name = Column(String(200), nullable=False, index=True)
    item_type = Column(String(100), nullable=True, index=True)
    item_type_id = Column(Integer, ForeignKey("inventory_item_types.id", ondelete="SET NULL"), nullable=True)
    subtype = Column(String(100), nullable=True)
    material = Column(String(100), nullable=True, index=True)
    material_type_id = Column(Integer, ForeignKey("inventory_material_types.id", ondelete="SET NULL"), nullable=True)
    color = Column(String(50), nullable=True)
    size = Column(String(50), nullable=True)
    find_type = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    place = Column(String(200), nullable=True)
    burial_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_club_item = Column(Boolean, default=False, nullable=False)
    image_path = Column(String(500), nullable=True)  # Оставляем для обратной совместимости
    image_data = Column(Text, nullable=True)  # Новое поле для хранения base64 изображения
    image_filename = Column(String(255), nullable=True)  # Оригинальное имя файла
    image_size = Column(Integer, nullable=True)  # Размер изображения в байтах
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner_user = relationship("User", foreign_keys=[owner_user_id], back_populates="owned_inventory")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    item_type_ref = relationship("InventoryItemType", back_populates="inventory_items")
    material_type_ref = relationship("InventoryMaterialType", back_populates="inventory_items")

# Новая таблица для VK whitelist (админы)
class VKWhitelist(Base):
    __tablename__ = "vk_whitelist"
    
    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)  # Имя пользователя из VK
    is_admin = Column(Boolean, default=False)   # Админские права
    added_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)   # ИСПРАВЛЕНИЕ: добавляем SET NULL
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# НОВЫЕ СПРАВОЧНИКИ
class BudgetType(Base):
    """Справочник типов операций бюджета"""
    __tablename__ = "budget_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Название типа
    description = Column(String, nullable=True)         # Описание
    is_active = Column(Boolean, default=True)           # Активен ли тип
    sort_order = Column(Integer, default=0)             # Порядок сортировки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class InventoryItemType(Base):
    """Справочник типов предметов инвентаря"""
    __tablename__ = "inventory_item_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Название типа
    description = Column(String, nullable=True)         # Описание
    is_active = Column(Boolean, default=True)           # Активен ли тип
    sort_order = Column(Integer, default=0)             # Порядок сортировки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class InventoryMaterialType(Base):
    """Справочник материалов для инвентаря"""
    __tablename__ = "inventory_material_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Название материала
    category = Column(String, nullable=True)            # Категория (Металл, Дерево, Ткань и т.д.)
    description = Column(String, nullable=True)         # Описание
    is_active = Column(Boolean, default=True)           # Активен ли материал
    sort_order = Column(Integer, default=0)             # Порядок сортировки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AccountLinkRequest(Base):
    """Запросы на связывание аккаунтов"""
    __tablename__ = "account_link_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # ИСПРАВЛЕНИЕ: CASCADE для обязательных связей
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # ИСПРАВЛЕНИЕ: CASCADE для обязательных связей
    status = Column(String, default="pending")  # pending, approved, rejected
    message = Column(Text, nullable=True)  # Опциональное сообщение от пользователя
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # ИСПРАВЛЕНИЕ: SET NULL для опциональных

    # Отношения
    requester = relationship("User", foreign_keys=[user_id])
    target = relationship("User", foreign_keys=[target_user_id])
    processor = relationship("User", foreign_keys=[processed_by]) 