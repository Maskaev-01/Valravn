from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

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
    price = Column(Float)
    description = Column(String)
    data = Column(Date)  # используем оригинальное название поля
    type = Column(String)
    
    # Новые поля для модерации
    screenshot_path = Column(String, nullable=True)  # Путь к скриншоту перевода
    is_approved = Column(Boolean, default=False)     # Одобрен ли взнос
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # ИСПРАВЛЕНИЕ: добавляем SET NULL
    contributor_name = Column(String, nullable=True)  # Имя из VK или введенное вручную
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # ИСПРАВЛЕНИЕ: добавляем SET NULL

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(Text)  # Строковое поле для обратной совместимости
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Владелец (ссылка на пользователя)
    item_name = Column(Text, nullable=False)
    item_type = Column(Text)  # Старое поле - оставляем для обратной совместимости
    item_type_id = Column(Integer, ForeignKey("inventory_item_types.id", ondelete="SET NULL"), nullable=True)  # Новое поле
    subtype = Column(Text)
    material = Column(Text)
    color = Column(Text)
    size = Column(Text)
    find_type = Column(Text)
    region = Column(Text)
    place = Column(Text)
    burial_number = Column(Text)
    notes = Column(Text)
    
    # Новые поля
    image_path = Column(String, nullable=True)        # Путь к фотографии предмета
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # ИСПРАВЛЕНИЕ: добавляем SET NULL
    is_club_item = Column(Boolean, default=False)    # Клубный ли предмет
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Отношения
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    item_type_ref = relationship("InventoryItemType", foreign_keys=[item_type_id])

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