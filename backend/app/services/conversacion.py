"""Diálogo WhatsApp guiado; la IA es apoyo y no asigna personas u horarios."""
import json
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.config import PILOTO_ABIERTO
from app.services.intenciones import is_acknowledgement, is_greeting, is_request, normalize

STEPS = ["nombre", "direccion", "tipo_generador", "flujo", "preferencia_horaria", "observaciones", "consentimiento"]

PROMPTS = {
    "nombre": "¿Cómo te llamas?",
    "direccion": "¿En qué dirección de Villas de San Pablo recogemos el material? Puedes indicar sector, manzana y casa o local.",
    "tipo_generador": "¿La recolección sería en un hogar o en un negocio?",
    "flujo": "¿Qué material necesitas entregar: residuos orgánicos (por ejemplo, restos de comida) o reciclables?",
    "preferencia_horaria": "¿Qué día o franja horaria te viene mejor? El equipo te confirmará la hora.",
    "observaciones": "¿Hay algún detalle que ayude a encontrar el lugar o identificar el material? Si no, responde «ninguna».",
    "consentimiento": "¿Me autorizas a usar estos datos únicamente para organizar la recolección? Responde SÍ o NO.",
}


def process_text(db: Session, phone: str, message: str) -> str:
    """Una conversación por número, simple y auditable para un MVP."""
    text = (message or "").strip()
    if not text:
        return "No alcancé a leer tu mensaje. ¿Me lo envías otra vez? También puedes mandarme una nota de voz."
    low = normalize(text)
    if low in {"cancelar", "salir", "reiniciar"}:
        state = db.get(models.Conversacion, phone)
        if state:
            db.delete(state)
            db.commit()
        return "Listo, dejamos esta solicitud sin continuar. Cuando quieras volver a empezar, cuéntame qué necesitas o escribe AYUDA. 🌿"
    if low in {"menu", "menú", "inicio", "ayuda"}:
        return ("¡Hola! 😊 Te ayudo a pedir una recolección, consultar una solicitud o revisar tus puntos. "
                "Cuéntame qué necesitas; también puedes escribir EDUCACIÓN para recibir consejos.")
    if low in {"educacion", "reciclar"}:
        return ("Para separar: deja los restos de frutas y verduras aparte; entrega el cartón seco "
                "y los envases limpios, sin mezclarlos con residuos húmedos. Si quieres que pasemos "
                "a recogerlos, cuéntame y lo organizamos. 🌱")
    if low.startswith("estado ") and low[7:].strip().isdigit():
        request_id = int(low[7:].strip())
        req = db.get(models.Solicitud, request_id)
        citizen = db.get(models.Ciudadano, req.ciudadano_id) if req else None
        if not req or not citizen or citizen.telefono != phone:
            return "No encontré una solicitud tuya con ese número."
        when = req.programada_para.strftime("%Y-%m-%d %H:%M UTC") if req.programada_para else "sin fecha confirmada"
        if req.programada_para:
            return f"Tu solicitud #{req.id} está {req.estado.replace('_', ' ')}. La fecha acordada es {when}."
        return f"Tu solicitud #{req.id} está {req.estado.replace('_', ' ')}. El equipo aún no confirma una fecha."
    if low == "puntos":
        citizen = db.scalar(select(models.Ciudadano).where(models.Ciudadano.telefono == phone))
        if not citizen:
            return "Aún no tienes solicitudes registradas. Envía SOLICITUD para empezar."
        from sqlalchemy import func
        total = db.scalar(select(func.coalesce(func.sum(models.MovimientoPuntos.puntos), 0)).where(models.MovimientoPuntos.ciudadano_id == citizen.id))
        return f"Tienes {total} puntos de participación registrados. La regla de puntos del piloto es provisional."

    state = db.get(models.Conversacion, phone)
    if state and not is_request(text) and (is_greeting(text) or is_acknowledgement(text)):
        prefix = "¡Hola! 😊 " if is_greeting(text) else "¡Con gusto! 😊 "
        return prefix + PROMPTS.get(state.paso, "¿En qué puedo ayudarte?")
    if is_request(text) and not state:
        state = models.Conversacion(telefono=phone, paso="nombre", datos_json="{}")
        db.add(state)
        db.commit()
        return "¡Claro! Te ayudo a coordinarlo. 😊 ¿Cómo te llamas?"
    if is_greeting(text):
        return "¡Hola! 😊 Cuéntame qué necesitas y lo vemos. Puedo ayudarte con una recolección, el estado de una solicitud o tus puntos."
    if not state:
        return "Cuéntame si necesitas una recolección, consultar una solicitud o conocer cómo separar tus residuos. Estoy aquí para ayudarte. ♻️"

    data = json.loads(state.datos_json)
    step = state.paso
    if step == "nombre":
        if len(text) < 3 or len(text) > 150:
            return "Indícame tu nombre completo (mínimo 3 letras)."
        data[step] = text
        next_step, reply = "direccion", f"Gracias, {text}. ¿En qué dirección de Villas de San Pablo recogemos el material? Puedes indicar sector, manzana y casa o local."
    elif step == "direccion":
        if len(text) < 6 or len(text) > 300:
            return "Escribe una dirección de al menos 6 caracteres."
        data[step] = text
        next_step, reply = "tipo_generador", "Perfecto. ¿La recolección sería en un hogar o en un negocio?"
    elif step == "tipo_generador":
        hogar = bool(re.search(r"\b(hogar|casa)\b", low))
        negocio = bool(re.search(r"\b(negocio|unidad productiva|comercio)\b", low))
        if hogar == negocio:
            return "¿Me confirmas si es un hogar o un negocio? Así dirigimos tu solicitud al equipo adecuado."
        data[step] = "hogar" if hogar else "unidad_productiva"
        suggestion = data.get("sugerencia_foto")
        material_hint = f" En la foto parece que podrían ser {suggestion}; tú me confirmas." if suggestion else " Si quieres, puedes mandar una foto."
        next_step, reply = "flujo", ("¿Qué material necesitas entregar: residuos orgánicos (por ejemplo, restos de comida) "
                                     f"o reciclables?{material_hint}")
    elif step == "flujo":
        organicos = "organico" in low
        reciclables = "reciclable" in low or "aprovechable" in low
        if organicos == reciclables:
            return "¿Son principalmente orgánicos (restos de comida) o reciclables (cartón, vidrio o envases)?"
        data[step] = "organicos" if organicos else "reciclables"
        next_step, reply = "preferencia_horaria", "Gracias. ¿Qué día o franja horaria te viene mejor? El equipo te confirmará la hora."
    elif step == "preferencia_horaria":
        data[step] = text[:150]
        next_step, reply = "observaciones", "Anotado. ¿Hay algún detalle que ayude a encontrar el lugar o identificar el material? Si no, responde «ninguna»."
    elif step == "observaciones":
        data[step] = "" if low in {"ninguna", "no"} else text[:2000]
        next_step, reply = "consentimiento", ("Para gestionar la recolección, ¿AUTORIZAS el tratamiento de tu nombre, teléfono y dirección "
                                              "por EcoConecta y la fundación únicamente para este servicio? Responde SÍ o NO.")
    else:
        affirmative = low in {"si", "s", "acepto", "autorizo", "de acuerdo"} or bool(re.match(r"^(si|acepto|autorizo)(?:\b|[, ])", low))
        negative = low in {"no", "n"} or bool(re.match(r"^no(?:\b|[, ])", low))
        if not affirmative and not negative:
            return "¿Me autorizas a usar estos datos únicamente para organizar la recolección? Responde SÍ o NO."
        if negative:
            db.delete(state)
            db.commit()
            return "Entiendo, no registraremos la solicitud. Si cambias de opinión, aquí estaré para ayudarte."
        citizen = db.scalar(select(models.Ciudadano).where(models.Ciudadano.telefono == phone))
        if citizen is None:
            citizen = models.Ciudadano(telefono=phone, nombre=data["nombre"], direccion=data["direccion"],
                                      tipo_generador=data["tipo_generador"], consentimiento=True,
                                      habilitado_piloto=PILOTO_ABIERTO)
            db.add(citizen)
            db.flush()
        else:
            citizen.nombre = data["nombre"]
            citizen.direccion = data["direccion"]
            citizen.tipo_generador = data["tipo_generador"]
            citizen.consentimiento = True
        if not citizen.habilitado_piloto:
            db.delete(state)
            db.commit()
            return "Gracias por tu autorización. La Fundación aún debe habilitar tu participación en el piloto; te avisaremos cuando esté listo."
        req = models.Solicitud(ciudadano_id=citizen.id, flujo=data["flujo"], direccion=data["direccion"],
                               preferencia_horaria=data["preferencia_horaria"], observaciones=data["observaciones"])
        db.add(req)
        db.flush()
        db.add(models.Evento(solicitud_id=req.id, accion="creada_desde_whatsapp", detalle="Pendiente de revisión humana"))
        db.delete(state)
        db.commit()
        flujo = "orgánicos" if req.flujo == "organicos" else "reciclables"
        return (f"¡Listo, {citizen.nombre}! Registré tu solicitud #{req.id} para recoger residuos {flujo}. ✅ "
                "El equipo coordinador la revisará y te escribiremos para confirmar quién pasará y cuándo. "
                f"Si necesitas consultarla, escribe ESTADO {req.id}.")
    state.paso = next_step
    state.datos_json = json.dumps(data, ensure_ascii=False)
    db.commit()
    return reply
