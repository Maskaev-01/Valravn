from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_admin: int
    created_at: datetime

    class Config:
        from_attributes = True

class BudgetCreate(BaseModel):
    price: float
    description: str
    data: date
    type: str = "Взнос"

class Budget(BaseModel):
    id: int
    price: float
    description: str
    data: date
    type: str

    class Config:
        from_attributes = True

class InventoryCreate(BaseModel):
    owner: str
    item_name: str
    item_type: Optional[str] = None
    subtype: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    find_type: Optional[str] = None
    region: Optional[str] = None
    place: Optional[str] = None
    burial_number: Optional[str] = None
    notes: Optional[str] = None

class Inventory(BaseModel):
    id: int
    owner: str
    item_name: str
    item_type: Optional[str] = None
    subtype: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    find_type: Optional[str] = None
    region: Optional[str] = None
    place: Optional[str] = None
    burial_number: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True 