from sqlalchemy.orm import Session
from models.user import User
from models.skill import Skill
from models.users_skills import UserSkill, IntentEnum
from schemas.skill import UserSkillsRequest
from fastapi import HTTPException

def save_user_skills(db: Session, data: UserSkillsRequest):
    # Guarda las habilidades que un usuario quiere aprender o enseñar, creandolas si no existen
    # Verificamos si el usuario existe
    user = db.query(User).filter(User.user_id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Función interna para procesar una lista de habilidades y su intención
    def _process_skills(skills_list, intent):
        for skill_name in skills_list:
            # Buscamos si la habilidad (ej. "React") ya existe en la DB global
            skill_name = skill_name.strip().lower()
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            
            # Si no existe, la creamos para que otros también puedan usarla
            if not skill:
                skill = Skill(name=skill_name)
                db.add(skill)
                db.flush() # flush() le asigna un skill_id sin guardar permanentemente aún

            # Ahora revisamos si el usuario ya tiene esta habilidad con esta intención
            existing_link = db.query(UserSkill).filter(
                UserSkill.user_id == user.user_id,
                UserSkill.skill_id == skill.skill_id,
                UserSkill.intent == intent
            ).first()

            # Si no existe, creamos el enlace en la tabla intermedia
            if not existing_link:
                user_skill = UserSkill(
                    user_id=user.user_id,
                    skill_id=skill.skill_id,
                    intent=intent
                )
                db.add(user_skill)

    # Procesamos las dos listas que vienen del frontend
    _process_skills(data.learn_skills, IntentEnum.learn)
    _process_skills(data.teach_skills, IntentEnum.teach)

    # Guardamos todos los cambios
    db.commit()

    return {"msg": "Habilidades guardadas exitosamente"}
