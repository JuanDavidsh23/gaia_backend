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
@router.post("/onboarding/skills", summary="Add User Skills Onboarding")
def add_user_skills(data: UserSkillsRequest, db: Session = Depends(get_db)):
    # Asocia las habilidades que el usuario quiere aprender y enseñar.
    return save_user_skills(db, data)
