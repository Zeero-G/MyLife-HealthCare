"""
Records Router – CRUD + QR sharing for medical records.
All routes are protected by JWT (get_current_user dependency).

IMPORTANT: Specific routes (/share-qr, /family/{id}, /upload) MUST come
before the generic /{record_id} route to avoid FastAPI matching them as record IDs.
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
import httpx

from app.core.config import settings
from app.core.security import get_current_user, oauth2_scheme
from app.core.database import supabase, supabase_family
from app.core.audit import write_audit
from app.core.storage import create_signed_url, with_signed_file_url
from app.schemas.records_schemas import (
    CreateRecordRequest, UpdateRecordRequest, ShareQRRequest,
    RecordResponse, ShareQRResponse,
)

router = APIRouter()


# ── GET /records/ ─────────────────────────────────────────────
@router.get("/", response_model=list[RecordResponse])
async def list_records(current_user: dict = Depends(get_current_user)):
    result = supabase.table("medical_records") \
        .select("*") \
        .eq("user_id", current_user["sub"]) \
        .order("created_at", desc=True) \
        .execute()
    return [with_signed_file_url(r) for r in result.data]


# ── POST /records/share-qr ─────────────────────────────────── (BEFORE /{record_id})
@router.post("/share-qr", response_model=ShareQRResponse)
async def share_qr(payload: ShareQRRequest, current_user: dict = Depends(get_current_user)):
    record_check = supabase.table("medical_records") \
        .select("id") \
        .eq("id", payload.record_id) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not record_check.data:
        raise HTTPException(status_code=404, detail="Record not found")

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=payload.expires_hours)

    supabase.table("shared_records").insert({
        "record_id": payload.record_id,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "created_by": current_user["sub"],
    }).execute()

    write_audit(current_user["sub"], "record_shared", "medical_records", payload.record_id)

    share_url = f"https://mylife.vercel.app/shared/{token}"
    return ShareQRResponse(qr_token=token, share_url=share_url, expires_at=expires_at.isoformat())


# ── POST /records/upload ──────────────────────────────────── (BEFORE /{record_id})
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF/image to private Supabase Storage and trigger AI processing."""
    file_bytes = await file.read()
    file_path = f"{current_user['sub']}/{uuid.uuid4()}_{file.filename}"

    supabase.storage.from_(settings.STORAGE_BUCKET).upload(file_path, file_bytes)

    try:
        headers = {"Authorization": f"Bearer {token}"}
        if settings.INTERNAL_SERVICE_KEY:
            headers["X-Internal-Service-Key"] = settings.INTERNAL_SERVICE_KEY

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.AI_SERVICE_URL}/ai/process",
                json={"user_id": current_user["sub"], "file_url": file_path},
                headers=headers,
                timeout=10,
            )
    except Exception:
        pass

    return {
        "file_path": file_path,
        "file_url": create_signed_url(file_path),
        "message": "File uploaded. AI extraction queued.",
    }


# ── GET /records/family/{patient_id} ─────────────────────── (BEFORE /{record_id})
@router.get("/family/{patient_id}", response_model=list[RecordResponse])
async def list_family_records(patient_id: str, current_user: dict = Depends(get_current_user)):
    link_check = supabase_family.table("linked_accounts") \
        .select("*") \
        .eq("owner_id", current_user["sub"]) \
        .eq("linked_user_id", patient_id) \
        .execute()

    if not link_check.data:
        raise HTTPException(status_code=403, detail="Not authorized to view these records")

    result = supabase.table("medical_records") \
        .select("*") \
        .eq("user_id", patient_id) \
        .order("created_at", desc=True) \
        .execute()
    return [with_signed_file_url(r) for r in result.data]


# ── POST /records/ ─────────────────────────────────────────────
@router.post("/", response_model=RecordResponse, status_code=201)
async def create_record(payload: CreateRecordRequest, current_user: dict = Depends(get_current_user)):
    new_record = {
        "user_id": current_user["sub"],
        "title": payload.title,
        "record_type": payload.record_type,
        "description": payload.description,
        "doctor_name": payload.doctor_name,
        "visit_date": str(payload.visit_date) if payload.visit_date else None,
        "diagnosis": payload.diagnosis,
        "file_url": payload.file_url,
    }
    result = supabase.table("medical_records").insert(new_record).execute()
    record = result.data[0]

    write_audit(current_user["sub"], "record_created", "medical_records", record["id"])

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/notify/email",
                json={"user_id": current_user["sub"], "event": "record_created", "record_title": payload.title},
                headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
                timeout=5,
            )
    except Exception:
        pass

    return with_signed_file_url(record)


# ── GET /records/{record_id} ────────────────────────────────── (AFTER specific routes)
@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(record_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table("medical_records") \
        .select("*") \
        .eq("id", record_id) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Record not found")

    write_audit(current_user["sub"], "record_viewed", "medical_records", record_id)
    return with_signed_file_url(result.data[0])


# ── PUT /records/{record_id} ───────────────────────────────────
@router.put("/{record_id}", response_model=RecordResponse)
async def update_record(record_id: str, payload: UpdateRecordRequest, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = supabase.table("medical_records") \
        .update(update_data) \
        .eq("id", record_id) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Record not found")

    write_audit(current_user["sub"], "record_updated", "medical_records", record_id)
    return with_signed_file_url(result.data[0])


# ── DELETE /records/{record_id} ───────────────────────────────
@router.delete("/{record_id}", status_code=204)
async def delete_record(record_id: str, current_user: dict = Depends(get_current_user)):
    check = supabase.table("medical_records") \
        .select("id") \
        .eq("id", record_id) \
        .eq("user_id", current_user["sub"]) \
        .execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Record not found or not owned by you")

    supabase.table("medical_records") \
        .delete() \
        .eq("id", record_id) \
        .eq("user_id", current_user["sub"]) \
        .execute()

    write_audit(current_user["sub"], "record_deleted", "medical_records", record_id)
