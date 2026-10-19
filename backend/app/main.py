from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.calls import router as calls_router
from backend.app.api.knowledge import router as knowledge_router
from backend.app.api.leads import router as leads_router
from backend.app.api.scripts import router as scripts_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.webhooks import router as webhooks_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine

# Ensure database tables exist on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="India-First Multi-Tenant AI Lead Generation & Voice Calling SaaS Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local Next.js frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Core API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(leads_router, prefix=settings.API_V1_STR)
app.include_router(knowledge_router, prefix=settings.API_V1_STR)
app.include_router(scripts_router, prefix=settings.API_V1_STR)
app.include_router(calls_router, prefix=settings.API_V1_STR)
app.include_router(webhooks_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)


@app.get("/healthz")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "env": settings.APP_ENV
    }
