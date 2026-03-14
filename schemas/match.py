from pydantic import BaseModel
from typing import List, Optional
from models.interaction import ActionEnum

# Esquema para una solicitud de interaccion (swipe).
class InteractionRequest(BaseModel):
    user_from_id: int   # El usuario actual que está haciendo swipe
    user_to_id: int     # El usuario de la tarjeta a la que le dio swipe
    action: ActionEnum  # "like" o "pass"

# Esquema para una habilidad en el feed.
class SkillResponse(BaseModel):
    name: str

# Esquema para un usuario en el feed.
class FeedUserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Habilidades que tiene para enseñar/aprender (opcional para mostrar en tarjeta)
    skills_to_teach: List[str] = []
    skills_to_learn: List[str] = []

# Esquema para la respuesta del feed.
class FeedResponse(BaseModel):
    users: List[FeedUserResponse]
