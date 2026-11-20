import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.config import SESSION_HOURS
from app.db import get_db

# PBKDF2-HMAC-SHA256: no almacena contraseñas en texto plano.
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    return "pbkdf2_sha256$600000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt64, hash64 = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), base64.b64decode(salt64), int(rounds))
        return hmac.compare_digest(digest, base64.b64decode(hash64))
    except (ValueError, TypeError):
        return False

def create_session(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.add(models.Sesion(token_hash=hashlib.sha256(token.encode()).hexdigest(), usuario_id=user_id,
                           expira_en=datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)))
    db.commit()
    return token

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> models.Usuario:
    token = (authorization or "").removeprefix("Bearer ").strip()
    if not token or token == authorization:
        raise HTTPException(401, "Debes iniciar sesión")
    session = db.get(models.Sesion, hashlib.sha256(token.encode()).hexdigest())
    if not session or session.expira_en < datetime.now(timezone.utc):
        raise HTTPException(401, "Sesión inválida o expirada")
    user = db.get(models.Usuario, session.usuario_id)
    if not user or not user.activo:
        raise HTTPException(401, "Cuenta inactiva")
    return user

def user_roles(db: Session, user_id: int) -> set[str]:
    return set(db.scalars(select(models.UsuarioRol.rol).where(models.UsuarioRol.usuario_id == user_id)).all())

def require_role(db: Session, user: models.Usuario, *accepted: str) -> None:
    if not user_roles(db, user.id).intersection(accepted):
        raise HTTPException(403, "No tienes permisos para esta función")
