"""
Family Router – link/unlink family accounts, list members with user details.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.core.database import supabase, supabase_auth

router = APIRouter()


@router.post("/link")
async def link_family_member(
    linked_user_id: str,
    relationship: str,
    current_user: dict = Depends(get_current_user),
):
    """Link another user as a family member (e.g., 'parent', 'child', 'spouse')."""
    # Verify the target user exists
    user_check = supabase_auth.table("users") \
        .select("id, full_name, email, role, gender") \
        .eq("id", linked_user_id) \
        .execute()
    if not user_check.data:
        raise HTTPException(status_code=404, detail="User not found. Please check the ID.")

    # Prevent self-linking
    if linked_user_id == current_user["sub"]:
        raise HTTPException(status_code=400, detail="Cannot link yourself as a family member.")

    # Check if already linked
    existing = supabase.table("linked_accounts") \
        .select("id") \
        .eq("owner_id", current_user["sub"]) \
        .eq("linked_user_id", linked_user_id) \
        .execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="This user is already linked as a family member.")

    result = supabase.table("linked_accounts").insert({
        "owner_id": current_user["sub"],
        "linked_user_id": linked_user_id,
        "relationship": relationship,
    }).execute()

    linked_user = user_check.data[0]
    return {
        "message": "Family member linked",
        "data": {
            **result.data[0],
            "full_name": linked_user["full_name"],
            "email": linked_user["email"],
            "role": linked_user["role"],
            "gender": linked_user.get("gender"),
        }
    }


@router.get("/members")
async def list_family_members(current_user: dict = Depends(get_current_user)):
    """Returns all linked family members with their user details (name, email, gender)."""
    # Get all linked accounts
    links = supabase.table("linked_accounts") \
        .select("*") \
        .eq("owner_id", current_user["sub"]) \
        .execute()

    if not links.data:
        return []

    # Fetch user details for each linked member
    enriched = []
    for link in links.data:
        user_data = supabase_auth.table("users") \
            .select("id, full_name, email, role, gender") \
            .eq("id", link["linked_user_id"]) \
            .execute()
        
        user_info = user_data.data[0] if user_data.data else {}
        enriched.append({
            "id": link.get("id"),
            "owner_id": link["owner_id"],
            "linked_user_id": link["linked_user_id"],
            "relationship": link["relationship"],
            "created_at": link.get("created_at"),
            # Enriched user details:
            "full_name": user_info.get("full_name", "Unknown"),
            "email": user_info.get("email", ""),
            "role": user_info.get("role", ""),
            "gender": user_info.get("gender"),
        })

    return enriched


@router.delete("/unlink/{linked_user_id}")
async def unlink_family_member(linked_user_id: str, current_user: dict = Depends(get_current_user)):
    supabase.table("linked_accounts") \
        .delete() \
        .eq("owner_id", current_user["sub"]) \
        .eq("linked_user_id", linked_user_id) \
        .execute()
    return {"message": "Family member unlinked"}
