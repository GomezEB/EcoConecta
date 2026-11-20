import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models
from app.db import get_db
from app.security import current_user, require_role

router = APIRouter(prefix="/api/admin", tags=["reportes"])

@router.get("/exportar-csv")
def exportar(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    require_role(db, user, "administrador")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["solicitud", "flujo", "estado", "tipo_generador", "programada_para", "cantidad", "unidad", "puntos"])
    for req in db.scalars(select(models.Solicitud).order_by(models.Solicitud.id)).all():
        citizen = db.get(models.Ciudadano, req.ciudadano_id)
        movement = db.scalar(select(models.MovimientoPuntos).where(models.MovimientoPuntos.solicitud_id == req.id))
        writer.writerow([req.id, req.flujo, req.estado, citizen.tipo_generador if citizen else "", req.programada_para or "", req.cantidad_recibida or "", req.unidad or "", movement.puntos if movement else 0])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="ecoconecta_reporte.csv"'})
