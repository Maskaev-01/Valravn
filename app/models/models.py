from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0)  # 0 - обычный пользователь, 1 - админ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Budget(Base):
    __tablename__ = "budget"
    
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float)
    description = Column(String)
    data = Column(Date)  # используем оригинальное название поля
    type = Column(String)

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(Text, nullable=False)
    item_name = Column(Text, nullable=False)
    item_type = Column(Text)
    subtype = Column(Text)
    material = Column(Text)
    color = Column(Text)
    size = Column(Text)
    find_type = Column(Text)
    region = Column(Text)
    place = Column(Text)
    burial_number = Column(Text)
    notes = Column(Text) 