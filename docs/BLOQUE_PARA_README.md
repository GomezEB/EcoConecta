## Entrega hackathon EcoConecta — 21/11/2026

- **Repositorio:** https://github.com/GomezEB/EcoConecta
- **URL pública:** PENDIENTE — reemplazar por URL real comprobada en Render.
- **Infraestructura prevista:** Render Docker Web Service (Nginx sirve React + enruta FastAPI) + PostgreSQL administrado. WhatsApp Meta Cloud API y OpenAI son servicios opcionales condicionados a credenciales privadas.
- **Ejecución local:** copiar `.env.example` a `.env`, configurar contraseña/URL PostgreSQL coincidentes y ejecutar `docker compose up --build -d`. Web local en `http://localhost:8080`; salud en `http://localhost:8000/api/salud`.
- **Variables necesarias:** `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (las tres últimas para Docker Compose local); opcionales `CORS_ORIGINS`, `SESSION_HOURS`, `PILOTO_ABIERTO`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `META_GRAPH_VERSION`, `OPENAI_API_KEY`.
- **Credenciales demo privadas en nube:** `DEMO_ADMIN_PASSWORD`, `DEMO_HUERTA_PASSWORD`, `DEMO_RECICLAJE_PASSWORD` y `DEMO_SEED_ENABLED` solo en entorno de evaluación.
- **Documentación:** [despliegue](docs/GUIA_DESPLIEGUE.md), [arquitectura y relaciones](docs/ARQUITECTURA_ENTREGA.md), [guion](docs/ESCENARIO_JURADOS.md), [criterios](docs/PRUEBAS_ACEPTACION_RN01_RN08.md).
- **Regla de puntos de ejemplo:** 2 puntos por kg, no oficial de FSD. Solo se registra al confirmar la recolección humana.
- **Limitaciones:** migraciones versionadas y auditoría avanzada pendientes; Meta/IA requieren credenciales y pruebas reales; planes gratuitos pueden dormir y PostgreSQL gratuito Render tiene límites y vigencia de 30 días.
