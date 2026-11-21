# Cobertura de criterios del reto EcoConecta — 20–21 nov 2026

| Criterio | Comprobación de aceptación | Evidencia |
|---|---|---|
| RN-01 separación | orgánicos visibles solo para huerta; reciclables solo para reciclaje | `tests/test_api_postgres.py`, 2 flujos |
| RN-02 programación | sin coordinador/recolector falla; fecha futura y con zona; `programada` visible | `tests/test_api_postgres.py`, API |
| RN-03 asignación | persona y coordinador registrados; otro colectivo rechazado | `tests/test_api_postgres.py`, API |
| RN-04 trazabilidad | id, estado, 4+ eventos por solicitud | `tests/test_api_postgres.py`, historial |
| RN-05 cierre | puntos nulos antes de recoger; no segunda recolección | `tests/test_api_postgres.py` |
| RN-06 regla puntos | demo 2 puntos/kg, 3 kg=6, 2 kg=4; NO oficial FSD | `tests/test_api_postgres.py` y panel |
| RN-07 privacidad | acceso cruzado a detalle 404; reporte restringido a admin | `tests/test_api_postgres.py` |
| RN-08 piloto | ciudadanos con consentimiento + habilitación; otro no permitido | revisión API + `seed_demo.py` |

Otros entregables:
- React móvil y paleta/manual: revisar en móviles reales antes de jurados.
- WhatsApp Cloud API y OpenAI son integraciones **condicionadas**, no simular actividad real sin credenciales.
- Evidenciar URL de Render públicamente, README actualizado y diagrama de arquitectura.
- La prueba E2E CI usa PostgreSQL real en contenedor **temporal** de GitHub Actions.
