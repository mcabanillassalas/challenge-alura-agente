from fastapi import FastAPI

from app.api.routes.ask import router as ask_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="API para consultas RAG sobre manuales PDF de ERP Exactus"
)

app.include_router(health_router)
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(ask_router, prefix="/api/v1")
