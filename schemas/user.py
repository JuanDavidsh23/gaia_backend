from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    password: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr 
    password: str 

# Para enviar el Perfil al Frontend (Lectura)
from typing import Optional, List

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

# Para recibir la actualización del Frontend (Escritura)
class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None