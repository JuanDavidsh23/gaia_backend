from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from schemas.user import UserProfileResponse, UserUpdateRequest
from services.user_service import get_user_profile, update_user_profile

router = APIRouter()

# ---------- DEPENDENCIA DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- OBTENER PERFIL ----------
@router.get("/users/{user_id}", response_model=UserProfileResponse)
def read_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Devuelve los datos actuales del usuario para llenar
    el formulario de "Mi Perfil" en el Frontend.
    """
    return get_user_profile(db, user_id)

# ---------- ACTUALIZAR PERFIL ----------
@router.put("/users/{user_id}", response_model=UserProfileResponse)
def edit_user_profile(user_id: int, data: UserUpdateRequest, db: Session = Depends(get_db)):
    """
    Recibe los datos nuevos (bio, foto, teléfono, etc.)
    y los actualiza en la base de datos.
    """
    return update_user_profile(db, user_id, data)
