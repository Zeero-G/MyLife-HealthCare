"""
MYLIFE – AI Processing Service (Port 8004)
Extracts structured data from uploaded medical documents using Claude API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ai_processing
from app.core.config import settings

app = FastAPI(
    title="MYLIFE AI Processing Service",
    description="Extracts structured data from uploaded medical documents using Claude API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_processing.router, prefix="/ai", tags=["AI Processing"])


@app.get("/health")
def health_check():
    return {"service": "ai-processing-service", "status": "ok"}
