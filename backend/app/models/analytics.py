"""
Analytics event model — lightweight telemetry for product improvement.

Table: analytics_events
  id          — auto-increment primary key
  event_name  — e.g. page_view, search, gap_analysis
  properties  — JSON dict with arbitrary payload
  user_id     — nullable FK to user_accounts
  session_id  — browser session UUID
  created_at  — server timestamp
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    properties: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
