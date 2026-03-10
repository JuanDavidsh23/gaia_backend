from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# salas de chat
rooms = {}

@router.websocket("/ws/chat/{conversation_id}")
async def chat(websocket: WebSocket, conversation_id: int):

    await websocket.accept()

    if conversation_id not in rooms:
        rooms[conversation_id] = []

    rooms[conversation_id].append(websocket)

    print("Usuario conectado a conversación", conversation_id)

    try:
        while True:

            data = await websocket.receive_json()

            # enviar mensaje solo a los de esta conversación
            for connection in rooms[conversation_id]:
                await connection.send_json(data)

    except WebSocketDisconnect:

        rooms[conversation_id].remove(websocket)

        print("Usuario desconectado")