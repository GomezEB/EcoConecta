import re
import unicodedata


REQUEST_HINTS = (
    "nueva solicitud", "crear solicitud", "hacer una solicitud", "recoger", "recojan",
    "recoleccion", "pasen por", "retirar mis residuos",
    "llevarse mis residuos", "reportar residuos", "reportar los residuos", "tengo residuos",
    "buscar mis residuos", "venir por mis residuos", "pasar a recoger", "recoger la basura",
    "solicitar recoleccion",
)
REQUEST_ACTION = re.compile(
    r"\b(recoger|recojan|recoleccion|retirar|pasar|pasen|vengan|reportar|llevarse)\b"
)
COLLECTION_REQUEST = re.compile(
    r"\b(quiero|quisiera|necesito|solicito|solicitar|me gustaria)\b.{0,30}\brecoleccion\b"
)
MATERIAL = re.compile(
    r"\b(residuos?|basura|desechos?|organicos?|reciclables?|carton|envases?|botellas?|"
    r"papel|vidrio|plastico|latas?|hojas|restos)\b"
)
GREETINGS = {
    "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "buen dia",
    "que tal", "como estas", "como va",
}


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip()


def is_request(text: str) -> bool:
    normalized = normalize(text)
    if any(hint in normalized for hint in REQUEST_HINTS):
        return True
    return bool(
        COLLECTION_REQUEST.search(normalized)
        or (REQUEST_ACTION.search(normalized) and MATERIAL.search(normalized))
    )


def is_greeting(text: str) -> bool:
    normalized = normalize(text).strip(" .,!¡¿?")
    return normalized in GREETINGS or any(
        normalized.startswith(greeting + " ") or normalized.startswith(greeting + ",")
        for greeting in GREETINGS
    )


def is_acknowledgement(text: str) -> bool:
    return normalize(text).strip(" .,!¡¿?") in {"gracias", "muchas gracias", "ok", "okay", "vale", "listo"}
