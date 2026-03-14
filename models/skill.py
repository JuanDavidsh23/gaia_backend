from sqlalchemy import Column, Integer, String
from core.database import Base

# Tabla que representa una habilidad que los usuarios pueden aprender o enseñar.
class Skill(Base):
    __tablename__ = 'skills'
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True)
