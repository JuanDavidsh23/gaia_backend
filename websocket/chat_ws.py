import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db, SessionLocal
from core.security import SECRET_KEY, ALGORITHM
from models.message import Message
from jose import JWTError, jwt

router = APIRouter()

# Salas activas: { room_id: [websocket, ...] }
rooms: dict[int, list[WebSocket]] = {}

# Historial reciente por sala para darle contexto a la IA (últimos 10 mensajes)
room_history: dict[int, list[dict]] = {}


# ---------- HISTORIAL DE MENSAJES ----------
@router.get("/messages/{room_id}", summary="Get Chat Room Messages")
def get_messages(room_id: int, db: Session = Depends(get_db)):
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
    token: str = Query(...)
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

    # Inicializar historial de la sala si no existe
    if conversation_id not in room_history:
        room_history[conversation_id] = []

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

            # Actualizar historial en memoria para la IA
            room_history[conversation_id].append({
                "user_id": user_id,
                "message": data.get("message")
            })
            # Mantener solo los últimos 10 mensajes
            if len(room_history[conversation_id]) > 10:
                room_history[conversation_id].pop(0)

            # Transmitir el mensaje a todos en la sala
            for connection in rooms[conversation_id]:
                await connection.send_json(data)

            # Llamar a la IA en segundo plano (no bloquea el chat)
            asyncio.create_task(
                _ai_moderate(conversation_id, data.get("message"), room_history[conversation_id].copy())
            )

    except WebSocketDisconnect:
        rooms[conversation_id].remove(websocket)

        # Fix memory leak: limpiar la sala si queda vacía
        if not rooms[conversation_id]:
            del rooms[conversation_id]
            room_history.pop(conversation_id, None)

        print(f"Usuario {user_id} desconectado de sala {conversation_id}")


async def _ai_moderate(conversation_id: int, message: str, history: list[dict]):
    """
    Tarea en segundo plano: la IA revisa el mensaje y responde si es necesario.
    Al ser una tarea async separada, no ralentiza el chat.
    """
    try:
        from services.ai_service import moderate_and_comment

        # Llamar a OpenAI en un hilo separado para no bloquear el event loop
        ai_response = await asyncio.to_thread(moderate_and_comment, message, history)

        if ai_response and conversation_id in rooms:
            ai_message = {
                "user_id": 0,            # 0 = identificador del asistente IA
                "username": "Asistente IA 🤖",
                "message": ai_response,
                "message_id": None,
                "is_ai": True,
                "created_at": None
            }
            for connection in rooms[conversation_id]:
                await connection.send_json(ai_message)

    except Exception as e:
        # Si la IA falla (API caída, etc.) el chat sigue funcionando
        print(f"Error en IA moderación: {e}")