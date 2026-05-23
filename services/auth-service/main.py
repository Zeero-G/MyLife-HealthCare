"""
MYLIFE – Authentication Service (Port 8001)
Responsibilities: Registration, Login, JWT issue/refresh, Role management, Password reset
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.core.config import settings

app = FastAPI(
    title="MYLIFE Auth Service",
    description="Handles all user identity, authentication, roles, and permissions.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


@app.get("/health")
def health_check():
    return {"service": "auth-service", "status": "ok"}
