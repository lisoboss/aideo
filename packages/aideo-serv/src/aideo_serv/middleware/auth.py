"""JWT authentication middleware skeleton (reserved for future use)."""

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


class AnonymousUser:
    """Placeholder user for unauthenticated requests."""

    is_authenticated = False
    username = "anonymous"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AnonymousUser:
    """Return the current user (always anonymous in MVP)."""
    return AnonymousUser()
