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


class MedicalInfoStatus(str, Enum):
    UNKNOWN = "unknown"
    NONE = "none"
    HAS_ITEMS = "has_items"


class EmergencyContact(BaseModel):
    name: str
    phone: str
    relationship: Optional[str] = None
    priority: int = 1
    notes: Optional[str] = None


class EmergencyProfileUpsert(BaseModel):
    blood_type: Optional[str] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    allergies_status: Optional[MedicalInfoStatus] = None
    conditions_status: Optional[MedicalInfoStatus] = None
    medications_status: Optional[MedicalInfoStatus] = None
    show_emergency_contacts_publicly: Optional[bool] = None


class EmergencyProfileResponse(BaseModel):
    user_id: str
    blood_type: Optional[str]
    allergies: List[str]
    chronic_conditions: List[str]
    current_medications: List[str]
    emergency_contacts: List[EmergencyContact] = []
    allergies_status: MedicalInfoStatus = MedicalInfoStatus.UNKNOWN
    conditions_status: MedicalInfoStatus = MedicalInfoStatus.UNKNOWN
    medications_status: MedicalInfoStatus = MedicalInfoStatus.UNKNOWN
    last_confirmed_at: Optional[str] = None
    show_emergency_contacts_publicly: bool = False
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class EmergencyPublicProfileResponse(BaseModel):
    blood_type: Optional[str]
    allergies_status: MedicalInfoStatus
    allergies: List[str]
    conditions_status: MedicalInfoStatus
    chronic_conditions: List[str]
    medications_status: MedicalInfoStatus
    current_medications: List[str]
    last_confirmed_at: Optional[str] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
