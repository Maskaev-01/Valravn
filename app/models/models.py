from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # Теперь может быть null для VK users
    is_admin = Column(Integer, default=0)  # 0 - обычный пользователь, 1 - админ (для обратной совместимости)
    
    # Расширенная ролевая модель
    role = Column(String(20), default='member', index=True)  # guest, member, moderator, admin, superadmin
    permissions = Column(JSON, default={})  # JSON с разрешениями
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    profile_settings = Column(JSON, default={})  # Настройки профиля
    notification_settings = Column(JSON, default={})  # Настройки уведомлений
    
    # VK OAuth поля
    vk_id = Column(String, unique=True, index=True, nullable=True)  # VK User ID
    first_name = Column(String, nullable=True)  # Имя из VK
    last_name = Column(String, nullable=True)   # Фамилия из VK
    avatar_url = Column(String, nullable=True)  # Аватар из VK
    
    # Whitelist для админов
    is_whitelisted = Column(Boolean, default=False)  # Разрешен ли доступ через VK
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    budget_entries = relationship("Budget", back_populates="created_by_user")
    owned_inventory = relationship("Inventory", foreign_keys="Inventory.owner_user_id", back_populates="owner_user")
    activity_logs = relationship("UserActivityLog", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    stats = relationship("UserStats", back_populates="user", uselist=False)

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class InventoryItemType(Base):
    """Справочник типов предметов инвентаря"""
    __tablename__ = "inventory_item_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Название типа
    description = Column(String, nullable=True)         # Описание
    is_active = Column(Boolean, default=True)           # Активен ли тип
    sort_order = Column(Integer, default=0)             # Порядок сортировки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    inventory_items = relationship("Inventory", back_populates="item_type_ref")

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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    inventory_items = relationship("Inventory", back_populates="material_type_ref")

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

# Новые модели для расширенной ролевой системы

class UserActivityLog(Base):
    """Лог активности пользователей"""
    __tablename__ = "user_activity_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")

class UserAchievement(Base):
    """Достижения пользователей"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_type = Column(String(50), nullable=False, index=True)
    achievement_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    badge_color = Column(String(20), nullable=True)
    earned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    progress = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="achievements")

class UserStats(Base):
    """Статистика пользователей для дашборда"""
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_contributions = Column(Float, default=0)
    contributions_count = Column(Integer, default=0)
    inventory_count = Column(Integer, default=0)
    club_inventory_count = Column(Integer, default=0)
    achievements_count = Column(Integer, default=0)
    last_contribution_date = Column(Date, nullable=True)
    last_inventory_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="stats") 