"""Private Supabase Storage helpers — signed URLs instead of public links."""

from typing import Any, Optional

from app.core.config import settings
from app.core.database import supabase


def is_storage_path(value: Optional[str]) -> bool:
    if not value:
        return False
    return not value.startswith(("http://", "https://"))


def create_signed_url(storage_path: str, expires_seconds: Optional[int] = None) -> str:
    ttl = expires_seconds or settings.STORAGE_SIGNED_URL_SECONDS
    result = supabase.storage.from_(settings.STORAGE_BUCKET).create_signed_url(
        storage_path,
        ttl,
    )
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or result.get("signed_url", "")
    signed = getattr(result, "signed_url", None) or getattr(result, "signedURL", None)
    return signed or ""


def with_signed_file_url(record: dict[str, Any], expires_seconds: Optional[int] = None) -> dict[str, Any]:
    out = dict(record)
    file_ref = out.get("file_url")
    if is_storage_path(file_ref):
        out["file_url"] = create_signed_url(file_ref, expires_seconds)
    return out
