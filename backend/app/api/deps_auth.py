"""Authentication dependency for FastAPI routes.

Provides:
  get_current_user   — extract JWT, return UserAccount or None
  require_user       — enforce authentication (401 if missing)
  require_admin      — enforce admin role (403 if not admin)
  get_current_profile — resolve UserProfile from authenticated user (auto-create)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import UserAccount, UserAuthMethod
from app.models.survey import UserProfile

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserAccount | None:
    """Extract and validate the current user from JWT.

    Returns None if no token is provided (allows optional auth).
    Raises 401 if token is invalid or user not found.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(UserAccount)
        .where(UserAccount.id == int(user_id))
        .options(selectinload(UserAccount.auth_methods))
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def require_user(
    user: UserAccount | None = Depends(get_current_user),
) -> UserAccount:
    """Require a valid authenticated user. Raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


async def require_admin(
    user: UserAccount = Depends(require_user),
) -> UserAccount:
    """Require an admin user. Raises 403 if not admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def get_current_profile(
    user: UserAccount = Depends(require_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Resolve the UserProfile for the currently authenticated user.

    Auto-creates a default profile if none exists yet (e.g. for
    accounts created before the UserAccount↔UserProfile link was added,
    or admin-created accounts).
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile
