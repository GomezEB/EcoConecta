from decimal import Decimal
from fastapi import HTTPException

ROLES_COORDINACION = {"organicos": "coordinador_huerta", "reciclables": "coordinador_reciclaje"}
ROLES_RECOLECCION = {"organicos": "huertero", "reciclables": "reciclador"}
ESTADOS = ("recibida", "en_revision", "asignada", "programada", "recolectada", "cancelada", "rechazada")

def calculate_points(weight_kg: Decimal, points_per_kg: int) -> int:
    """Calcula puntos enteros proporcionalmente; las fracciones se redondean hacia abajo."""
    return int(weight_kg * points_per_kg)

def validate_flow(flow: str) -> None:
    if flow not in ROLES_COORDINACION:
        raise HTTPException(422, "El flujo debe ser organicos o reciclables")

def can_transition(actual: str, nuevo: str) -> bool:
    allowed = {
        "recibida": {"en_revision", "asignada", "cancelada"},
        "en_revision": {"asignada", "cancelada", "rechazada"},
        "asignada": {"programada", "cancelada"},
        "programada": {"recolectada", "cancelada"},
        "recolectada": set(), "cancelada": set(), "rechazada": set(),
    }
    return nuevo in allowed.get(actual, set())

def move_state(actual: str, nuevo: str) -> str:
    if not can_transition(actual, nuevo):
        raise HTTPException(409, f"No se puede pasar de {actual} a {nuevo}")
    return nuevo
