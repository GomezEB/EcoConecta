"""Integración exclusiva con WhatsApp Business Cloud API (Meta).

Requiere HTTPS público para webhooks. No utilizar tokens en el frontend.
"""
from __future__ import annotations
import base64
import hmac
import hashlib
import io
import logging
from typing import Any
import httpx
from app.config import (
    WHATSAPP_APP_SECRET, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID,
    META_GRAPH_VERSION, OPENAI_API_KEY,
)

log = logging.getLogger(__name__)


def valid_signature(body: bytes, signature: str | None) -> bool:
    if not WHATSAPP_APP_SECRET or not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(WHATSAPP_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix("sha256="))


def configured() -> bool:
    return bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)


async def send_message(phone: str, message: str) -> bool:
    """Envía texto mediante Cloud API; nunca almacena o muestra el token."""
    if not configured():
        return False
    url = f"https://graph.facebook.com/{META_GRAPH_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp", "to": phone,
        "type": "text", "text": {"body": message[:4096]},
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"})
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        log.exception("No se pudo enviar mensaje de WhatsApp")
        return False


async def download_media(media_id: str, max_bytes: int = 8_000_000) -> tuple[bytes, str]:
    """Descarga contenido desde Meta en memoria. No se publica como archivo estático."""
    if not WHATSAPP_ACCESS_TOKEN:
        raise RuntimeError("Falta configurar WHATSAPP_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=False) as client:
        meta = await client.get(f"https://graph.facebook.com/{META_GRAPH_VERSION}/{media_id}", headers=headers)
        meta.raise_for_status()
        info = meta.json()
        if int(info.get("file_size", 0)) > max_bytes:
            raise ValueError("Archivo excede el tamaño permitido")
        url = info["url"]
        # URL suministrada por Meta. Por seguridad, no seguir redirecciones arbitrarias.
        if not url.startswith("https://") or not (url.split("/", 3)[2].endswith(".facebook.com") or url.split("/", 3)[2].endswith(".fbcdn.net")):
            raise ValueError("Dominio de medio no permitido")
        data = await client.get(url, headers=headers)
        data.raise_for_status()
        if len(data.content) > max_bytes:
            raise ValueError("Archivo demasiado grande")
        return data.content, info.get("mime_type", "application/octet-stream")


async def transcribe_audio(media_id: str) -> str | None:
    """Transcripción opcional mediante un modelo permitido; no enviar identificación personal."""
    if not OPENAI_API_KEY:
        return None
    from openai import AsyncOpenAI
    content, mime = await download_media(media_id)
    suffix = ".ogg" if "ogg" in mime else ".mp3" if "mpeg" in mime else ".m4a"
    fileobj = io.BytesIO(content)
    fileobj.name = "nota_voz" + suffix
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    result = await client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=fileobj)
    return result.text.strip()


async def suggest_image_flow(media_id: str) -> str | None:
    """Clasificación *orientativa*; el usuario la confirma y un humano decide la atención."""
    if not OPENAI_API_KEY:
        return None
    from openai import AsyncOpenAI
    content, mime = await download_media(media_id)
    if mime not in {"image/jpeg", "image/png", "image/webp"}:
        return None
    encoded = base64.b64encode(content).decode("ascii")
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    res = await client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "Observa únicamente el residuo, no a las personas. Responde con UNA palabra: organicos, reciclables o incierto. No inventes una clasificación si hay duda."},
            {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"},
        ]}], max_output_tokens=20,
    )
    val = res.output_text.strip().lower()
    return val if val in {"organicos", "reciclables"} else None
