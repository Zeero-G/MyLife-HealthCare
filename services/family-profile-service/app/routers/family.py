"""
Family Router – link/unlink family accounts, list members, manage caregiver permissions.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.core.database import supabase

router = APIRouter()


@router.post("/link")
async def link_family_member(
    linked_user_id: str,
    relationship: str,
    current_user: dict = Depends(get_current_user),
):
    """Link another user as a family member (e.g., 'parent', 'child', 'spouse')."""
    result = supabase.table("linked_accounts").insert({
        "owner_id": current_user["sub"],
        "linked_user_id": linked_user_id,
        "relationship": relationship,
    }).execute()
    return {"message": "Family member linked", "data": result.data[0]}


@router.get("/members")
async def list_family_members(current_user: dict = Depends(get_current_user)):
    result = supabase.table("linked_accounts") \
        .select("*, family_schema.family_profiles(*)") \
        .eq("owner_id", current_user["sub"]) \
        .execute()
    return result.data


@router.delete("/unlink/{linked_user_id}")
async def unlink_family_member(linked_user_id: str, current_user: dict = Depends(get_current_user)):
    supabase.table("linked_accounts") \
        .delete() \
        .eq("owner_id", current_user["sub"]) \
        .eq("linked_user_id", linked_user_id) \
        .execute()
    return {"message": "Family member unlinked"}
