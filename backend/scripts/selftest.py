"""Verificacion de solo lectura de reglas, esquema y usuarios DEMO.
Ejecutar: docker compose exec -e PYTHONPATH=/app api python -m scripts.selftest
"""
from decimal import Decimal
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.db import engine
from app import models
from app.workflows import calculate_points, can_transition

checks = [
    ("recibida -> en_revision", can_transition("recibida", "en_revision")),
    ("asignada -> programada", can_transition("asignada", "programada")),
    ("programada -> recolectada", can_transition("programada", "recolectada")),
    ("no recoleccion directa", not can_transition("recibida", "recolectada")),
    ("no retroceso de recoleccion", not can_transition("recolectada", "programada")),
    ("puntos: 3 kg x 2", calculate_points(Decimal("3"), 2) == 6),
    ("puntos: 0.9 kg x 2", calculate_points(Decimal("0.9"), 2) == 1),
]
with Session(engine) as db:
    checks.append(("conexion PostgreSQL", db.scalar(text("select 1")) == 1))
    checks.append(("tres perfiles internos disponibles", all(db.scalar(select(models.UsuarioRol.id).where(models.UsuarioRol.rol == r).limit(1)) for r in ("administrador", "huertero", "reciclador"))))
    for flow, role in (("organicos", "coordinador_huerta"), ("reciclables", "coordinador_reciclaje")):
        checks.append((f"rol para {flow}", bool(db.scalar(select(models.UsuarioRol.id).where(models.UsuarioRol.rol == role).limit(1)))))
for label, ok in checks:
    print(("OK " if ok else "FALLO ") + label)
if not all(ok for _, ok in checks):
    raise SystemExit(1)
print("Verificacion completada sin modificar la base de datos")
