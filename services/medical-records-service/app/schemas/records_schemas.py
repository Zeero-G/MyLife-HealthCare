from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from enum import Enum


class RecordType(str, Enum):
    DIAGNOSIS = "diagnosis"
    LAB = "lab"
    PRESCRIPTION = "prescription"
    IMAGING = "imaging"
    OTHER = "other"


# ── Requests ──

class CreateRecordRequest(BaseModel):
    title: str
    record_type: RecordType
    description: Optional[str] = None
    doctor_name: Optional[str] = None
    visit_date: Optional[date] = None
    diagnosis: Optional[str] = None
    file_url: Optional[str] = None


class UpdateRecordRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    doctor_name: Optional[str] = None
    diagnosis: Optional[str] = None


class ShareQRRequest(BaseModel):
    record_id: str
    expires_hours: int = 24     # QR link valid for N hours


# ── Responses ──

class RecordResponse(BaseModel):
    id: str
    user_id: str
    title: str
    record_type: RecordType
    description: Optional[str]
    doctor_name: Optional[str]
    visit_date: Optional[date]
    diagnosis: Optional[str]
    file_url: Optional[str]
    created_at: str


class ShareQRResponse(BaseModel):
    qr_token: str
    share_url: str
    expires_at: str


class EmergencyProfileResponse(BaseModel):
    user_id: str
    blood_type: Optional[str]
    allergies: List[str]
    chronic_conditions: List[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    current_medications: List[str]
