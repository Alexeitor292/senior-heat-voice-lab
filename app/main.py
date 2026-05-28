from fastapi import FastAPI

from app.config import settings
from app.routes.calls import router as calls_router
from app.routes.twilio_webhooks import router as twilio_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Step 1 prototype for senior heat safety phone check-ins."
)

app.include_router(calls_router)
app.include_router(twilio_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }