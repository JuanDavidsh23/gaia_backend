from pydantic import BaseModel
from typing import List

# Esquema para una solicitud de habilidades de usuario.
# NOTA: user_id ya NO se envía — el backend lo extrae del JWT token
class UserSkillsRequest(BaseModel):
    learn_skills: List[str]  # Lista de habilidades que quiere aprender
    teach_skills: List[str]  # Lista de habilidades que quiere enseñar
