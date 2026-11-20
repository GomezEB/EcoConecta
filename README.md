# EcoConecta — MVP oficial Hackathon 2026

**Fundación Santo Domingo + Universidad Libre | Villas de San Pablo (Barranquilla)**

Este proyecto es un **esqueleto funcional y extensible** conforme al reto oficial. Reemplaza la estructura anterior de SQLite y frontend HTML simple por PostgreSQL, FastAPI, React/TypeScript/Tailwind, Docker y un adaptador de WhatsApp Business Cloud API. **No contiene credenciales ni datos reales.**

## Estructura

```text
EcoConecta-MVP-Oficial/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, db.py, models.py, schemas.py, security.py
│   │   ├── workflows.py
│   │   ├── routers/         auth.py, operacion.py, reportes.py, webhook.py
│   │   └── services/        conversacion.py, whatsapp.py
│   ├── scripts/crear_cuentas.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/                App.tsx, main.tsx, api.ts, styles.css
│   ├── package.json, vite.config.ts, tailwind.config.js
│   ├── Dockerfile, nginx.conf
│   └── index.html
├── tests/test_reglas.py
├── docs/ARQUITECTURA.md
├── docs/MIGRACION-DESDE-ETAPA-05.md
├── compose.yaml
├── .env.example
└── .gitignore
```

## Requisitos locales

- VS Code, **Docker Desktop** (Docker Compose disponible), Git.
- Para uso vía Docker no es obligatorio instalar Python ni Node en Windows.
- Para editar frontend directamente: Node 22 recomendado. Backend: Python 3.12 recomendado.

## Primer inicio — PowerShell en la carpeta raíz

**1.** Duplica `.env.example` y renómbralo `.env`. Cambia `POSTGRES_PASSWORD` y el mismo valor dentro de `DATABASE_URL` (los servicios internos de Docker usan `db:5432`). Nunca subas `.env` a GitHub.

```powershell
Copy-Item .env.example .env
notepad .env
```

**2.** Construye y ejecuta PostgreSQL, la API y React:

```powershell
docker compose up --build -d
```

**3.** Comprueba:

- Panel web: http://localhost:8080
- Salud API: http://localhost:8000/api/salud
- Documentación Swagger: http://localhost:8000/docs

**4.** Crea **tres cuentas internas** (dos encargados + administración fundación), ejecutando el comando 3 veces y eligiendo las opciones 1, 2 y 3 en el menú:

```powershell
docker compose exec api python scripts/crear_cuentas.py
```

**5.** Inicia sesión en `http://localhost:8080` con la cuenta de fundación. En «Fundación / Demo» crea ciudadanos ficticios y dos solicitudes de prueba: una orgánica y otra reciclable. Luego, desde la bandeja, revisa → asigna → programa y, con cada cuenta recolectora, confirma recolección. Vuelve al panel de fundación para comprobar puntos y CSV.

**6.** Para detener sin borrar datos:

```powershell
docker compose down
```

> **Nunca uses** `docker compose down -v` si quieres conservar tu base de datos.

## Cómo funciona WhatsApp

Integración por webhook exclusivo de **Meta WhatsApp Business Cloud API**. Configura en `.env` las variables `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` y el Graph API correspondiente. El proveedor debe acceder a una URL **HTTPS pública** como `https://TU-DOMINIO/webhooks/whatsapp`. `localhost` no funciona como webhook público. No se incluyen credenciales.

Mensajes `texto` se guían con un diálogo de preguntas y consentimiento. `audio` requiere clave `OPENAI_API_KEY` y transcripción; `imagen` admite sugerencia de categoría con OpenAI y confirmación humana. Al programar/cerrar, el sistema intenta avisar por WhatsApp cuando la integración está configurada. La asignación final, día/hora y cierre siempre son humanos.

> Sin credenciales de Meta ni OpenAI puedes probar el flujo principal desde «Fundación / Demo». **Eso no equivale a una conexión real de WhatsApp.** Una notificación no enviada devuelve `whatsapp_notificado: false`.

## Alcance y límites visibles

- **Sí:** PostgreSQL, login interno, roles por colectivo, creación demo de solicitudes, revisión, asignación, programación humana, cierre humano, regla de puntos configurable, historial, reporte CSV, guía ambiental y adaptador de WhatsApp.
- **Condicionado a credenciales y despliegue:** recepción real WhatsApp, descarga y análisis de imágenes, transcripción de audios, confirmaciones salientes.
- **No implementado todavía:** respuesta por audio hablado, publicación en nube, almacenamiento duradero de imágenes, migración automática de SQLite, migraciones versionadas o auditoría avanzada.
- Los puntos de ejemplo son **provisionales y no oficiales**; se activan manualmente en el panel Fundación.
- Esta plantilla es un punto de partida, **no una entrega completa certificada ni una aplicación en producción**.

## GitHub y entrega

```powershell
git init
git add .
git commit -m "Estructura oficial EcoConecta"
```

Crea el repositorio desde tu cuenta de GitHub y añade a tus compañeros. Publica el código, documentación y `.env.example`, **nunca** `.env`, tokens, contraseñas, fotos ni bases de datos. Para la evaluación deben completar la URL publicada en nube, la configuración real de Meta y el proveedor de infraestructura.

## Responsabilidades sugeridas para 4 integrantes

1. Backend / PostgreSQL / roles.
2. React / Tailwind / panel de encargados y fundación.
3. WhatsApp Cloud API / webhooks / conversación / notificaciones.
4. OpenAI (audio/visión) / pruebas / reportes y soporte de despliegue.

Consulta el [diagrama de arquitectura](docs/ARQUITECTURA.md) y la [guía de migración](docs/MIGRACION-DESDE-ETAPA-05.md).
