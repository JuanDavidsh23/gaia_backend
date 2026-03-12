from sqlalchemy import Column, Integer, String
from core.database import Base

class Skill(Base):
    __tablename__ = 'skills'
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True)
