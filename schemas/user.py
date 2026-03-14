from pydantic import BaseModel, EmailStr
from typing import Optional, List

# Esquema para registrar un nuevo usuario.
class UserCreate(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    password: str
    phone: str

# Esquema para el login de usuario.
class UserLogin(BaseModel):
    email: EmailStr 
    password: str 

# Esquema para la respuesta del perfil de usuario.
class UserProfileResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    skills_to_learn: List[str] = []
    skills_to_teach: List[str] = []

# Esquema para actualizar el perfil de usuario.
class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None