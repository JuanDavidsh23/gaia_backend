from fastapi import APIRouter
from pydantic import BaseModel
from services.ai_service import ask_ai

router = APIRouter()

# Modelo de solicitud para la ruta de IA
class AIRequest(BaseModel):
    message: str

from fastapi import HTTPException

# Ruta para interactuar con el asistente de IA
@router.post("/ai", summary="Interact with the AI Assistant")
def ai_chat(request: AIRequest):
    try:
        # Envia el mensaje al servicio de IA y devuelve la respuesta generada
        answer = ask_ai(request.message)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))