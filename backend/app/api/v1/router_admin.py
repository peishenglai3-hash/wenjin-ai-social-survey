"""Admin user management API — search, list, promote, demote users.

Protected by require_admin dependency — only admins can access.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import require_admin
from app.core.database import get_db
from app.models.user import UserAccount

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Schemas ────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    is_active: bool
    phone: str | None = None

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    total: int
    users: list[UserOut]


class PromoteRequest(BaseModel):
    role: str  # "admin" or "researcher"


# ── Routes ──────────────────────────────────────────────────────────────

@router.get("/users", response_model=UserListOut)
async def search_users(
    search: str = Query(default="", description="Fuzzy search by name, email, or phone"),
    db: AsyncSession = Depends(get_db),
    _admin: UserAccount = Depends(require_admin),
):
    """Search users by display_name / email / phone. Empty search returns all users."""
    query = select(UserAccount)

    if search.strip():
        like = f"%{search.strip()}%"
        query = query.where(
            (UserAccount.display_name.ilike(like))
            | (UserAccount.email.ilike(like))
            | (UserAccount.phone.ilike(like))
        )

    # Count total matching
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    result = await db.execute(query.order_by(UserAccount.id))
    users = result.scalars().all()

    return UserListOut(
        total=total,
        users=[UserOut.model_validate(u) for u in users],
    )


@router.put("/users/{user_id}/role")
async def set_user_role(
    user_id: int,
    body: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    _admin: UserAccount = Depends(require_admin),
):
    """Promote or demote a user. Role must be 'admin' or 'researcher'."""
    if body.role not in ("admin", "researcher"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'researcher'",
        )

    result = await db.execute(select(UserAccount).where(UserAccount.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_role = user.role
    user.role = body.role
    await db.commit()
    await db.refresh(user)

    return {
        "ok": True,
        "user_id": user.id,
        "display_name": user.display_name,
        "email": user.email,
        "old_role": old_role,
        "new_role": user.role,
    }
