from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.database import Base

# Tabla que representa un mensaje enviado entre dos usuarios en una sala de chat.
class Message(Base):
    __tablename__ = 'messages'
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.room_id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    message = Column(Text, nullable=False)
    datetime_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    room = relationship("ChatRoom")
    sender = relationship("User")
