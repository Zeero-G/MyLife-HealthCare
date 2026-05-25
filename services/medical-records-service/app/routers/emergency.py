"""
Emergency Router – Read-only emergency profiles and SOS alerts.
The /profile/{userId} endpoint is publicly readable (no JWT) for emergency responders.
"""

from fastapi import APIRouter, HTTPException
from app.core.database import supabase
from app.schemas.records_schemas import EmergencyProfileResponse

router = APIRouter()


@router.get("/profile/{user_id}", response_model=EmergencyProfileResponse)
async def get_emergency_profile(user_id: str):
    """
    Public endpoint – returns minimal emergency data for a patient.
    In production, protect with a scoped QR token check.
    """
    result = supabase.table("emergency_profiles") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found")
    return result.data[0]
