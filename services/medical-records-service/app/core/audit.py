"""Append-only audit log writes (medical_schema.audit_log)."""

from typing import Optional

from app.core.database import supabase


def write_audit(
    user_id: Optional[str],
    action: str,
    table_name: str,
    record_id: Optional[str] = None,
) -> None:
    try:
        supabase.table("audit_log").insert({
            "user_id": user_id,
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
        }).execute()
    except Exception:
        pass
