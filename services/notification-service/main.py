"""
MYLIFE – Notification Service (Port 8005)
Sends emails and push notifications for key events. Called directly by other services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import notifications
from app.core.config import settings

app = FastAPI(
    title="MYLIFE Notification Service",
    description="Sends email and push notifications for key events across the platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications.router, prefix="/notify", tags=["Notifications"])


@app.get("/health")
def health_check():
    return {"service": "notification-service", "status": "ok"}
