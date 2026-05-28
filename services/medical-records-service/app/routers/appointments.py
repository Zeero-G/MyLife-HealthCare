"""
Appointments Router – Patient books doctor, doctor manages queue.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.security import get_current_user
from app.core.database import supabase, supabase_auth

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_id: str
    scheduled_at: str   # ISO datetime string
    reason: Optional[str] = None


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None   # confirmed, completed, cancelled
    notes: Optional[str] = None
    scheduled_at: Optional[str] = None


# ── POST /appointments/ ─────────────────────────────────────── Patient books
@router.post("/", status_code=201)
async def book_appointment(
    payload: AppointmentCreate,
    current_user: dict = Depends(get_current_user),
):
    """Patient books an appointment with a doctor."""
    if current_user.get("role") not in ("patient",):
        raise HTTPException(status_code=403, detail="Only patients can book appointments")

    # Verify doctor exists and has doctor role
    doctor = supabase_auth.table("users") \
        .select("id, full_name, email") \
        .eq("id", payload.doctor_id) \
        .eq("role", "doctor") \
        .execute()
    if not doctor.data:
        raise HTTPException(status_code=404, detail="Doctor not found")

    result = supabase.table("appointments").insert({
        "patient_id": current_user["sub"],
        "doctor_id": payload.doctor_id,
        "scheduled_at": payload.scheduled_at,
        "reason": payload.reason,
        "status": "pending",
    }).execute()

    return {
        **result.data[0],
        "doctor_name": doctor.data[0]["full_name"],
    }


# ── GET /appointments/mine ─────────────────────────────────── Patient's own
@router.get("/mine")
async def get_my_appointments(current_user: dict = Depends(get_current_user)):
    """Get appointments for the currently logged-in patient."""
    result = supabase.table("appointments") \
        .select("*") \
        .eq("patient_id", current_user["sub"]) \
        .order("scheduled_at", desc=True) \
        .execute()

    # Enrich with doctor names
    enriched = []
    for appt in result.data:
        doctor = supabase_auth.table("users") \
            .select("full_name, email") \
            .eq("id", appt["doctor_id"]) \
            .execute()
        enriched.append({
            **appt,
            "doctor_name": doctor.data[0]["full_name"] if doctor.data else "Unknown",
            "doctor_email": doctor.data[0]["email"] if doctor.data else "",
        })
    return enriched


# ── GET /appointments/doctor ───────────────────────────────── Doctor's queue
@router.get("/doctor")
async def get_doctor_appointments(current_user: dict = Depends(get_current_user)):
    """Get all appointments assigned to the currently logged-in doctor."""
    if current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this endpoint")

    result = supabase.table("appointments") \
        .select("*") \
        .eq("doctor_id", current_user["sub"]) \
        .order("scheduled_at", desc=True) \
        .execute()

    # Enrich with patient names
    enriched = []
    for appt in result.data:
        patient = supabase_auth.table("users") \
            .select("full_name, email, gender") \
            .eq("id", appt["patient_id"]) \
            .execute()
        enriched.append({
            **appt,
            "patient_name": patient.data[0]["full_name"] if patient.data else "Unknown",
            "patient_email": patient.data[0]["email"] if patient.data else "",
            "patient_gender": patient.data[0].get("gender") if patient.data else None,
        })
    return enriched


# ── PUT /appointments/{appointment_id} ────────────────────── Update status
@router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Doctor confirms/completes/cancels an appointment; patient can also cancel."""
    # Fetch the appointment
    appt = supabase.table("appointments") \
        .select("*") \
        .eq("id", appointment_id) \
        .execute()
    if not appt.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    a = appt.data[0]
    is_doctor = current_user.get("role") == "doctor" and a["doctor_id"] == current_user["sub"]
    is_patient = a["patient_id"] == current_user["sub"]

    if not is_doctor and not is_patient:
        raise HTTPException(status_code=403, detail="Not authorized to modify this appointment")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = supabase.table("appointments") \
        .update(update_data) \
        .eq("id", appointment_id) \
        .execute()
    return result.data[0]


# ── DELETE /appointments/{appointment_id} ─────────────────── Cancel
@router.delete("/{appointment_id}", status_code=204)
async def cancel_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel an appointment (patient or doctor)."""
    appt = supabase.table("appointments") \
        .select("patient_id, doctor_id") \
        .eq("id", appointment_id) \
        .execute()
    if not appt.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    a = appt.data[0]
    if a["patient_id"] != current_user["sub"] and a["doctor_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    supabase.table("appointments").delete().eq("id", appointment_id).execute()
