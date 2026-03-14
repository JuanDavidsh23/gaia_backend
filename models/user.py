from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Text, DateTime
from sqlalchemy.orm import relationship 
import enum
from datetime import datetime
from core.database import Base 

# Enumeracion para los diferentes roles que un usuario puede tener dentro de la plataforma.
class UserRole(str, enum.Enum):
    user = 'user'
    admin = 'admin'
    superadmin = 'superadmin'
    teacher = 'teacher'

# Tabla que representa un usuario en el sistema.
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.user)
    plan_id = Column(Integer, ForeignKey("plans.plan_id"))
    is_active = Column(Boolean, default=True)
    bio = Column(Text)
    avatar_url = Column(String(255))
    datetime_created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan")