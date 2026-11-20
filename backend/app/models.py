from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

def now():
    return datetime.now(timezone.utc)

class Usuario(Base):
    __tablename__ = "usuarios_internos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    correo: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    contrasena_hash: Mapped[str] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"
    __table_args__ = (UniqueConstraint("usuario_id", "rol"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios_internos.id"))
    rol: Mapped[str] = mapped_column(String(40))

class Sesion(Base):
    __tablename__ = "sesiones"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios_internos.id"))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Ciudadano(Base):
    __tablename__ = "ciudadanos"
    id: Mapped[int] = mapped_column(primary_key=True)
    telefono: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150))
    direccion: Mapped[str] = mapped_column(String(300))
    tipo_generador: Mapped[str] = mapped_column(String(30))  # hogar | unidad_productiva
    consentimiento: Mapped[bool] = mapped_column(Boolean, default=False)
    habilitado_piloto: Mapped[bool] = mapped_column(Boolean, default=False)

class Solicitud(Base):
    __tablename__ = "solicitudes"
    id: Mapped[int] = mapped_column(primary_key=True)
    ciudadano_id: Mapped[int] = mapped_column(ForeignKey("ciudadanos.id"), index=True)
    flujo: Mapped[str] = mapped_column(String(20), index=True)  # organicos | reciclables
    estado: Mapped[str] = mapped_column(String(30), default="recibida", index=True)
    direccion: Mapped[str] = mapped_column(String(300))
    observaciones: Mapped[str] = mapped_column(Text, default="")
    preferencia_horaria: Mapped[str] = mapped_column(String(150), default="")
    coordinador_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios_internos.id"), nullable=True)
    recolector_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios_internos.id"), nullable=True)
    programada_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cantidad_recibida: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(30), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    actualizada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class Evento(Base):
    __tablename__ = "historial_solicitudes"
    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes.id"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios_internos.id"), nullable=True)
    accion: Mapped[str] = mapped_column(String(100))
    detalle: Mapped[str] = mapped_column(Text, default="")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ReglaPuntos(Base):
    __tablename__ = "reglas_puntos"
    id: Mapped[int] = mapped_column(primary_key=True)
    puntos_por_solicitud: Mapped[int] = mapped_column(Integer, default=1)  # Legacy column retained for existing MVP databases.
    puntos_por_kg: Mapped[int] = mapped_column(Integer, default=2)
    activa: Mapped[bool] = mapped_column(Boolean, default=False)
    nombre: Mapped[str] = mapped_column(String(150), default="Regla provisional por validar con FSD")

class MovimientoPuntos(Base):
    __tablename__ = "movimientos_puntos"
    id: Mapped[int] = mapped_column(primary_key=True)
    ciudadano_id: Mapped[int] = mapped_column(ForeignKey("ciudadanos.id"), index=True)
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes.id"), unique=True)
    regla_id: Mapped[int] = mapped_column(ForeignKey("reglas_puntos.id"))
    puntos: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class WhatsappEvento(Base):
    __tablename__ = "whatsapp_eventos"
    id_externo: Mapped[str] = mapped_column(String(255), primary_key=True)
    telefono: Mapped[str] = mapped_column(String(30))
    tipo: Mapped[str] = mapped_column(String(25))
    texto: Mapped[str] = mapped_column(Text, default="")
    media_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Conversacion(Base):
    __tablename__ = "conversaciones_whatsapp"
    telefono: Mapped[str] = mapped_column(String(30), primary_key=True)
    paso: Mapped[str] = mapped_column(String(40))
    datos_json: Mapped[str] = mapped_column(Text, default="{}")
    actualizada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
