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
@router.get("/users/{user_id}", response_model=UserProfileResponse, summary="Get User Profile")
def read_user_profile(user_id: int, db: Session = Depends(get_db)):
    # Devuelve el perfil completo del usuario con sus habilidades
    return get_user_profile(db, user_id)

from fastapi import APIRouter, Depends, UploadFile, File, Form

# ---------- ACTUALIZAR PERFIL ----------
@router.put("/users/{user_id}", response_model=UserProfileResponse, summary="Update User Profile")
def edit_user_profile(
    user_id: int, 
    first_name: str = Form(None),
    last_name: str = Form(None),
    bio: str = Form(None),
    phone: str = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Actualiza los datos del usuario y permite subir una foto al storage de Supabase
    # Empacamos los datos en el esquema que ya teníamos
    data = UserUpdateRequest(
        first_name=first_name,
        last_name=last_name,
        bio=bio,
        phone=phone
    )
    return update_user_profile(db, user_id, data, foto)
