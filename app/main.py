from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.database import init_db
from app.routes.baselines import router as baselines_router
from app.routes.calls import router as calls_router
from app.routes.dashboard import router as dashboard_router
from app.routes.heat_risk import router as heat_risk_router
from app.routes.schedules import router as schedules_router
from app.routes.seniors import router as seniors_router
from app.routes.twilio_webhooks import router as twilio_router
from app.routes.ui_api import router as ui_api_router
from app.routes.support_network import router as support_network_router
from app.routes.operational_status import router as operational_status_router
from app.routes.demographics import router as demographics_router
from app.routes.timeline import router as timeline_router
from app.routes.operator_actions import router as operator_actions_router
from app.routes.conversation_analysis import router as conversation_analysis_router
from app.routes.check_ins import router as check_ins_router
from app.routes.ai_call_sessions import router as ai_call_sessions_router
from app.routes.ai_call_sessions import router as ai_call_sessions_router
from app.routes.twilio_ai_stream import router as twilio_ai_stream_router
from app.security.basic_auth import BasicDashboardAuthMiddleware
from app.security.twilio_signature import TwilioSignatureValidationMiddleware
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

app.add_middleware(BasicDashboardAuthMiddleware)
app.add_middleware(TwilioSignatureValidationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy static dashboard.
# The real frontend now lives in /frontend as a Next.js app.
# This mount is optional so the backend does not crash if app/static is missing.
static_dir = Path("app/static")

if static_dir.exists():
    app.mount(
        "/ui",
        StaticFiles(directory=str(static_dir), html=True),
        name="ui",
    )

app.include_router(calls_router)
app.include_router(seniors_router)
app.include_router(support_network_router)
app.include_router(demographics_router)
app.include_router(schedules_router)
app.include_router(heat_risk_router)
app.include_router(baselines_router)
app.include_router(dashboard_router)
app.include_router(operational_status_router)
app.include_router(conversation_analysis_router)
app.include_router(timeline_router)
app.include_router(operator_actions_router)
app.include_router(twilio_router)
app.include_router(ui_api_router)
app.include_router(check_ins_router)
app.include_router(ai_call_sessions_router)
app.include_router(ai_call_sessions_router)
app.include_router(twilio_ai_stream_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
        "dashboard_ui": "/ui" if static_dir.exists() else None,
        "next_frontend": "http://localhost:3000",
        "ui_api": "/ui-api",
        "dashboard_auth_enabled": settings.dashboard_auth_enabled,
        "twilio_signature_validation_enabled": settings.twilio_signature_validation_enabled,
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