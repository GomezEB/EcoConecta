from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.schemas import CiudadanoIn, SolicitudIn, AsignacionIn, ProgramacionIn, RecoleccionIn, ReglaPuntosIn
from app.security import current_user, require_role, user_roles
from app.workflows import ROLES_COORDINACION, ROLES_RECOLECCION, move_state
from app.services.whatsapp import send_message

router = APIRouter(prefix="/api", tags=["operación"])


def _has_access(db: Session, user: models.Usuario, req: models.Solicitud) -> bool:
    roles = user_roles(db, user.id)
    return "administrador" in roles or ROLES_COORDINACION[req.flujo] in roles or (req.recolector_id == user.id and ROLES_RECOLECCION[req.flujo] in roles)


def _get_accessible(db: Session, user: models.Usuario, request_id: int) -> models.Solicitud:
    req = db.get(models.Solicitud, request_id)
    if not req or not _has_access(db, user, req):
        raise HTTPException(404, "Solicitud no encontrada")
    return req


def _serialize(db: Session, req: models.Solicitud, show_contact: bool = True) -> dict:
    citizen = db.get(models.Ciudadano, req.ciudadano_id)
    return {
        "id": req.id, "flujo": req.flujo, "estado": req.estado,
        "nombre": citizen.nombre if show_contact and citizen else None,
        "telefono": citizen.telefono if show_contact and citizen else None,
        "direccion": req.direccion if show_contact else None,
        "observaciones": req.observaciones,
        "tipo_generador": citizen.tipo_generador if citizen else None,
        "preferencia_horaria": req.preferencia_horaria,
        "coordinador_id": req.coordinador_id, "recolector_id": req.recolector_id,
        "programada_para": req.programada_para,
        "cantidad_recibida": req.cantidad_recibida, "unidad": req.unidad,
        "creada_en": req.creada_en,
    }


@router.get("/personal")
def personal(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "coordinador_huerta", "coordinador_reciclaje", "administrador")
    my_roles = user_roles(db, user.id)
    people = db.scalars(select(models.Usuario).where(models.Usuario.activo.is_(True)).order_by(models.Usuario.nombre)).all()
    result = []
    for person in people:
        roles = user_roles(db, person.id)
        if "administrador" in my_roles or ("coordinador_huerta" in my_roles and "huertero" in roles) or ("coordinador_reciclaje" in my_roles and "reciclador" in roles):
            result.append({"id": person.id, "nombre": person.nombre, "roles": sorted(roles)})
    return result


@router.post("/ciudadanos")
def crear_ciudadano(payload: CiudadanoIn, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")
    if not payload.consentimiento:
        raise HTTPException(422, "Se requiere consentimiento para tratar datos")
    citizen = db.scalar(select(models.Ciudadano).where(models.Ciudadano.telefono == payload.telefono))
    if citizen:
        raise HTTPException(409, "Teléfono ya registrado")
    citizen = models.Ciudadano(**payload.model_dump())
    db.add(citizen)
    db.commit()
    db.refresh(citizen)
    return {"id": citizen.id, "nombre": citizen.nombre, "habilitado_piloto": citizen.habilitado_piloto}


@router.get("/ciudadanos")
def ciudadanos(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")
    return [{"id": c.id, "nombre": c.nombre, "tipo_generador": c.tipo_generador, "habilitado_piloto": c.habilitado_piloto} for c in db.scalars(select(models.Ciudadano).order_by(models.Ciudadano.id.desc()).limit(100)).all()]


@router.post("/solicitudes")
def crear_solicitud(payload: SolicitudIn, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")  # Ruta demo/administrativa; ciudadano usa WhatsApp.
    citizen = db.get(models.Ciudadano, payload.ciudadano_id)
    if not citizen or not citizen.consentimiento or not citizen.habilitado_piloto:
        raise HTTPException(422, "Ciudadano no habilitado o sin consentimiento")
    req = models.Solicitud(ciudadano_id=citizen.id, flujo=payload.flujo,
                           direccion=citizen.direccion, observaciones=payload.observaciones,
                           preferencia_horaria=payload.preferencia_horaria)
    db.add(req)
    db.flush()
    db.add(models.Evento(solicitud_id=req.id, actor_id=user.id, accion="creada_por_administrador"))
    db.commit()
    return {"id": req.id, "estado": req.estado, "flujo": req.flujo}


@router.get("/solicitudes")
def solicitudes(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    roles = user_roles(db, user.id)
    stmt = select(models.Solicitud).order_by(models.Solicitud.id.desc()).limit(150)
    # Filtrado antes de construir la respuesta, para no exponer datos de otros colectivos.
    if "administrador" not in roles:
        allowed_flows = [flow for flow, role in ROLES_COORDINACION.items() if role in roles]
        if allowed_flows:
            stmt = stmt.where(models.Solicitud.flujo.in_(allowed_flows))
        else:
            stmt = stmt.where(models.Solicitud.recolector_id == user.id)
    return [_serialize(db, req) for req in db.scalars(stmt).all() if _has_access(db, user, req)]


@router.get("/solicitudes/{request_id}")
def detalle(request_id: int, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    req = _get_accessible(db, user, request_id)
    history = db.scalars(select(models.Evento).where(models.Evento.solicitud_id == req.id).order_by(models.Evento.fecha)).all()
    return {**_serialize(db, req), "historial": [{"accion": e.accion, "fecha": e.fecha, "detalle": e.detalle} for e in history]}


@router.post("/solicitudes/{request_id}/revisar")
def revisar(request_id: int, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    req = _get_accessible(db, user, request_id)
    require_role(db, user, ROLES_COORDINACION[req.flujo], "administrador")
    req.estado = move_state(req.estado, "en_revision")
    req.coordinador_id = user.id
    db.add(models.Evento(solicitud_id=req.id, actor_id=user.id, accion="en_revision"))
    db.commit()
    return {"id": req.id, "estado": req.estado}


@router.post("/solicitudes/{request_id}/asignar")
def asignar(request_id: int, payload: AsignacionIn, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    req = _get_accessible(db, user, request_id)
    require_role(db, user, ROLES_COORDINACION[req.flujo], "administrador")
    collector = db.get(models.Usuario, payload.recolector_id)
    if not collector or not collector.activo or ROLES_RECOLECCION[req.flujo] not in user_roles(db, collector.id):
        raise HTTPException(422, "El encargado no pertenece al colectivo correspondiente")
    req.estado = move_state(req.estado, "asignada")
    req.coordinador_id = req.coordinador_id or user.id
    req.recolector_id = collector.id
    db.add(models.Evento(solicitud_id=req.id, actor_id=user.id, accion="asignada", detalle=f"Recolector interno #{collector.id}"))
    db.commit()
    return {"id": req.id, "estado": req.estado, "recolector_id": req.recolector_id}


@router.post("/solicitudes/{request_id}/programar")
async def programar(request_id: int, payload: ProgramacionIn, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    req = _get_accessible(db, user, request_id)
    require_role(db, user, ROLES_COORDINACION[req.flujo], "administrador")
    if not req.coordinador_id or not req.recolector_id:
        raise HTTPException(409, "Falta asignación de coordinador y recolector")
    if payload.fecha_hora.tzinfo is None or payload.fecha_hora <= datetime.now(timezone.utc):
        raise HTTPException(422, "La fecha debe indicar zona horaria y ser futura")
    req.estado = move_state(req.estado, "programada")
    req.programada_para = payload.fecha_hora
    collector = db.get(models.Usuario, req.recolector_id)
    citizen = db.get(models.Ciudadano, req.ciudadano_id)
    db.add(models.Evento(solicitud_id=req.id, actor_id=user.id, accion="programada", detalle=payload.fecha_hora.isoformat()))
    db.commit()
    date_local = payload.fecha_hora.astimezone(__import__("zoneinfo").ZoneInfo("America/Bogota")).strftime("%d/%m/%Y %I:%M %p")
    sent = await send_message(citizen.telefono, f"EcoConecta: tu solicitud #{req.id} quedó programada para {date_local}. Encargado: {collector.nombre}.")
    return {"id": req.id, "estado": req.estado, "whatsapp_notificado": sent}


@router.post("/solicitudes/{request_id}/recolectar")
async def recolectar(request_id: int, payload: RecoleccionIn, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    req = _get_accessible(db, user, request_id)
    if req.recolector_id != user.id or ROLES_RECOLECCION[req.flujo] not in user_roles(db, user.id):
        raise HTTPException(403, "Solo el encargado asignado puede registrar esta recolección")
    req.estado = move_state(req.estado, "recolectada")
    req.cantidad_recibida, req.unidad = payload.cantidad_recibida, payload.unidad
    db.add(models.Evento(solicitud_id=req.id, actor_id=user.id, accion="recolectada", detalle=f"{payload.cantidad_recibida} {payload.unidad}"))
    active_rule = db.scalar(select(models.ReglaPuntos).where(models.ReglaPuntos.activa.is_(True)).order_by(models.ReglaPuntos.id.desc()))
    points = 0
    if active_rule:
        # Un índice único por solicitud impide duplicar puntos.
        points = active_rule.puntos_por_solicitud
        db.add(models.MovimientoPuntos(ciudadano_id=req.ciudadano_id, solicitud_id=req.id, regla_id=active_rule.id, puntos=points))
    db.commit()
    citizen = db.get(models.Ciudadano, req.ciudadano_id)
    sent = await send_message(citizen.telefono, f"EcoConecta: recolección #{req.id} confirmada. Puntos registrados: {points} (regla de piloto provisional). Gracias por participar.")
    return {"id": req.id, "estado": req.estado, "puntos": points, "whatsapp_notificado": sent}


@router.get("/admin/resumen")
def resumen(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")
    by_flow = db.execute(select(models.Solicitud.flujo, func.count()).group_by(models.Solicitud.flujo)).all()
    by_state = db.execute(select(models.Solicitud.estado, func.count()).group_by(models.Solicitud.estado)).all()
    points = db.scalar(select(func.coalesce(func.sum(models.MovimientoPuntos.puntos), 0)))
    return {"total": sum(n for _, n in by_flow), "por_flujo": dict(by_flow), "por_estado": dict(by_state), "puntos": points}


@router.get("/admin/regla-puntos")
def ver_regla(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")
    rule = db.scalar(select(models.ReglaPuntos).where(models.ReglaPuntos.activa.is_(True)))
    return {"id": rule.id, "puntos_por_solicitud": rule.puntos_por_solicitud, "nombre": rule.nombre} if rule else {"nombre": "Sin regla activa", "puntos_por_solicitud": None}


@router.put("/admin/regla-puntos")
def cambiar_regla(payload: ReglaPuntosIn, user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")
    for rule in db.scalars(select(models.ReglaPuntos).where(models.ReglaPuntos.activa.is_(True))).all():
        rule.activa = False
    new_rule = models.ReglaPuntos(**payload.model_dump(), activa=True)
    db.add(new_rule)
    db.commit()
    return {"id": new_rule.id, "nombre": new_rule.nombre, "puntos_por_solicitud": new_rule.puntos_por_solicitud}
