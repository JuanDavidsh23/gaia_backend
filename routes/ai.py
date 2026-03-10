from fastapi import APIRouter
from pydantic import BaseModel
from services.ai_service import ask_ai

router = APIRouter()

class AIRequest(BaseModel):
    message: str

@router.post("/ai")
def ai_chat(request: AIRequest):

    answer = ask_ai(request.message)

    return {"response": answer}