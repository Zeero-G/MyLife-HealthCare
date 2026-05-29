"""Signed URL helper for AI result responses."""

from typing import Optional

from app.core.config import settings
from app.core.database import supabase


def is_storage_path(value: Optional[str]) -> bool:
    if not value:
        return False
    return not value.startswith(("http://", "https://"))


def create_signed_url(storage_path: str, expires_seconds: int = 300) -> str:
    bucket = "medical-docs"
    result = supabase.storage.from_(bucket).create_signed_url(storage_path, expires_seconds)
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or result.get("signed_url", "")
    return getattr(result, "signed_url", None) or getattr(result, "signedURL", "") or ""
