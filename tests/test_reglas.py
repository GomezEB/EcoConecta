from pathlib import Path
import sys
import pytest
from fastapi import HTTPException
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.workflows import can_transition, move_state

@pytest.mark.parametrize("a,b", [("recibida", "en_revision"), ("recibida", "asignada"),
                                  ("en_revision", "asignada"), ("asignada", "programada"),
                                  ("programada", "recolectada")])
def test_transiciones_permitidas(a, b):
    assert can_transition(a, b)

@pytest.mark.parametrize("a,b", [("recibida", "recolectada"), ("recolectada", "programada"), ("programada", "asignada")])
def test_transiciones_prohibidas(a, b):
    with pytest.raises(HTTPException):
        move_state(a, b)
