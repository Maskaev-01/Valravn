from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from fastapi import UploadFile

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class VKUserCreate(BaseModel):
    vk_id: str
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_admin: int
    vk_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_whitelisted: Optional[bool] = False
    created_at: datetime

    class Config:
        from_attributes = True

class BudgetCreate(BaseModel):
    price: float
    description: str
    data: date
    type: str = "Взнос"
    contributor_name: Optional[str] = None

class BudgetWithScreenshot(BaseModel):
    price: float
    description: str
    data: date
    type: str = "Взнос"
    contributor_name: Optional[str] = None
    # screenshot будет передаваться как UploadFile отдельно

class Budget(BaseModel):
    id: int
    price: float
    description: str
    data: date
    type: str
    screenshot_path: Optional[str] = None
    is_approved: bool = False
    user_id: Optional[int] = None
    contributor_name: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None

    class Config:
        from_attributes = True

class BudgetApproval(BaseModel):
    is_approved: bool

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
    is_club_item: bool = False

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
    image_path: Optional[str] = None
    created_by_user_id: Optional[int] = None
    is_club_item: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VKWhitelistCreate(BaseModel):
    vk_id: str
    username: str
    is_admin: bool = False

class VKWhitelist(BaseModel):
    id: int
    vk_id: str
    username: str
    is_admin: bool
    added_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True 