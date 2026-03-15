"""
Modulo de seguridad.

Proporciona funciones de utilidad para el hashing de contraseñas, la verificacion de contraseñas,
la generacion de tokens de acceso JWT y la dependencia get_current_user para proteger endpoints.
"""

import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Hashea la contraseña del usuario
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

# Verifica la contraseña del usuario
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

# Genera un token JWT para el usuario
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = None):
    """
    Dependencia reutilizable para proteger endpoints.
    Decodifica el JWT del header 'Authorization: Bearer <token>'
    y retorna el usuario autenticado desde la base de datos.
    """
    from core.database import SessionLocal
    from models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Abrir sesión de BD para buscar el usuario
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
    finally:
        db.close()

    if user is None:
        raise credentials_exception

    return user