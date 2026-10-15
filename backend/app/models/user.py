"""User account model for authentication.

UserAccount handles core identity.  Each account has one UserProfile
(survey persona) linked via user_profile.user_id → user_accounts.id.

Multi-method authentication: UserAuthMethod allows one user to have
multiple login methods (email+password, phone+SMS, WeChat OAuth, etc.)
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.survey import UserProfile


class UserAccount(Base, TimestampMixin):
    """Core identity — one user, potentially many auth methods."""

    __tablename__ = "user_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), default="")
    role: Mapped[str] = mapped_column(String(20), default="researcher")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # ── NEW: Multi-method auth fields ──
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, default=None)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, default=None)
    wechat_unionid: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    real_name_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── 1:1 link to survey persona ──
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # ── 1:N link to auth methods (future extensibility) ──
    auth_methods: Mapped[list["UserAuthMethod"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserAuthMethod(Base, TimestampMixin):
    """One authentication method belonging to a user.

    Examples:
      - auth_type='email', identifier='researcher@example.invalid', credential=<bcrypt>
      - auth_type='phone', identifier='+8613800138000', credential=NULL
      - auth_type='wechat', identifier='oUpF8uMuAJ...', credential=NULL
    """

    __tablename__ = "user_auth_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    auth_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="email | phone | wechat | qq"
    )
    identifier: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="email address / phone number / openid"
    )
    credential: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="bcrypt hash for password; NULL for OAuth"
    )
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    last_used_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True, default=None)

    user: Mapped["UserAccount"] = relationship(back_populates="auth_methods")
