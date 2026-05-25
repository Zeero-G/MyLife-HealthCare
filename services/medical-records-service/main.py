"""
MYLIFE – Medical Records Service (Port 8002)
Core service: stores & manages all health records, QR sharing, emergency profiles, SOS alerts.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import records, emergency, appointments
from app.core.config import settings

app = FastAPI(
    title="MYLIFE Medical Records Service",
    description="Core service: manages all health records, QR sharing, and emergency profiles.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(records.router, prefix="/records", tags=["Records"])
app.include_router(emergency.router, prefix="/emergency", tags=["Emergency"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])


@app.get("/health")
def health_check():
    return {"service": "medical-records-service", "status": "ok"}
