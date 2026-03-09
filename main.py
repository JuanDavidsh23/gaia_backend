from fastapi import FastAPI
from core.database import Base, engine
from models.user import User
from models.role import Role
from routes.auth import router as auth_router
from middlewares.cors import add_cors_middleware

app = FastAPI()

# Configurar CORS desde la carpeta middlewares
add_cors_middleware(app)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
