"""Create an administrator account from explicit deployment environment values.

This script intentionally has no default email or password. Do not pass either
value on a command line where it can be captured by shell history or process
inspection; inject them through a protected environment mechanism instead.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.security import hash_password
from app.models.user import UserAccount
from app.core.database import async_session_factory
from sqlalchemy import select


ADMIN_EMAIL = os.environ.get("ADMIN_INIT_EMAIL", "").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_INIT_PASSWORD", "")
ADMIN_DISPLAY_NAME = os.environ.get("ADMIN_INIT_DISPLAY_NAME", "Administrator").strip()


def validate_admin_inputs() -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_INIT_EMAIL and ADMIN_INIT_PASSWORD must be set")
    if len(ADMIN_PASSWORD) < 12:
        raise RuntimeError("ADMIN_INIT_PASSWORD must contain at least 12 characters")


async def create_admin():
    validate_admin_inputs()
    async with async_session_factory() as session:
        result = await session.execute(
            select(UserAccount).where(UserAccount.email == ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print("An account with that email already exists; no changes made.")
            return

        admin = UserAccount(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            display_name=ADMIN_DISPLAY_NAME or "Administrator",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print("Administrator account created. Remove the initialization secrets now.")


if __name__ == "__main__":
    asyncio.run(create_admin())
