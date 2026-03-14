from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User
from schemas.user import UserUpdateRequest

def get_user_profile(db: Session, user_id: int):
    # Recupera los datos completos del perfil de un usuario, junto con sus habilidades
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

from fastapi import HTTPException, UploadFile
import uuid
from core.database import supabase

def update_user_profile(db: Session, user_id: int, data: UserUpdateRequest, foto: UploadFile = None):
    # Actualiza los datos del perfil y opcionalmente sube una nueva imagen a Supabase
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # --- LÓGICA DE SUBIDA DE IMAGEN A SUPABASE ---
    if foto and supabase:
        try:
            # Generamos un nombre único para evitar sobreescribir fotos de otros
            file_extension = foto.filename.split(".")[-1]
            unique_filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
            
            # Subimos el archivo al bucket llamado 'avatars' (Debes crear este bucket en Supabase)
            # foto.file.read() lee los bytes de la imagen
            res = supabase.storage.from_("avatars").upload(
                file=foto.file.read(),
                path=unique_filename,
                file_options={"content-type": foto.content_type}
            )
            
            # Obtenemos la URL pública para guardarla en la Base de Datos
            public_url = supabase.storage.from_("avatars").get_public_url(unique_filename)
            
            # Asignamos esa URL a nuestro objeto 'data' para que se guarde abajo
            data.avatar_url = public_url

        except Exception as e:
            # Si algo falla con la subida, se lo decimos al Front
            raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {str(e)}")
            
    # --- FIN LÓGICA DE IMAGEN ---
    
    # Solo actualizamos los campos que el Frontend envió (que no son None)
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    
    return user
