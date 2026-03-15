from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.user import UserCreate, UserLogin
from services.auth_service import register_user, login_user

router = APIRouter()


# ---------- REGISTER ----------
@router.post("/register", summary="Register a new user")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Registra un nuevo usuario en la base de datos
    return register_user(db, user)


# ---------- LOGIN ----------
@router.post("/login", summary="User Login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Autentica al usuario y devuelve el token JWT
    return login_user(db, user)