from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_internal_service(
    internal_key: Optional[str] = Header(default=None, alias="X-Internal-Service-Key"),
) -> bool:
    if not settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal service key is not configured",
        )

    if internal_key != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
        )

    return True
