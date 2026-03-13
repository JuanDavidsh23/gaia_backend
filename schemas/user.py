from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    user = 'user'
    admin = 'admin'
    superadmin = 'superadmin'
    teacher = 'teacher'

class UserCreate(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    password: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr 
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    bio: str = None
    avatar_url: str = None 

class UserUpdate(BaseModel):
    bio: str = None
    avatar_url: str = None