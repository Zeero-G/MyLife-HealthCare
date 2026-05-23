"""
MYLIFE – Family & Profile Service (Port 8003)
Manages linked family accounts, caregivers, children, and women's health tracking.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import family, health
from app.core.config import settings

app = FastAPI(
    title="MYLIFE Family & Profile Service",
    description="Manages linked family accounts, caregivers, and women's health tracking.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(family.router, prefix="/family", tags=["Family"])
app.include_router(health.router, prefix="/health", tags=["Women's Health"])


@app.get("/health")
def health_check():
    return {"service": "family-profile-service", "status": "ok"}
