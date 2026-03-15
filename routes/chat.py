import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, supabase
from core.security import get_current_user
from models.user import User

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/chat/upload", summary="Upload image or audio for chat")
async def upload_chat_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Sube una imagen o audio a Supabase Storage y devuelve la URL pública.
    El frontend luego envía esa URL por WebSocket como mensaje con type image/audio.
    """
    # Validar tipo de archivo
    content_type = file.content_type or ""

    if content_type in ALLOWED_IMAGE_TYPES:
        message_type = "image"
        folder = "chat/images"
    elif content_type in ALLOWED_AUDIO_TYPES:
        message_type = "audio"
        folder = "chat/audio"
    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Solo imágenes (jpg, png, gif, webp) y audios (mp3, ogg, wav, webm)"
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el límite de 10 MB")

    # Nombre único para evitar colisiones
    extension = file.filename.split(".")[-1] if file.filename else "bin"
    file_name = f"{folder}/{current_user.user_id}_{uuid.uuid4().hex}.{extension}"

    # Subir a Supabase Storage
    try:
        res = supabase.storage.from_("chat-media").upload(
            file_name,
            content,
            {"content-type": content_type, "upsert": "false"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {str(e)}")

    # Obtener URL pública
    public_url = supabase.storage.from_("chat-media").get_public_url(file_name)

    return {
        "url": public_url,
        "type": message_type
    }
