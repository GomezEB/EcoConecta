from pathlib import Path
from decimal import Decimal
import sys
import pytest
from fastapi import HTTPException
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.workflows import calculate_points, can_transition, move_state

@pytest.mark.parametrize("a,b", [("recibida", "en_revision"), ("recibida", "asignada"),
                                  ("en_revision", "asignada"), ("asignada", "programada"),
                                  ("programada", "recolectada")])
def test_transiciones_permitidas(a, b):
    assert can_transition(a, b)

@pytest.mark.parametrize("a,b", [("recibida", "recolectada"), ("recolectada", "programada"), ("programada", "asignada")])
def test_transiciones_prohibidas(a, b):
    with pytest.raises(HTTPException):
        move_state(a, b)

@pytest.mark.parametrize("weight,rate,expected", [
    ("2.00", 5, 10),
    ("1.50", 2, 3),
    ("0.90", 2, 1),
    ("0.25", 2, 0),
])
def test_puntos_proporcionales_al_peso(weight, rate, expected):
    assert calculate_points(Decimal(weight), rate) == expected
