import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
CORS_ORIGINS = [v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if v.strip()]
SESSION_HOURS = int(os.getenv("SESSION_HOURS", "12"))
PILOTO_ABIERTO = os.getenv("PILOTO_ABIERTO", "false").lower() == "true"
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
META_GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v23.0")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
