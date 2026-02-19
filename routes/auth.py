from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from models.role import Role 
from schemas.user import UserCreate, UserLogin
from utils.security import hash_password, verify_password, create_access_token

router = APIRouter()

# ---------- DEPENDENCIA DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ---------- REGISTER ----------
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    role = db.query(Role).filter(Role.name == "tourist").first()

    if not role:
        raise HTTPException(status_code=400, detail="Rol no encontrado")

    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        hashed_password=hash_password(user.password),
        phone=user.phone,
        id_role=role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuario creado correctamente."}

# ---------- LOGIN ----------
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    token = create_access_token({"user_id": db_user.id})

    return {"access_token": token, "token_type": "bearer"}
