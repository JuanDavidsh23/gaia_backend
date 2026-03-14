"""
Modulo de CORS Middleware.

Maneja la configuracion de Cross-Origin Resource Sharing para la aplicacion FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Agrega el middleware de CORS a la aplicacion FastAPI, Para aceptar peticiones desde diferentes origenes
def add_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, cámbialo por tu dominio
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
