from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User
from schemas.user import UserUpdateRequest

def get_user_profile(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

def update_user_profile(db: Session, user_id: int, data: UserUpdateRequest):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Solo actualizamos los campos que el Frontend envió (que no son None)
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    
    return user
