from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User
from schemas.user import UserUpdateRequest

def get_user_profile(db: Session, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    from models.users_skills import UserSkill, IntentEnum
    from models.skill import Skill
    
    # Habilidades que quiere enseñar
    teach_skills_query = db.query(Skill.name).join(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.intent == IntentEnum.teach
    ).all()
    
    # Habilidades que quiere aprender
    learn_skills_query = db.query(Skill.name).join(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.intent == IntentEnum.learn
    ).all()

    # Formateamos un nuevo diccionario para que cumpla con el Schema de respuesta
    profile_data = {
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "phone": user.phone,
        "skills_to_teach": [s[0] for s in teach_skills_query],
        "skills_to_learn": [s[0] for s in learn_skills_query]
    }
    
    return profile_data

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
