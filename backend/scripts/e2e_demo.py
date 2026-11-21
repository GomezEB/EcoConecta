"""Prueba INTEGRAL contra una DEMO con datos ficticios (escribe en PostgreSQL).

PRECONDICIONES:
 - Haber ejecutado seed_demo antes para crear cuentas DEMO.
 - DEMO_ADMIN_PASSWORD, DEMO_HUERTA_PASSWORD, DEMO_RECICLAJE_PASSWORD presentes.
 - FastAPI levantada. Ejecutar en contenedor web: python -m scripts.e2e_demo

La prueba no requiere WhatsApp/IA. No usar contra datos reales.
"""
from __future__ import annotations
import os
import uuid
from datetime import datetime, timedelta, timezone
import httpx

URL = os.getenv("DEMO_API_URL", "http://127.0.0.1:8000").rstrip("/")
ACC = {
    "admin": ("fundacion.demo@ecoconecta.invalid", "DEMO_ADMIN_PASSWORD"),
    "huerta": ("huerta.demo@ecoconecta.invalid", "DEMO_HUERTA_PASSWORD"),
    "reciclaje": ("reciclaje.demo@ecoconecta.invalid", "DEMO_RECICLAJE_PASSWORD"),
}

def run() -> None:
    if os.getenv("DEMO_E2E_ENABLED", "").lower() != "true":
        raise SystemExit("Para ejecutar pruebas que crean solicitudes, usar DEMO_E2E_ENABLED=true en entorno DEMO")
    with httpx.Client(base_url=URL, timeout=20) as http:
        tokens: dict[str, str] = {}
        for name, (email, secret_key) in ACC.items():
            pw = os.getenv(secret_key, "")
            if not pw:
                raise SystemExit(f"Falta {secret_key} para el test")
            resp = http.post("/api/auth/login", json={"correo": email, "contrasena": pw})
            resp.raise_for_status()
            tokens[name] = resp.json()["token"]
        def req(role: str, method: str, path: str, payload=None):
            r = http.request(method, path, json=payload, headers={"Authorization": f"Bearer {tokens[role]}"})
            if r.is_error:
                raise AssertionError(f"HTTP {r.status_code} {role} {method} {path}: {r.text[:240]}")
            return r.json()
        print("OK: inicio de sesion de tres perfiles")
        baseline = req("admin", "GET", "/api/admin/resumen")["puntos"]
        req("admin", "PUT", "/api/admin/regla-puntos", {"puntos_por_kg": 2, "nombre": "Regla temporal DEMO E2E - NO OFICIAL"})
        uid = uuid.uuid4().hex[:12]
        ids: dict[str, int] = {}
        for flow, role, qty, expected in (("organicos", "huerta", 3, 6), ("reciclables", "reciclaje", 2, 4)):
            citizen = req("admin", "POST", "/api/ciudadanos", {
                "telefono": f"DEMO-{uid}-{flow[:3]}",
                "nombre": f"Ciudadano ficticio {flow}",
                "direccion": "Villas de San Pablo, local ficticio de prueba",
                "tipo_generador": "unidad_productiva" if flow == "organicos" else "hogar",
                "consentimiento": True,
                "habilitado_piloto": True,
            })
            s = req("admin", "POST", "/api/solicitudes", {
                "ciudadano_id": citizen["id"], "flujo": flow,
                "preferencia_horaria": "Proximo dia durante la tarde",
                "observaciones": "TEST E2E - DATOS FICTICIOS",
            })
            sid = s["id"]
            ids[flow] = sid
            assert s["estado"] == "recibida"
            other = "reciclaje" if role == "huerta" else "huerta"
            deny = http.get(f"/api/solicitudes/{sid}", headers={"Authorization": f"Bearer {tokens[other]}"})
            assert deny.status_code == 404, f"Acceso cruzado indebido: HTTP {deny.status_code}"
            req(role, "POST", f"/api/solicitudes/{sid}/revisar")
            people = req(role, "GET", "/api/personal")
            target_role = "huertero" if role == "huerta" else "reciclador"
            collector = next(p for p in people if target_role in p["roles"])
            req(role, "POST", f"/api/solicitudes/{sid}/asignar", {"recolector_id": collector["id"]})
            date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            req(role, "POST", f"/api/solicitudes/{sid}/programar", {"fecha_hora": date})
            before = req("admin", "GET", "/api/admin/resumen")["puntos"]
            completed = req(role, "POST", f"/api/solicitudes/{sid}/recolectar", {"cantidad_recibida": qty, "unidad": "kg"})
            assert completed["estado"] == "recolectada" and completed["puntos"] == expected, completed
            after = req("admin", "GET", "/api/admin/resumen")["puntos"]
            assert after - before == expected, f"Puntos inesperados: {before} -> {after}"
            detail = req(role, "GET", f"/api/solicitudes/{sid}")
            assert detail["estado"] == "recolectada" and len(detail["historial"]) >= 4
            print(f"OK: {flow}, solicitud #{sid}, peso {qty} kg, puntos {expected}, historial y permisos")
        print(f"OK: prueba de 2 flujos; incremento total de puntos = {req('admin', 'GET', '/api/admin/resumen')['puntos'] - baseline}")
        print("Pruebas de extremo a extremo terminadas. Datos E2E ficticios persistieron para auditoria demo.")

if __name__ == "__main__":
    run()
