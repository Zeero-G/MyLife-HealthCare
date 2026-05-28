"""
Notification Router – email and push notifications for key platform events.
Called directly by other microservices with an internal service key.
"""

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings
from app.core.database import supabase, supabase_auth
from app.core.security import require_internal_service

router = APIRouter(dependencies=[Depends(require_internal_service)])

# Firebase Admin SDK init (only once)
firebase_initialized = False
try:
    firebase_admin.get_app()
    firebase_initialized = True
except ValueError:
    if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        firebase_initialized = True


# ── Schemas ──────────────────────────────────────────────

class EmailRequest(BaseModel):
    user_id: str
    event: str                        # e.g. "record_created", "ai_extraction_complete"
    record_title: Optional[str] = None


class PushRequest(BaseModel):
    user_id: str
    title: str
    body: str
    fcm_token: Optional[str] = None   # If not provided, look up from DB


class ReminderRequest(BaseModel):
    user_id: str
    reminder_type: str                # e.g. "appointment", "medication"
    scheduled_at: str                 # ISO datetime


# ── Event → message map ──────────────────────────────────

EVENT_MESSAGES = {
    "record_created": ("✅ Record Uploaded", "Your medical record '{title}' has been saved to MYLIFE."),
    "ai_extraction_complete": ("🤖 AI Extraction Done", "Your medical document has been analysed. View your records."),
    "sos_alert": ("🚨 SOS Alert", "An emergency alert has been triggered for your account."),
    "verification": ("🔑 Verify Your Email", "Welcome to MYLIFE! Please verify your email address."),
}


# ── Helpers ──────────────────────────────────────────────

async def send_email_via_supabase(to_email: str, subject: str, body: str):
    """Send transactional email via Supabase Edge Function or SMTP."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.SUPABASE_URL}/functions/v1/send-email",
            headers={"Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"},
            json={"to": to_email, "subject": subject, "body": body},
            timeout=10,
        )


def send_push_notification(fcm_token: str, title: str, body: str):
    if not firebase_initialized:
        raise HTTPException(status_code=503, detail="Firebase credentials are not configured")

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=fcm_token,
    )
    messaging.send(message)


# ── Endpoints ────────────────────────────────────────────

@router.post("/email")
async def send_email_notification(payload: EmailRequest):
    # Fetch user email from DB
    user = supabase_auth.table("users").select("email, full_name").eq("id", payload.user_id).execute()
    if not user.data:
        return {"error": "User not found"}

    email = user.data[0]["email"]
    subject_template, body_template = EVENT_MESSAGES.get(
        payload.event, ("MYLIFE Notification", "You have a new notification from MYLIFE.")
    )
    body = body_template.replace("{title}", payload.record_title or "")

    await send_email_via_supabase(email, subject_template, body)

    # Log notification
    supabase.table("notification_logs").insert({
        "user_id": payload.user_id,
        "channel": "email",
        "event": payload.event,
        "status": "sent",
    }).execute()

    return {"message": "Email sent"}


@router.post("/push")
async def send_push(payload: PushRequest):
    fcm_token = payload.fcm_token
    if not fcm_token:
        # Look up FCM token from DB
        result = supabase.table("notifications").select("fcm_token").eq("user_id", payload.user_id).execute()
        if result.data:
            fcm_token = result.data[0].get("fcm_token")

    if fcm_token:
        send_push_notification(fcm_token, payload.title, payload.body)

    supabase.table("notification_logs").insert({
        "user_id": payload.user_id,
        "channel": "push",
        "event": "manual_push",
        "status": "sent" if fcm_token else "no_token",
    }).execute()

    return {"message": "Push notification processed"}


@router.post("/reminder")
async def schedule_reminder(payload: ReminderRequest):
    supabase.table("notifications").insert({
        "user_id": payload.user_id,
        "reminder_type": payload.reminder_type,
        "scheduled_at": payload.scheduled_at,
        "status": "pending",
    }).execute()
    return {"message": "Reminder scheduled"}
