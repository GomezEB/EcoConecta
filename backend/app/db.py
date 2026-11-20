from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from app.config import DATABASE_URL

if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError("EcoConecta requiere DATABASE_URL con PostgreSQL + psycopg. Revisar .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as db:
        yield db
