from pydantic import BaseModel, EmailStr, ConfigDict
from app.database.models import UserRole
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)  # Updated for Pydantic v2

class UpdateUserRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    mobile: Optional[str] = None
    new_password: Optional[str] = None

