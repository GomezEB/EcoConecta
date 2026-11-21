# Despliegue de EcoConecta para la evaluación (Render)

## Objetivo
Una sola URL HTTPS para **React + FastAPI**, con una **base PostgreSQL administrada**. Docker local (`compose.yaml`) no se modifica; el despliegue usa `Dockerfile.render` y `render.yaml`.

## Requisitos antes del despliegue
- GitHub con los cambios de los cuatro desarrolladores integrados, `npm run build` funcionando.
- No subir `.env`, contraseñas, credenciales o fotografías personales.
- Crear cuenta en https://dashboard.render.com/ y conectar GitHub (requiere acción del propietario).
- Verificar en Render condiciones actuales: bases Free expiran a los 30 días y NO tienen backups administrados. El web Free puede entrar en suspensión y no ofrece Shell. Para la evaluación, comprobar encendido y considerar plan pago si se necesita continuidad.

## Procedimiento con Blueprint
1. Copiar los archivos de este paquete en la **raíz del repositorio EcoConecta**, preservando su estructura. No reemplazar `frontend` ni `backend/app`.
2. Validar localmente: `docker compose up --build -d`; luego `docker compose ps`.
3. Guardar el paquete con Git y subirlo (`git add .dockerignore Dockerfile.render render.yaml deploy backend/scripts/seed_demo.py backend/scripts/selftest.py docs; git commit -m "Preparar demo y despliegue EcoConecta"; git pull --rebase origin main; git push origin main`). Si hay conflictos, no sobrescribir trabajo ajeno.
4. En Render > **New > Blueprint**, conectar repositorio `GomezEB/EcoConecta`, rama `main`; importar `render.yaml`.
5. Revisar los recursos que Render propone: **1 web service Docker** y **1 PostgreSQL**. Revisar cargos/condiciones antes de confirmar. Los nombres deben ser únicos en la cuenta; cambiar si ya están ocupados.
6. El servicio debe usar `Dockerfile.render`. El secret `DATABASE_URL` llega automáticamente desde PostgreSQL. `start-render.sh` convierte `postgresql://` al dialecto `postgresql+psycopg://`.
7. Al quedar publicado, comprobar `https://<tu-app>.onrender.com/api/salud`, `/docs`, el inicio de sesión y el flujo completo.
8. Registrar la URL **real** y los servicios realmente desplegados en `README.md`. Nunca inventar ni anunciar una URL todavía inexistente.

## Crear datos ficticios de la DEMO
En Render > servicio web > Environment, configurar tres contraseñas **distintas** de al menos 12 caracteres:
- `DEMO_ADMIN_PASSWORD`
- `DEMO_HUERTA_PASSWORD`
- `DEMO_RECICLAJE_PASSWORD`

Cambiar `DEMO_SEED_ENABLED` a `true` y **reiniciar/redeployar** el servicio. En el arranque se crean idempotentemente tres usuarios, dos ciudadanos ficticios, una solicitud orgánica de unidad productiva, una solicitud reciclable de hogar y una regla de puntos **provisional, no oficial**, de 2 puntos/kg. Cuando lo confirme en logs, cambiar `DEMO_SEED_ENABLED` a `false` para no ejecutar el seed en siguientes arranques. No hace falta reiniciar otra vez hasta nueva versión; el dato ya quedó guardado.

Usuarios DEMO:
- `fundacion.demo@ecoconecta.invalid` con `DEMO_ADMIN_PASSWORD`
- `huerta.demo@ecoconecta.invalid` con `DEMO_HUERTA_PASSWORD`
- `reciclaje.demo@ecoconecta.invalid` con `DEMO_RECICLAJE_PASSWORD`

**Entregar contraseñas de demostración a jurados por un canal privado**, no en GitHub ni en presentaciones públicas. No incluir datos reales. Son cuentas de evaluación: los jurados pueden modificar los datos ficticios.

## WhatsApp Business Cloud API (si está disponible)
En Render > Environment agregar privadamente:
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `OPENAI_API_KEY` (solo si se usa IA)

En Meta configurar callback `https://<tu-app>.onrender.com/webhooks/whatsapp`, token de verificación coincidente y suscripción a `messages`. El sender de prueba debe estar autorizado. **No mostrar tokens, no usar números reales sin consentimiento y nunca afirmar que la integración está operativa sin comprobar un envío/recepción de prueba.**

El webhook puede tardar en responder durante arranques en frío de planes gratuitos; para una demo importante conviene usar capacidad que no duerma si el presupuesto lo permite.

## Solución de problemas
- `npm run build`: arreglar errores TypeScript *antes* de desplegar. No usar un archivo viejo que quite cambios del equipo.
- `DATABASE_URL`: no usar el hostname `db` de Docker local en Render, ni pegar cadenas de conexión al repositorio.
- `password authentication failed`: corregir credenciales del proveedor, no eliminar volúmenes.
- Frontend carga pero no hay solicitudes: comprobar logs de backend, tabla `solicitudes` y reglas de roles.
- `404` en `/api/...`: comprobar que se copió la plantilla Nginx y que se escucha en `$PORT`.
- Conflicto con otro compañero: resolver Git antes de integrar, sin `git push --force` ni `git reset --hard`.

## Limitaciones
Este despliegue de hackathon corre dos procesos en un contenedor para simplificar una sola URL; para producción real conviene separarlos. `Base.metadata.create_all()` no sustituye un sistema de migraciones versionadas. El seed de demo no crea recolecciones completadas; deben demostrarse en vivo por los usuarios autorizados. Si se habilita Meta/IA, hay que probarlas por separado. Considerar expiración y límites de planes gratuitos.

## Prueba integral automatizada (escribe datos ficticios)
Tras activar las cuentas demo, en Render Shell (si tu plan ofrece acceso) o en un contenedor equivalente con la API en ejecucion:

```bash
DEMO_E2E_ENABLED=true python -m scripts.e2e_demo
```

Requiere las tres variables `DEMO_*_PASSWORD` y que el backend escuche en `127.0.0.1:8000`. Crea **nuevas solicitudes ficticias** y confirma recolecciones por API; no ejecutarlo en una base con datos reales. Si no hay Shell en el proveedor, hacer la demostracion desde la interfaz con cuentas de demo y la lista de `docs/ESCENARIO_JURADOS.md`.

Para comprobaciones de solo lectura en Docker local (despues de copiar este paquete y reconstruir el servicio `api`):

```powershell
docker compose up -d --build api
docker compose exec -e PYTHONPATH=/app api python -m scripts.selftest
```

## Comprobación especial del plan gratuito
- Según documentación oficial de Render consultada para 2026, PostgreSQL Free **expira a los 30 días** y no incluye backups administrados; no usarlo con datos reales y exportar/respaldar todo antes de esa fecha.
- Web Free puede tardar en responder tras inactividad y no ofrece Shell. Para crear demo en cloud, usar bandera `DEMO_SEED_ENABLED=true` una vez y luego devolver a false.
- Si el deploy falla por falta de recursos/plan Free, revisar costos y límites en la cuenta antes de autorizar un plan pago.
