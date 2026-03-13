from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserUpdate
from core.security import get_current_user, get_db

router = APIRouter(prefix="/user")

# GET: Obtener datos del usuario
@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    print(f"GET user {user_id}")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# PUT: Actualizar biografía
@router.put("/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.user_id != user_id and current_user.role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user_update.bio is not None:
        user.bio = user_update.bio
    if user_update.avatar_url is not None:
        user.avatar_url = user_update.avatar_url
    
    db.commit()
    db.refresh(user)
    return user
