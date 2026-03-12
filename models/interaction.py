from sqlalchemy import Column, Integer, ForeignKey, Enum, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from core.database import Base

class ActionEnum(str, enum.Enum):
    like = 'like'
    pass_ = 'pass'  # Usamos pass_ porque 'pass' es palabra reservada en Python

class Interaction(Base):
    __tablename__ = 'interactions'
    
    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_from_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    user_to_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    actions = Column(Enum(ActionEnum), nullable=False)
    datetime_created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_from_id', 'user_to_id', name='uq_interaction_users'),
    )

    user_from = relationship("User", foreign_keys=[user_from_id])
    user_to = relationship("User", foreign_keys=[user_to_id])
