# Arquitectura de entrega — EcoConecta

## Componentes

```mermaid
flowchart TD
  Comunidad[Ciudadano / negocio] -->|WhatsApp opcional| Meta[Meta WhatsApp Business Cloud API]
  Meta -->|Webhook HTTPS| Nginx[Nginx reverse proxy en Render]
  Jurado[Jurado / Coordinadores / Fundacion] -->|HTTPS| Nginx
  Nginx -->|/| React[React + Tailwind SPA]
  Nginx -->|/api y /webhooks| API[FastAPI / SQLAlchemy / Psycopg]
  API -->|PostgreSQL privado| PG[(Render PostgreSQL)]
  API -.->|IA texto/audio/imagen opcional| OpenAI[OpenAI API]
  API -.->|Notificaciones opcionales| Meta
```

El contenedor Render sirve React y API en un dominio compartido; PostgreSQL es un servicio aparte. No almacenar secretos en GitHub. La programación final, la asignación y el cierre se hacen mediante humanos autenticados.

## Modelo de datos resumido

```mermaid
erDiagram
    USUARIOS_INTERNOS ||--o{ USUARIOS_ROLES : tiene
    USUARIOS_INTERNOS ||--o{ SESIONES : autentica
    CIUDADANOS ||--o{ SOLICITUDES : crea
    SOLICITUDES ||--o{ HISTORIAL_SOLICITUDES : registra
    SOLICITUDES ||--o| MOVIMIENTOS_PUNTOS : genera
    REGLAS_PUNTOS ||--o{ MOVIMIENTOS_PUNTOS : aplica
    CIUDADANOS ||--o{ MOVIMIENTOS_PUNTOS : recibe
    CIUDADANOS ||--o| CONVERSACIONES_WHATSAPP : conversa
```

## Restricciones del reto
- RN-01: separación estricta orgánicos / reciclables.
- RN-02: programación con fecha/hora futura y persona asignada.
- RN-03: coordinador y recolector registrados.
- RN-04: id, estado e historial.
- RN-05: puntos solo después de recolección.
- RN-06: regla parametrizable, valores no oficiales FSD.
- RN-07: perfiles con autorización y datos personales mínimos.
- RN-08: habilitación explícita del piloto.

## Componentes cloud para declarar en entrega
- Proveedor: **Render** (solo si realmente se desplegó allí).
- Compute: Render Docker web service; Nginx, React estático, Python 3.12 / FastAPI.
- Datos: Render PostgreSQL administrado.
- Red: dominio HTTPS Render + red entre servicio y PostgreSQL.
- Externos opcionales: Meta Cloud API y OpenAI (si se configuraron y probaron).
- Almacenamiento adicional: no usado en la demo, salvo que otro compañero implemente almacenamiento de medios.
