# Coordinación de dos desarrolladores — EcoConecta

1. Antes de empezar: `git status`, luego `git pull origin main` (solo con árbol de trabajo limpio).
2. Repartir propiedad temporal: integrante A en `backend/app` + `backend/scripts` + `tests`; integrante B en `frontend/src` y diseño. Acordar quién integra `render.yaml`, README y `docs/`.
3. Mantener el mismo único repositorio. Para reducir conflictos, **no editar App.tsx simultáneamente**.
4. Commit pequeño con descripción; `git pull --rebase origin main`; `git push origin main`. No usar `--force`.
5. GitHub Actions debe pasar en verde antes del despliegue: compilación frontend, pruebas de reglas y de API contra PostgreSQL real.
6. Los dos usan `.env` local diferente; el entorno demo de Render usa variables privadas y una sola PostgreSQL compartida.
7. Demostrar ambas rutas con ciudadanos **ficticios**. No cargar datos personales reales sin autorización.
8. `render.yaml` crea servicios con costos/limitaciones sujetos a comprobación; aprobar en panel antes de crear.
