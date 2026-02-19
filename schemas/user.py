from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    password: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr 
    password: str 