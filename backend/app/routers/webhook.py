import json
import logging
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app import models
from app.config import WHATSAPP_VERIFY_TOKEN
from app.db import get_db
from app.services.whatsapp import valid_signature, send_message, suggest_image_flow, transcribe_audio
from app.services.conversacion import process_text

log = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Cloud API"])

@router.get("")
def verify_webhook(mode: str = Query(default="", alias="hub.mode"),
                   token: str = Query(default="", alias="hub.verify_token"),
                   challenge: str = Query(default="", alias="hub.challenge")):
    if not WHATSAPP_VERIFY_TOKEN or mode != "subscribe" or token != WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(403, "Token de verificación incorrecto")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(challenge)

@router.post("")
async def inbound(request: Request, signature: str | None = Header(default=None, alias="X-Hub-Signature-256"),
                  db: Session = Depends(get_db)):
    body = await request.body()
    if not valid_signature(body, signature):
        raise HTTPException(403, "Firma de Meta inválida")
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Contenido inválido")
    processed = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                phone, event_id, kind = msg.get("from", ""), msg.get("id", ""), msg.get("type", "")
                if not phone or not event_id or db.get(models.WhatsappEvento, event_id):
                    continue
                media_id = msg.get(kind, {}).get("id") if kind in {"audio", "image"} else None
                text = msg.get("text", {}).get("body", "") if kind == "text" else ""
                db.add(models.WhatsappEvento(id_externo=event_id, telefono=phone, tipo=kind, texto="", media_id=media_id))
                db.commit()  # Idempotencia antes de transcribir/contestar.
                answer = ""
                try:
                    if kind == "audio" and media_id:
                        text = await transcribe_audio(media_id) or ""
                        answer = (process_text(db, phone, text) if text else "Recibí tu audio. Aún no puedo transcribirlo: configura la API de IA o responde con texto.")
                    elif kind == "image" and media_id:
                        suggestion = await suggest_image_flow(media_id)
                        state = db.get(models.Conversacion, phone)
                        if not state:
                            answer = process_text(db, phone, "solicitud")
                            if suggestion:
                                state = db.get(models.Conversacion, phone)
                                data = json.loads(state.datos_json)
                                data["sugerencia_foto"] = suggestion
                                state.datos_json = json.dumps(data, ensure_ascii=False)
                                db.commit()
                                answer += " Recibí la foto; más adelante te preguntaré por el tipo de material para que me lo confirmes."
                        elif state.paso == "flujo" and suggestion:
                            answer = f"Gracias por la foto. Parece que podrían ser {suggestion}. ¿Me confirmas si son orgánicos o reciclables?"
                        elif suggestion:
                            answer = f"Gracias por compartir la foto. Parece que podría ser {suggestion}. Sigamos con la información que te pregunté."
                        else:
                            answer = "Gracias por compartir la foto. Sigamos con la información que te pregunté para registrar la solicitud."
                    elif kind == "text":
                        answer = process_text(db, phone, text)
                    else:
                        answer = "Puedes enviarme texto, notas de voz o fotografías. Escribe AYUDA para empezar."
                    event = db.get(models.WhatsappEvento, event_id)
                    event.texto = text[:2500]
                    db.commit()
                except Exception:
                    log.exception("Error procesando mensaje de WhatsApp")
                    answer = "Hubo un problema al procesar tu mensaje. Inténtalo de nuevo en unos minutos."
                if answer:
                    await send_message(phone, answer)
                processed += 1
    return {"ok": True, "mensajes_procesados": processed}
