"""
Modulo de configuracion de base de datos.

Configura el motor de SQLAlchemy, la sesión y la base declarativa.
Tambien inicializa el cliente de Supabase si se proporcionan las credenciales.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  
)

# Inicializar Cliente de Supabase (Soporta Auth, Storage, etc.)
from supabase import create_client, Client

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ---------- DEPENDENCIA DB (centralizada) ----------
def get_db():
    """
    Generador de sesión de base de datos para inyección de dependencias en FastAPI.
    Garantiza que la sesión se cierre correctamente aunque ocurra un error.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
