from sqlalchemy import Column, Integer, String
from core.database import Base

# Tabla que representa un plan de suscripcion que define los limites del usuario.
class Plan(Base):
    __tablename__ = 'plans'
    
    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    max_matches_perday = Column(Integer)
