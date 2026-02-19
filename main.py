from fastapi import FastAPI
from database import Base, engine
from models.user import User
from models.role import Role
from routes.auth import router as auth_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
