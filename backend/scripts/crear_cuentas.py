"""Ejecutar: docker compose exec api python scripts/crear_cuentas.py"""
from getpass import getpass
from sqlalchemy import select
from app.db import Base, Session, engine
from app import models
from app.security import hash_password

ROLES = {
    "1": ["coordinador_huerta", "huertero"],
    "2": ["coordinador_reciclaje", "reciclador"],
    "3": ["administrador"],
}

def main():
    Base.metadata.create_all(engine)
    print("EcoConecta — Crear cuenta interna (dos encargados + fundación)")
    print("1. Encargado huerta (coordinación + recolección)")
    print("2. Encargado reciclaje (coordinación + recolección)")
    print("3. Fundación (administración y reportes)")
    option = input("Elige 1/2/3: ").strip()
    if option not in ROLES:
        raise SystemExit("Opción no válida")
    name = input("Nombre: ").strip()
    email = input("Correo: ").strip().lower()
    password = getpass("Contraseña (12 o más caracteres): ")
    if len(password) < 12 or not name or "@" not in email:
        raise SystemExit("Datos inválidos o contraseña demasiado corta")
    with Session(engine) as db:
        if db.scalar(select(models.Usuario).where(models.Usuario.correo == email)):
            raise SystemExit("Ese correo ya existe")
        user = models.Usuario(nombre=name, correo=email, contrasena_hash=hash_password(password))
        db.add(user)
        db.flush()
        for role in ROLES[option]:
            db.add(models.UsuarioRol(usuario_id=user.id, rol=role))
        db.commit()
        print(f"Cuenta #{user.id} creada con roles: {', '.join(ROLES[option])}")

if __name__ == "__main__":
    main()
