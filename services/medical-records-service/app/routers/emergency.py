"""
Emergency Router – token-based public access; authenticated profile CRUD for owners.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_user
from app.core.database import supabase
from app.core.audit import write_audit
from app.schemas.records_schemas import (
    EmergencyProfileUpsert,
    EmergencyProfileResponse,
    EmergencyPublicProfileResponse,
    EmergencyContact,
    MedicalInfoStatus,
)

router = APIRouter()


class EmergencyAccessTokenResponse(BaseModel):
    token: str
    expires_at: str
    access_path: str


def _active_token_query(token: str):
    return supabase.table("emergency_access_tokens") \
        .select("*") \
        .eq("token", token) \
        .is_("revoked_at", "null") \
        .execute()


def _resolve_contacts(payload: EmergencyProfileUpsert) -> list[dict[str, Any]]:
    if payload.emergency_contacts:
        return [c.model_dump() for c in payload.emergency_contacts]
    if payload.emergency_contact_name and payload.emergency_contact_phone:
        return [{
            "name": payload.emergency_contact_name,
            "phone": payload.emergency_contact_phone,
            "relationship": "Emergency contact",
            "priority": 1,
            "notes": None,
        }]
    return []


def _primary_contact(contacts: list[dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    if not contacts:
        return None, None
    primary = sorted(contacts, key=lambda c: c.get("priority", 999))[0]
    return primary.get("name"), primary.get("phone")


def _validate_status_field(status: str, items: list, label: str) -> None:
    if status not in {s.value for s in MedicalInfoStatus}:
        raise HTTPException(status_code=422, detail=f"Invalid {label} status")
    if status == MedicalInfoStatus.HAS_ITEMS.value and not items:
        raise HTTPException(
            status_code=422,
            detail=f"{label} status is has_items but no items were provided",
        )


def _merge_profile_state(
    payload: EmergencyProfileUpsert,
    existing: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    base = existing or {}
    contacts = _resolve_contacts(payload) if (
        payload.emergency_contacts is not None
        or payload.emergency_contact_name is not None
        or payload.emergency_contact_phone is not None
    ) else (base.get("emergency_contacts") or [])

    allergies = payload.allergies if payload.allergies is not None else (base.get("allergies") or [])
    chronic_conditions = payload.chronic_conditions if payload.chronic_conditions is not None else (base.get("chronic_conditions") or [])
    medications = payload.current_medications if payload.current_medications is not None else (base.get("current_medications") or [])

    allergies_status = (
        payload.allergies_status.value if payload.allergies_status is not None
        else base.get("allergies_status", MedicalInfoStatus.UNKNOWN.value)
    )
    conditions_status = (
        payload.conditions_status.value if payload.conditions_status is not None
        else base.get("conditions_status", MedicalInfoStatus.UNKNOWN.value)
    )
    medications_status = (
        payload.medications_status.value if payload.medications_status is not None
        else base.get("medications_status", MedicalInfoStatus.UNKNOWN.value)
    )

    _validate_status_field(allergies_status, allergies, "allergies")
    _validate_status_field(conditions_status, chronic_conditions, "conditions")
    _validate_status_field(medications_status, medications, "medications")

    contact_name, contact_phone = _primary_contact(contacts)
    if not contact_name and base.get("emergency_contact_name"):
        contact_name = base.get("emergency_contact_name")
        contact_phone = base.get("emergency_contact_phone")

    now = datetime.utcnow().isoformat()
    show_public = (
        payload.show_emergency_contacts_publicly
        if payload.show_emergency_contacts_publicly is not None
        else base.get("show_emergency_contacts_publicly", False)
    )

    return {
        "blood_type": payload.blood_type if payload.blood_type is not None else base.get("blood_type"),
        "allergies": allergies,
        "chronic_conditions": chronic_conditions,
        "current_medications": medications,
        "emergency_contacts": contacts,
        "allergies_status": allergies_status,
        "conditions_status": conditions_status,
        "medications_status": medications_status,
        "last_confirmed_at": now,
        "show_emergency_contacts_publicly": show_public,
        "emergency_contact_name": contact_name,
        "emergency_contact_phone": contact_phone,
        "updated_at": now,
    }


def _format_profile_response(row: dict[str, Any]) -> EmergencyProfileResponse:
    contacts_raw = row.get("emergency_contacts") or []
    if not contacts_raw and row.get("emergency_contact_name") and row.get("emergency_contact_phone"):
        contacts_raw = [{
            "name": row["emergency_contact_name"],
            "phone": row["emergency_contact_phone"],
            "relationship": "Emergency contact",
            "priority": 1,
        }]
    contacts = [EmergencyContact(**c) for c in contacts_raw]
    return EmergencyProfileResponse(
        user_id=row["user_id"],
        blood_type=row.get("blood_type"),
        allergies=row.get("allergies") or [],
        chronic_conditions=row.get("chronic_conditions") or [],
        current_medications=row.get("current_medications") or [],
        emergency_contacts=contacts,
        allergies_status=MedicalInfoStatus(row.get("allergies_status", MedicalInfoStatus.UNKNOWN.value)),
        conditions_status=MedicalInfoStatus(row.get("conditions_status", MedicalInfoStatus.UNKNOWN.value)),
        medications_status=MedicalInfoStatus(row.get("medications_status", MedicalInfoStatus.UNKNOWN.value)),
        last_confirmed_at=row.get("last_confirmed_at"),
        show_emergency_contacts_publicly=bool(row.get("show_emergency_contacts_publicly", False)),
        emergency_contact_name=row.get("emergency_contact_name"),
        emergency_contact_phone=row.get("emergency_contact_phone"),
    )


def _format_public_response(row: dict[str, Any]) -> EmergencyPublicProfileResponse:
    contacts = None
    if row.get("show_emergency_contacts_publicly"):
        contacts_raw = row.get("emergency_contacts") or []
        contacts = [EmergencyContact(**c) for c in contacts_raw]

    return EmergencyPublicProfileResponse(
        blood_type=row.get("blood_type"),
        allergies_status=MedicalInfoStatus(row.get("allergies_status", MedicalInfoStatus.UNKNOWN.value)),
        allergies=row.get("allergies") or [],
        conditions_status=MedicalInfoStatus(row.get("conditions_status", MedicalInfoStatus.UNKNOWN.value)),
        chronic_conditions=row.get("chronic_conditions") or [],
        medications_status=MedicalInfoStatus(row.get("medications_status", MedicalInfoStatus.UNKNOWN.value)),
        current_medications=row.get("current_medications") or [],
        last_confirmed_at=row.get("last_confirmed_at"),
        emergency_contacts=contacts,
    )


_PROFILE_SELECT = (
    "user_id, blood_type, allergies, chronic_conditions, current_medications, "
    "emergency_contacts, allergies_status, conditions_status, medications_status, "
    "last_confirmed_at, show_emergency_contacts_publicly, "
    "emergency_contact_name, emergency_contact_phone"
)


# ── GET /emergency/access/{token} ────────────────────────────
@router.get("/access/{token}", response_model=EmergencyPublicProfileResponse)
async def get_emergency_by_token(token: str):
    """Public endpoint – emergency-safe fields only, via opaque access token."""
    token_row = _active_token_query(token)
    if not token_row.data:
        raise HTTPException(status_code=404, detail="Invalid or revoked emergency access token")

    row = token_row.data[0]
    expires_at = row.get("expires_at")
    if expires_at:
        exp = datetime.fromisoformat(expires_at.replace("Z", ""))
        if exp < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Emergency access token expired")

    profile = supabase.table("emergency_profiles") \
        .select(_PROFILE_SELECT) \
        .eq("user_id", row["user_id"]) \
        .execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found")

    write_audit(row["user_id"], "emergency_profile_accessed", "emergency_profiles", row["user_id"])
    return _format_public_response(profile.data[0])


# ── POST /emergency/access-token ───────────────────────────────
@router.post("/access-token", response_model=EmergencyAccessTokenResponse, status_code=201)
async def create_emergency_access_token(current_user: dict = Depends(get_current_user)):
    """Issue an opaque emergency QR/access token for the authenticated owner."""
    profile = supabase.table("emergency_profiles") \
        .select("id") \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Create an emergency profile before generating an access token")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.EMERGENCY_TOKEN_EXPIRE_DAYS)

    supabase.table("emergency_access_tokens").insert({
        "user_id": current_user["sub"],
        "token": token,
        "expires_at": expires_at.isoformat(),
    }).execute()

    return EmergencyAccessTokenResponse(
        token=token,
        expires_at=expires_at.isoformat(),
        access_path=f"/emergency/access/{token}",
    )


# ── DELETE /emergency/access-token/{token} ─────────────────────
@router.delete("/access-token/{token}", status_code=204)
async def revoke_emergency_access_token(token: str, current_user: dict = Depends(get_current_user)):
    """Revoke an emergency access token owned by the current user."""
    row = supabase.table("emergency_access_tokens") \
        .select("id") \
        .eq("token", token) \
        .eq("user_id", current_user["sub"]) \
        .is_("revoked_at", "null") \
        .execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Token not found")

    supabase.table("emergency_access_tokens") \
        .update({"revoked_at": datetime.utcnow().isoformat()}) \
        .eq("token", token) \
        .execute()


# ── GET /emergency/profile ────────────────────────────────────
@router.get("/profile", response_model=EmergencyProfileResponse)
async def get_emergency_profile(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's emergency profile."""
    result = supabase.table("emergency_profiles") \
        .select(_PROFILE_SELECT) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found")

    write_audit(current_user["sub"], "emergency_profile_viewed", "emergency_profiles", current_user["sub"])
    return _format_profile_response(result.data[0])


# ── POST /emergency/profile ───────────────────────────────────
@router.post("/profile", response_model=EmergencyProfileResponse, status_code=201)
async def create_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Create the current user's emergency profile."""
    existing = supabase.table("emergency_profiles") \
        .select("id") \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Emergency profile already exists. Use PUT to update.")

    profile_data = _merge_profile_state(payload)
    result = supabase.table("emergency_profiles").insert({
        "user_id": current_user["sub"],
        **profile_data,
    }).execute()
    write_audit(current_user["sub"], "emergency_profile_updated", "emergency_profiles", current_user["sub"])
    return _format_profile_response(result.data[0])


# ── PUT /emergency/profile ────────────────────────────────────
@router.put("/profile", response_model=EmergencyProfileResponse)
async def update_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Update the current user's emergency profile."""
    existing = supabase.table("emergency_profiles") \
        .select("*") \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Emergency profile not found. Create one first.")

    profile_data = _merge_profile_state(payload, existing.data[0])
    result = supabase.table("emergency_profiles") \
        .update(profile_data) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    write_audit(current_user["sub"], "emergency_profile_updated", "emergency_profiles", current_user["sub"])
    return _format_profile_response(result.data[0])


# ── POST /emergency/profile/upsert ───────────────────────────
@router.post("/profile/upsert", response_model=EmergencyProfileResponse)
async def upsert_emergency_profile(
    payload: EmergencyProfileUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Create or update emergency profile in one call (upsert)."""
    existing = supabase.table("emergency_profiles") \
        .select("*") \
        .eq("user_id", current_user["sub"]) \
        .execute()

    if existing.data:
        profile_data = _merge_profile_state(payload, existing.data[0])
        result = supabase.table("emergency_profiles") \
            .update(profile_data) \
            .eq("user_id", current_user["sub"]) \
            .execute()
    else:
        profile_data = _merge_profile_state(payload)
        result = supabase.table("emergency_profiles").insert({
            "user_id": current_user["sub"],
            **profile_data,
        }).execute()

    write_audit(current_user["sub"], "emergency_profile_updated", "emergency_profiles", current_user["sub"])
    return _format_profile_response(result.data[0])
