from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db, SessionLocal
from core.security import SECRET_KEY, ALGORITHM
from models.message import Message
from jose import JWTError, jwt

router = APIRouter()

# Salas activas: { room_id: [websocket, ...] }
rooms: dict[int, list[WebSocket]] = {}


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
async def chat(
    websocket: WebSocket,
    conversation_id: int,
    token: str = Query(...)  # El frontend debe pasar ?token=<jwt>
):
    # Validar el JWT antes de aceptar la conexión
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    # Registrar en la sala
    if conversation_id not in rooms:
        rooms[conversation_id] = []
    rooms[conversation_id].append(websocket)

    print(f"Usuario {user_id} conectado a sala {conversation_id}")

    try:
        while True:
            data = await websocket.receive_json()

            # Forzar que el user_id del mensaje sea el del token (seguridad)
            data["user_id"] = user_id

            # Guardar el mensaje en la Base de Datos
            db = SessionLocal()
            try:
                new_message = Message(
                    room_id=conversation_id,
                    sender_id=user_id,
                    message=data.get("message")
                )
                db.add(new_message)
                db.commit()

                data["message_id"] = new_message.message_id
                data["created_at"] = str(new_message.datetime_created_at)
            finally:
                db.close()

            # Enviar mensaje a todos en esta sala
            for connection in rooms[conversation_id]:
                await connection.send_json(data)

    except WebSocketDisconnect:
        rooms[conversation_id].remove(websocket)

        # Fix memory leak: limpiar la sala si queda vacía
        if not rooms[conversation_id]:
            del rooms[conversation_id]

        print(f"Usuario {user_id} desconectado de sala {conversation_id}")