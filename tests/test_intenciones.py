from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.intenciones import is_greeting, is_request


@pytest.mark.parametrize("message", [
    "Hola, necesito que pasen por mis botellas, por favor",
    "Quiero reportar residuos orgánicos",
    "¿Pueden recoger el cartón de mi casa?",
    "Necesito una recolección",
])
def test_reconoce_solicitudes_en_lenguaje_natural(message):
    assert is_request(message)


@pytest.mark.parametrize("message", [
    "Hola",
    "Buenas tardes",
    "¡Qué tal!",
])
def test_reconoce_saludos(message):
    assert is_greeting(message)


def test_no_confunde_consulta_de_estado_con_solicitud():
    assert not is_request("¿Cuál es el estado de mi solicitud 24?")
