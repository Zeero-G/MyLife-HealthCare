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


@router.post("/process", response_model=AIResultResponse, status_code=202)
async def process_document(payload: ProcessRequest):
    """
    Accepts a medical document URL, sends it to Claude API for extraction,
    stores the result, and notifies the patient.
    """
    # Store initial record
    doc_id = str(uuid.uuid4())
    supabase.table("ai_schema.uploaded_documents").insert({
        "id": doc_id,
        "user_id": payload.user_id,
        "file_url": payload.file_url,
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
                    "content": f"{EXTRACTION_PROMPT}\n\nDocument URL: {payload.file_url}",
                }
            ],
        )
        import json
        raw_text = message.content[0].text
        extracted = json.loads(raw_text)
        confidence = extracted.pop("confidence_score", 0.85)

        # Save to extracted_reports
        supabase.table("ai_schema.extracted_reports").insert({
            "document_id": doc_id,
            "user_id": payload.user_id,
            "extracted_data": extracted,
            "confidence_score": confidence,
        }).execute()

        # Update document status
        supabase.table("ai_schema.uploaded_documents") \
            .update({"status": "completed"}) \
            .eq("id", doc_id) \
            .execute()

        # Notify patient
        try:
            async with httpx.AsyncClient() as http:
                await http.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/notify/email",
                    json={"user_id": payload.user_id, "event": "ai_extraction_complete"},
                    timeout=5,
                )
        except Exception:
            pass

        return AIResultResponse(
            id=doc_id, user_id=payload.user_id, file_url=payload.file_url,
            extracted_data=extracted, confidence_score=confidence, status="completed",
        )

    except Exception as e:
        supabase.table("ai_schema.uploaded_documents") \
            .update({"status": "failed"}) \
            .eq("id", doc_id) \
            .execute()
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {str(e)}")


@router.get("/results/{doc_id}", response_model=AIResultResponse)
async def get_result(doc_id: str):
    result = supabase.table("ai_schema.extracted_reports") \
        .select("*") \
        .eq("document_id", doc_id) \
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Extraction result not found")
    r = result.data[0]
    return AIResultResponse(
        id=doc_id, user_id=r["user_id"], file_url="",
        extracted_data=r["extracted_data"], confidence_score=r["confidence_score"], status="completed",
    )


@router.get("/summary")
async def get_summary(user_id: str):
    """Returns all extraction results for a given user."""
    result = supabase.table("ai_schema.extracted_reports") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    return result.data
