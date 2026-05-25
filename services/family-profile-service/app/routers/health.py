"""
Women's Health Router – menstrual cycle and pregnancy tracking.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.core.security import get_current_user
from app.core.database import supabase

router = APIRouter()


class CycleRequest(BaseModel):
    start_date: date
    end_date: Optional[date] = None
    cycle_length: Optional[int] = None
    notes: Optional[str] = None


class PregnancyRequest(BaseModel):
    lmp_date: date   # Last menstrual period
    due_date: Optional[date] = None
    notes: Optional[str] = None


@router.post("/cycle")
async def log_cycle(payload: CycleRequest, current_user: dict = Depends(get_current_user)):
    result = supabase.table("menstrual_cycles").insert({
        "user_id": current_user["sub"],
        "start_date": str(payload.start_date),
        "end_date": str(payload.end_date) if payload.end_date else None,
        "cycle_length": payload.cycle_length,
        "notes": payload.notes,
    }).execute()
    return result.data[0]


@router.get("/cycle")
async def get_cycle_history(current_user: dict = Depends(get_current_user)):
    result = supabase.table("menstrual_cycles") \
        .select("*") \
        .eq("user_id", current_user["sub"]) \
        .order("start_date", desc=True) \
        .execute()
    return result.data


@router.post("/pregnancy")
async def log_pregnancy(payload: PregnancyRequest, current_user: dict = Depends(get_current_user)):
    result = supabase.table("pregnancy_records").insert({
        "user_id": current_user["sub"],
        "lmp_date": str(payload.lmp_date),
        "due_date": str(payload.due_date) if payload.due_date else None,
        "notes": payload.notes,
    }).execute()
    return result.data[0]


@router.get("/pregnancy")
async def get_pregnancy_records(current_user: dict = Depends(get_current_user)):
    result = supabase.table("pregnancy_records") \
        .select("*") \
        .eq("user_id", current_user["sub"]) \
        .execute()
    return result.data
