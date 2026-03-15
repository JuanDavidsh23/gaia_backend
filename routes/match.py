from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from schemas.match import InteractionRequest
from services.match_service import create_interaction

router = APIRouter()

# ---------- DEPENDENCIA DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- SWIPES LIKES Y PASSES ----------
@router.post("/swipe", summary="Record a User Swipe")
def swipe_user(data: InteractionRequest, db: Session = Depends(get_db)):
    # Registra si el usuario dio Like o Pass. Si es like mutuo se crea un Match automaticamente.
    return create_interaction(db, data)

@router.get("/feed/{user_id}", response_model=dict, summary="Get User Feed")
def get_feed(user_id: int, db: Session = Depends(get_db)):
    # Obtiene sugerencias de perfiles para el feed que el usuario no ha visto aun.
    from services.match_service import get_user_feed
    return get_user_feed(db, current_user_id=user_id)

@router.get("/matches/{user_id}", response_model=dict, summary="Get User Matches")
def get_matches(user_id: int, db: Session = Depends(get_db)):
    # Devuelve la lista de matches exitosos del usuario junto con las salas de chat.
    from services.match_service import get_user_matches
    return get_user_matches(db, user_id=user_id)

@router.post("/matches/{match_id}/finish", summary="Finish a match and grant points")
def finish_match(match_id: int, db: Session = Depends(get_db)):
    # Finaliza el match con otro usuario, sumando puntos de nivel a ambos
    from services.match_service import finish_match_session
    return finish_match_session(db, match_id)
