"""Poblacion idempotente de datos FICTICIOS, solo en entornos demo.

Desde contenedor: python -m scripts.seed_demo
Requiere DEMO_SEED_ENABLED=true y tres variables DEMO_*_PASSWORD (>=12 caracteres).
No cambia contrasenas de usuarios preexistentes ni borra registros.
"""
from __future__ import annotations
import os
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.db import Base, engine
from app import models
from app.security import hash_password

ACCOUNTS = (
    ("DEMO_ADMIN", "Fundacion EcoConecta (demo)", "fundacion.demo@ecoconecta.invalid", ("administrador",)),
    ("DEMO_HUERTA", "Encargado huerta (demo)", "huerta.demo@ecoconecta.invalid", ("coordinador_huerta", "huertero")),
    ("DEMO_RECICLAJE", "Encargado reciclaje (demo)", "reciclaje.demo@ecoconecta.invalid", ("coordinador_reciclaje", "reciclador")),
)
CITIZENS = (
    ("DEMO-ORG-001", "Unidad productiva demostracion", "Villas de San Pablo - Local ficticio 1", "unidad_productiva", "organicos"),
    ("DEMO-REC-002", "Hogar demostracion", "Villas de San Pablo - Casa ficticia 2", "hogar", "reciclables"),
)

def seed() -> None:
    if os.getenv("DEMO_SEED_ENABLED", "").lower() != "true":
        raise SystemExit("Seed deshabilitado. Establecer DEMO_SEED_ENABLED=true SOLO para el entorno demo")
    passwords = {}
    for prefix, _, _, _ in ACCOUNTS:
        password = os.getenv(prefix + "_PASSWORD", "")
        if len(password) < 12:
            raise SystemExit(f"Falta {prefix}_PASSWORD (12+ caracteres); no se guardaron cambios")
        passwords[prefix] = password
    # No alterar cuentas existentes: entorno demo separado del real.
    with engine.begin() as con:
        Base.metadata.create_all(con)
        # Compatible con instalaciones MVP previas sin esta columna.
        con.execute(text("ALTER TABLE reglas_puntos ADD COLUMN IF NOT EXISTS puntos_por_kg INTEGER NOT NULL DEFAULT 2"))
    with Session(engine) as db:
        for prefix, name, email, roles in ACCOUNTS:
            user = db.scalar(select(models.Usuario).where(models.Usuario.correo == email))
            if user is None:
                user = models.Usuario(nombre=name, correo=email, contrasena_hash=hash_password(passwords[prefix]))
                db.add(user)
                db.flush()
                print(f"Usuario demo creado: {email}")
            for role in roles:
                existing = db.scalar(select(models.UsuarioRol).where(models.UsuarioRol.usuario_id == user.id, models.UsuarioRol.rol == role))
                if existing is None:
                    db.add(models.UsuarioRol(usuario_id=user.id, rol=role))
        for phone, name, address, kind, flow in CITIZENS:
            citizen = db.scalar(select(models.Ciudadano).where(models.Ciudadano.telefono == phone))
            if citizen is None:
                citizen = models.Ciudadano(telefono=phone, nombre=name, direccion=address,
                                           tipo_generador=kind, consentimiento=True, habilitado_piloto=True)
                db.add(citizen)
                db.flush()
            # Solo sembrar una solicitud demo si todavia no tiene solicitudes.
            has_request = db.scalar(select(models.Solicitud.id).where(models.Solicitud.ciudadano_id == citizen.id).limit(1))
            if has_request is None:
                request = models.Solicitud(ciudadano_id=citizen.id, flujo=flow, direccion=address,
                                           observaciones="DATOS FICTICIOS PARA DEMOSTRACION",
                                           preferencia_horaria="Jornada siguiente; coordinar con el encargado")
                db.add(request)
                db.flush()
                db.add(models.Evento(solicitud_id=request.id, accion="seed_demo", detalle="Solicitud ficticia de evaluacion"))
                print(f"Solicitud {flow} creada: #{request.id}")
        active_rule = db.scalar(select(models.ReglaPuntos).where(models.ReglaPuntos.activa.is_(True)).limit(1))
        if active_rule is None:
            db.add(models.ReglaPuntos(puntos_por_kg=2, nombre="Demo 2 puntos/kg NO OFICIAL", activa=True))
        db.commit()
    print("Seed concluido. No imprimir contrasenas ni tokens en los logs.")

if __name__ == "__main__":
    seed()
