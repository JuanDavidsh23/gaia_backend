from fastapi import FastAPI
from core.database import Base, engine
from models.plan import Plan
from models.skill import Skill
from models.user import User
from models.users_skills import UserSkill
from models.interaction import Interaction
from models.match import Match
from models.chat_room import ChatRoom
from models.message import Message
from routes.auth import router as auth_router
from routes.users import router as users_router
from middlewares.cors import add_cors_middleware
from routes.ai import router as ai_router
from routes.skill import router as skill_router


# importar websocket
from websocket.chat_ws import router as chat_ws_router

app = FastAPI()

# CORS
add_cors_middleware(app)

# crear tablas
Base.metadata.create_all(bind=engine)

# rutas normales
app.include_router(auth_router)
app.include_router(users_router)

# websocket
app.include_router(chat_ws_router)


app.include_router(ai_router)

# onboarding de habilidades
app.include_router(skill_router)