from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class LoginIn(BaseModel):
    correo: str
    contrasena: str

class CiudadanoIn(BaseModel):
    telefono: str = Field(min_length=8, max_length=30)
    nombre: str = Field(min_length=2, max_length=150)
    direccion: str = Field(min_length=5, max_length=300)
    tipo_generador: Literal["hogar", "unidad_productiva"]
    consentimiento: bool
    habilitado_piloto: bool = True

class SolicitudIn(BaseModel):
    ciudadano_id: int
    flujo: Literal["organicos", "reciclables"]
    observaciones: str = Field(default="", max_length=2000)
    preferencia_horaria: str = Field(min_length=3, max_length=150)

class AsignacionIn(BaseModel):
    recolector_id: int

class ProgramacionIn(BaseModel):
    fecha_hora: datetime

class RecoleccionIn(BaseModel):
    cantidad_recibida: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    unidad: Literal["kg"] = "kg"

class ReglaPuntosIn(BaseModel):
    puntos_por_kg: int = Field(ge=0, le=10000)
    nombre: str = Field(min_length=3, max_length=150)
