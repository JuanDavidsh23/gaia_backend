from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.database import Base

# Tabla que representa una sala de chat para un match exitoso entre dos usuarios.
class ChatRoom(Base):
    __tablename__ = 'chat_rooms'
    
    room_id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.match_id'), unique=True, nullable=False)
    datetime_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    match = relationship("Match")
