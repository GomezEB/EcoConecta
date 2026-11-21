# EcoConecta — Cierre integrado para hackathon 2026

**BASE VERIFICADA:** GitHub `GomezEB/EcoConecta`, rama `main`, commit
`2ff923d5a5b9f206b399a794e23f44e54cc9b262` (versión consultada).

Este ZIP es **una actualización para el repositorio clonado**, NO un repositorio nuevo.
Conserva `backend/app/models.py`, `operacion.py`, `conversacion.py`, el diseño del frontend y el PostgreSQL local.

## Contenido

- `backend/app/routers/auth.py`: invalida el token en PostgreSQL al cerrar sesión.
- `frontend/src/App.tsx`: misma versión actual de GitHub, cambia solo el botón Salir para invocar el logout seguro.
- `tests/test_api_postgres.py`: prueba REAL de PostgreSQL, roles, orgánicos, reciclables, programación, puntos, CSV y logout (protegida contra ejecución accidental en DB personal).
- `.github/workflows/ci.yml`: compila React y ejecuta pytest en GitHub Actions sobre Postgres temporal.
- `backend/scripts/seed_demo.py`, `selftest.py`, `e2e_demo.py`: utilidades de demo.
- `Dockerfile.render`, `render.yaml`, `deploy/`: infraestructura cloud de Render en una URL.
- `docs/`: arquitectura, modelo de datos, criterios de aceptación, checklist y guion.

## Aplicación paso a paso (Windows + VS Code)

1. **No copies todavía si tu amigo está modificando App.tsx.** Coordinen un punto de integración.
2. En la raíz: `git status` y `git pull origin main`; si hay cambios locales, hagan commit antes.
3. Descarga/descomprime este ZIP y **COPIA SU CONTENIDO** (no la carpeta contenedora) encima de `EcoConecta`.
4. Si GitHub avanzó desde el commit citado, revisa `git diff -- frontend/src/App.tsx` y conserva las modificaciones nuevas de tu amigo. El cambio necesario en App es el botón `Salir`.
5. Ejecuta `docker compose up --build -d`. La base PostgreSQL local se preserva.
6. Comprueba `docker compose ps` y `/api/salud`.
7. Ejecuta `docker compose exec -e PYTHONPATH=/app api python -m scripts.selftest`.
8. **Prueba manual** usando el guion `docs/ESCENARIO_JURADOS.md`.
9. Haz `git status`, `git diff --check`, `git add` de los archivos previstos, commit, `git pull --rebase origin main`, push. No uses `--force`.
10. En Render, crear Blueprint desde `render.yaml`; poner contraseñas DEMO_* **solo en Environment** y activar/desactivar `DEMO_SEED_ENABLED` como indica `docs/GUIA_DESPLIEGUE.md`.

## Lo que este ZIP no puede hacer automáticamente

- Desplegar en una cuenta de Render sin que su propietario la conecte y autorice.
- Generar tokens de Meta/OpenAI ni demostrar WhatsApp real sin credenciales.
- Crear la URL de la nube o verificar un contenedor en tu Windows.
- Mover datos del PostgreSQL local a la nube. El script genera datos ficticios equivalentes.

## Seguridad y compatibilidad

- NO subas `.env`, bases reales, fotos, passwords ni tokens a GitHub.
- NO ejecutes `docker compose down -v`, ni `docker volume prune`.
- Las nuevas pruebas que destruyen tablas solo permiten la BD **`ecoconecta_test`**, con `ECO_TEST_DATABASE_URL` idéntica a `DATABASE_URL`; NO se ejecutan en tu PostgreSQL habitual.
- No sustituyas todos los archivos de tu proyecto por un ZIP anterior: este contiene únicamente los cambios de integración listados.
