from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from core.security import SECRET_KEY, ALGORITHM

router = APIRouter()

# Salas de señalización activas: { room_id: { user_id: WebSocket } }
# Máximo 2 usuarios por sala (llamada 1 a 1)
signal_rooms: dict[int, dict[int, WebSocket]] = {}


@router.websocket("/ws/signal/{room_id}")
async def signaling(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...)
):
    """
    Servidor de señalización WebRTC para llamadas de audio/video.
    
    El frontend intercambia por aquí:
      - offer  / answer  (SDP)
      - candidate         (ICE candidates)
      - hang-up           (colgar)
    
    El backend solo reenvía los mensajes al OTRO usuario en la sala.
    El audio/video viaja directamente entre los navegadores (P2P).
    """

    # 1. Validar JWT antes de aceptar
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    # 2. Verificar que la sala no esté llena (máximo 2 usuarios)
    room = signal_rooms.setdefault(room_id, {})
    if len(room) >= 2 and user_id not in room:
        await websocket.close(code=4002)  # sala llena
        return

    await websocket.accept()
    room[user_id] = websocket

    print(f"Usuario {user_id} conectado a sala de señalización {room_id}")

    try:
        while True:
            data = await websocket.receive_json()

            # Agregar quién envía el mensaje
            data["from_user_id"] = user_id

            # Reenviar el mensaje SOLO al otro usuario en la sala
            for uid, ws in room.items():
                if uid != user_id:
                    await ws.send_json(data)

    except WebSocketDisconnect:
        # Limpiar al usuario de la sala
        room.pop(user_id, None)

        # Notificar al otro usuario que se colgó
        for uid, ws in room.items():
            try:
                await ws.send_json({"type": "hang-up", "from_user_id": user_id})
            except Exception:
                pass

        # Limpiar sala si queda vacía
        if not room:
            del signal_rooms[room_id]

        print(f"Usuario {user_id} desconectado de sala de señalización {room_id}")
