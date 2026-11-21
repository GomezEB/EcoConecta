import hashlib
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.schemas import LoginIn
from app.security import create_session, current_user, user_roles, verify_password

router = APIRouter(prefix="/api/auth", tags=["acceso"])

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.Usuario).where(models.Usuario.correo == payload.correo.strip().lower()))
    if not user or not user.activo or not verify_password(payload.contrasena, user.contrasena_hash):
        raise HTTPException(401, "Credenciales incorrectas")
    token = create_session(db, user.id)
    return {"token": token, "tipo": "bearer", "usuario": {"id": user.id, "nombre": user.nombre, "roles": sorted(user_roles(db, user.id))}}

@router.get("/me")
def me(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    return {"id": user.id, "nombre": user.nombre, "correo": user.correo, "roles": sorted(user_roles(db, user.id))}

@router.post("/logout")
def logout(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db),
           authorization: str | None = Header(default=None)):
    """Invalida en PostgreSQL la sesión concreta asociada al token presentado."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.get(models.Sesion, token_hash)
    # current_user ya validó el token; conservar el chequeo defensivo del propietario.
    if not session or session.usuario_id != user.id:
        raise HTTPException(401, "Sesión inválida")
    db.delete(session)
    db.commit()
    return {"ok": True}
