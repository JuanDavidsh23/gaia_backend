from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from schemas.skill import UserSkillsRequest
from services.skill_service import save_user_skills

router = APIRouter()

# ---------- DEPENDENCIA DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ONBOARDING HABILIDADES ----------
@router.post("/onboarding/skills")
def add_user_skills(data: UserSkillsRequest, db: Session = Depends(get_db)):
    """
    Endpoint para recibir las habilidades que el usuario 
    quiere aprender y enseñar desde el frontend
    """
    return save_user_skills(db, data)
