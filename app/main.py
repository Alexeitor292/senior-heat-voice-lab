from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.database import init_db
from app.routes.calls import router as calls_router
from app.routes.heat_risk import router as heat_risk_router
from app.routes.schedules import router as schedules_router
from app.routes.seniors import router as seniors_router
from app.routes.twilio_webhooks import router as twilio_router
from app.services.checkin_store_service import checkin_store_service
from app.services.profile_service import profile_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialized.")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Prototype for senior heat safety phone check-ins.",
    lifespan=lifespan,
)

app.include_router(calls_router)
app.include_router(seniors_router)
app.include_router(schedules_router)
app.include_router(heat_risk_router)
app.include_router(twilio_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }


@app.get("/debug/check-ins")
def get_recent_check_ins(limit: int = 10):
    return {
        "items": checkin_store_service.get_recent_check_ins(limit=limit)
    }


@app.get("/debug/call-sessions")
def get_recent_call_sessions(limit: int = 10):
    return {
        "items": profile_service.list_recent_call_sessions(limit=limit)
    }