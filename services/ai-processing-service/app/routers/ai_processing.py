"""
AI Processing Router – accepts document URLs, calls Claude API, stores structured results.
"""

import uuid
import anthropic
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx

from app.core.config import settings
from app.core.database import supabase
from app.core.security import require_user_or_internal, get_current_user
from app.core.storage import is_storage_path, create_signed_url

router = APIRouter()


class ProcessRequest(BaseModel):
    user_id: str
    file_url: str


class AIResultResponse(BaseModel):
    id: str
    user_id: str
    file_url: str
    extracted_data: dict
    confidence_score: Optional[float]
    status: str


EXTRACTION_PROMPT = """
You are a medical document analysis assistant.
Analyze the medical document from the provided URL and extract the following structured data:
- Patient name and demographics (if present)
- Diagnosis / conditions
- Medications prescribed (name, dosage, frequency)
- Lab results (test name, value, unit, reference range)
- Doctor name and hospital/clinic
- Visit date
- Any allergies mentioned
- Follow-up instructions

Return a valid JSON object with these fields. Use null for missing fields.
Provide a confidence_score (0.0-1.0) based on document clarity.
"""


def _resolve_file_url_for_response(doc_id: str, stored_url: str) -> str:
    if stored_url and is_storage_path(stored_url):
        return create_signed_url(stored_url, 300)
    if not stored_url:
        doc = supabase.table("uploaded_documents").select("file_url").eq("id", doc_id).execute()
        if doc.data:
            ref = doc.data[0].get("file_url", "")
            if is_storage_path(ref):
                return create_signed_url(ref, 300)
            return ref or ""
    return stored_url or ""


@router.post("/process", response_model=AIResultResponse, status_code=202)
async def process_document(
    payload: ProcessRequest,
    actor: dict = Depends(require_user_or_internal),
):
    """
    Accepts a medical document URL, sends it to Claude API for extraction,
    stores the result, and notifies the patient.
    """
    if actor.get("auth_type") == "user" and actor.get("sub") != payload.user_id:
        raise HTTPException(status_code=403, detail="Cannot process documents for another user")

    # Store storage path when possible; signed URLs are resolved at read time
    stored_file_ref = payload.file_url
    if is_storage_path(stored_file_ref):
        ai_file_url = create_signed_url(stored_file_ref, 3600)
    else:
        ai_file_url = payload.file_url

    doc_id = str(uuid.uuid4())
    supabase.table("uploaded_documents").insert({
        "id": doc_id,
        "user_id": payload.user_id,
        "file_url": stored_file_ref,
        "status": "processing",
    }).execute()

    try:
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"{EXTRACTION_PROMPT}\n\nDocument URL: {ai_file_url}",
                }
            ],
        )
        import json
        raw_text = message.content[0].text
        extracted = json.loads(raw_text)
        confidence = extracted.pop("confidence_score", 0.85)

        supabase.table("extracted_reports").insert({
            "document_id": doc_id,
            "user_id": payload.user_id,
            "extracted_data": extracted,
            "confidence_score": confidence,
        }).execute()

        supabase.table("uploaded_documents") \
            .update({"status": "completed"}) \
            .eq("id", doc_id) \
            .execute()

        try:
            async with httpx.AsyncClient() as http:
                await http.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/notify/email",
                    json={"user_id": payload.user_id, "event": "ai_extraction_complete"},
                    headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
                    timeout=5,
                )
        except Exception:
            pass

        return AIResultResponse(
            id=doc_id,
            user_id=payload.user_id,
            file_url=_resolve_file_url_for_response(doc_id, stored_file_ref),
            extracted_data=extracted,
            confidence_score=confidence,
            status="completed",
        )

    except Exception as e:
        supabase.table("uploaded_documents") \
            .update({"status": "failed"}) \
            .eq("id", doc_id) \
            .execute()
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {str(e)}")


@router.get("/results/{doc_id}", response_model=AIResultResponse)
async def get_result(doc_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table("extracted_reports") \
        .select("*") \
        .eq("document_id", doc_id) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Extraction result not found")

    r = result.data[0]
    if r["user_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this result")

    return AIResultResponse(
        id=doc_id,
        user_id=r["user_id"],
        file_url=_resolve_file_url_for_response(doc_id, ""),
        extracted_data=r["extracted_data"],
        confidence_score=r["confidence_score"],
        status="completed",
    )


@router.get("/summary")
async def get_summary(current_user: dict = Depends(get_current_user)):
    """Returns extraction results for the authenticated user only."""
    result = supabase.table("extracted_reports") \
        .select("*") \
        .eq("user_id", current_user["sub"]) \
        .order("created_at", desc=True) \
        .execute()
    return result.data
