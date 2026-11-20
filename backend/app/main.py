from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app import models  # importa tablas para create_all
from app.config import CORS_ORIGINS
from app.db import Base, engine
from app.routers import auth, operacion, reportes, webhook

@asynccontextmanager
async def lifespan(app: FastAPI):
    # MVP inicial: crear tablas vacías. No sustituye migraciones versionadas en producción.
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(text(
            "ALTER TABLE reglas_puntos ADD COLUMN IF NOT EXISTS "
            "puntos_por_kg INTEGER NOT NULL DEFAULT 2"
        ))
    yield

app = FastAPI(title="EcoConecta API — MVP oficial", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(operacion.router)
app.include_router(reportes.router)
app.include_router(webhook.router)

@app.get("/api/salud")
def health():
    return {"estado": "ok", "proyecto": "EcoConecta"}

@app.get("/api/educacion")
def educacion():
    return {"consejos": [
        {"titulo": "Orgánicos", "detalle": "Separa restos de frutas y verduras. Evita mezclarlos con plásticos o vidrio."},
        {"titulo": "Reciclables", "detalle": "Entrega cartón seco y envases limpios, separados de residuos húmedos."},
        {"titulo": "Programación", "detalle": "Los horarios se acuerdan con el coordinador; no se asignan automáticamente mediante IA."},
    ]}
