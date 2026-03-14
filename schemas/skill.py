from pydantic import BaseModel
from typing import List

# Esquema para una solicitud de habilidades de usuario.
class UserSkillsRequest(BaseModel):
    user_id: int
    learn_skills: List[str]  # Lista de habilidades que quiere aprender
    teach_skills: List[str]  # Lista de habilidades que quiere enseñar
