"""Diálogo WhatsApp guiado; la IA es apoyo y no asigna personas u horarios."""
import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.config import PILOTO_ABIERTO

STEPS = ["nombre", "direccion", "tipo_generador", "flujo", "preferencia_horaria", "observaciones", "consentimiento"]


def process_text(db: Session, phone: str, message: str) -> str:
    """Una conversación por número, simple y auditable para un MVP."""
    text = (message or "").strip()
    if not text:
        return "No pude entender tu mensaje. Puedes enviar texto o nota de voz."
    low = text.lower()
    if low in {"cancelar", "salir", "reiniciar"}:
        state = db.get(models.Conversacion, phone)
        if state:
            db.delete(state)
            db.commit()
        return "Conversación reiniciada. Envía SOLICITUD para empezar o AYUDA para orientarte."
    if low in {"hola", "menu", "menú", "inicio", "ayuda"}:
        return ("¡Hola! Soy EcoConecta ♻️. Envía SOLICITUD para pedir una recolección, "
                "EDUCACIÓN para separar residuos, ESTADO 123 para consultar tu solicitud "
                "o PUNTOS para conocer tu saldo. Puedes enviarme notas de voz.")
    if low in {"educacion", "educación", "reciclar"}:
        return "Separa orgánicos (restos de frutas y verduras) de reciclables (cartón seco, vidrio y envases limpios). ¿Quieres recogerlos? Envía SOLICITUD."
    if low.startswith("estado ") and low[7:].strip().isdigit():
        request_id = int(low[7:].strip())
        req = db.get(models.Solicitud, request_id)
        citizen = db.get(models.Ciudadano, req.ciudadano_id) if req else None
        if not req or not citizen or citizen.telefono != phone:
            return "No encontré una solicitud tuya con ese número."
        when = req.programada_para.strftime("%Y-%m-%d %H:%M UTC") if req.programada_para else "sin fecha confirmada"
        return f"Solicitud #{req.id}: {req.estado}. Programación: {when}."
    if low == "puntos":
        citizen = db.scalar(select(models.Ciudadano).where(models.Ciudadano.telefono == phone))
        if not citizen:
            return "Aún no tienes solicitudes registradas. Envía SOLICITUD para empezar."
        from sqlalchemy import func
        total = db.scalar(select(func.coalesce(func.sum(models.MovimientoPuntos.puntos), 0)).where(models.MovimientoPuntos.ciudadano_id == citizen.id))
        return f"Tienes {total} puntos de participación registrados. La regla de puntos del piloto es provisional."

    state = db.get(models.Conversacion, phone)
    if low in {"solicitud", "recoger", "recolección", "recoleccion"} and not state:
        state = models.Conversacion(telefono=phone, paso="nombre", datos_json="{}")
        db.add(state)
        db.commit()
        return "Vamos a solicitar una recolección. ¿Cuál es tu nombre completo?"
    if not state:
        return "Envía SOLICITUD para iniciar una recolección o AYUDA para conocer las opciones."

    data = json.loads(state.datos_json)
    step = state.paso
    if step == "nombre":
        if len(text) < 3 or len(text) > 150:
            return "Indícame tu nombre completo (mínimo 3 letras)."
        data[step] = text
        next_step, reply = "direccion", "¿Cuál es tu dirección dentro de Villas de San Pablo (sector, manzana, casa o local)?"
    elif step == "direccion":
        if len(text) < 6 or len(text) > 300:
            return "Escribe una dirección de al menos 6 caracteres."
        data[step] = text
        next_step, reply = "tipo_generador", "¿Es un HOGAR o un NEGOCIO?"
    elif step == "tipo_generador":
        if low not in {"hogar", "casa", "negocio", "unidad productiva", "comercio"}:
            return "Responde HOGAR o NEGOCIO."
        data[step] = "hogar" if low in {"hogar", "casa"} else "unidad_productiva"
        next_step, reply = "flujo", "¿El material es ORGÁNICOS o RECICLABLES? Puedes enviar una foto para obtener una sugerencia."
    elif step == "flujo":
        if low not in {"organicos", "orgánicos", "reciclable", "reciclables", "aprovechables"}:
            return "Responde ORGÁNICOS o RECICLABLES. La categoría debe ser confirmada por ti."
        data[step] = "organicos" if low in {"organicos", "orgánicos"} else "reciclables"
        next_step, reply = "preferencia_horaria", "¿Qué día o franja horaria te queda mejor? La confirmará el encargado."
    elif step == "preferencia_horaria":
        data[step] = text[:150]
        next_step, reply = "observaciones", "¿Alguna observación para encontrar el lugar o el material? Responde NINGUNA si no tienes."
    elif step == "observaciones":
        data[step] = "" if low in {"ninguna", "no"} else text[:2000]
        next_step, reply = "consentimiento", ("Para gestionar la recolección, ¿AUTORIZAS el tratamiento de tu nombre, teléfono y dirección "
                                              "por EcoConecta y la fundación con esa finalidad? Responde SI o NO.")
    else:
        if low not in {"si", "sí", "no"}:
            return "Responde SI para aceptar el tratamiento de datos o NO para cancelar."
        if low == "no":
            db.delete(state)
            db.commit()
            return "Sin autorización no guardaremos tu solicitud. Envía SOLICITUD si deseas volver a intentarlo."
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
            return "Tus datos quedaron registrados. Por ahora el piloto requiere habilitación de la Fundación."
        req = models.Solicitud(ciudadano_id=citizen.id, flujo=data["flujo"], direccion=data["direccion"],
                               preferencia_horaria=data["preferencia_horaria"], observaciones=data["observaciones"])
        db.add(req)
        db.flush()
        db.add(models.Evento(solicitud_id=req.id, accion="creada_desde_whatsapp", detalle="Pendiente de revisión humana"))
        db.delete(state)
        db.commit()
        return (f"¡Solicitud #{req.id} registrada! ✅ Flujo: {req.flujo}. "
                "El coordinador revisará y confirmará quién irá y en qué horario. "
                f"Consulta escribiendo ESTADO {req.id}.")
    state.paso = next_step
    state.datos_json = json.dumps(data, ensure_ascii=False)
    db.commit()
    return reply
