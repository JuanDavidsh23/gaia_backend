from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.message import Message

router = APIRouter()

# salas de chat
rooms = {}

# ---------- DEPENDENCIA DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- HISTORIAL DE MENSAJES ----------
@router.get("/messages/{room_id}", summary="Get Chat Room Messages")
def get_messages(room_id: int, db: Session = Depends(get_db)):
    # Devuelve el historial de mensajes de la sala antes de conectar el WebSocket
    messages = db.query(Message).filter(
        Message.room_id == room_id
    ).order_by(Message.datetime_created_at.asc()).all()
    
    return {
        "messages": [
            {
                "message_id": msg.message_id,
                "user_id": msg.sender_id,
                "message": msg.message,
                "created_at": str(msg.datetime_created_at)
            }
            for msg in messages
        ]
    }

# ---------- WEBSOCKET CHAT ----------
@router.websocket("/ws/chat/{conversation_id}")
async def chat(websocket: WebSocket, conversation_id: int):
    # Endpoint de WebSocket para unirse a la sala, recibir, guardar y transmitir mensajes
    await websocket.accept()

    if conversation_id not in rooms:
        rooms[conversation_id] = []

    rooms[conversation_id].append(websocket)

    print("Usuario conectado a conversación", conversation_id)

    try:
        while True:

            data = await websocket.receive_json()

            # GUARDAR el mensaje en la Base de Datos
            db = SessionLocal()
            try:
                new_message = Message(
                    room_id=conversation_id,
                    sender_id=data.get("user_id"),
                    message=data.get("message")
                )
                db.add(new_message)
                db.commit()
                
                # Añadir el ID y timestamp al mensaje para el Frontend
                data["message_id"] = new_message.message_id
                data["created_at"] = str(new_message.datetime_created_at)
            finally:
                db.close()

            # enviar mensaje solo a los de esta conversación
            for connection in rooms[conversation_id]:
                await connection.send_json(data)

    except WebSocketDisconnect:

        rooms[conversation_id].remove(websocket)

        print("Usuario desconectado")