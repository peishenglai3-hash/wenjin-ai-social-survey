"""
Analytics endpoints — lightweight telemetry.

POST /api/v1/analytics/events  — Ingest events (public, no auth required)
GET  /api/v1/analytics/stats   — Aggregate stats (admin only)
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import require_admin
from app.core.database import get_db
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class AnalyticsEventPayload(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=100)
    properties: dict = Field(default_factory=dict)
    session_id: str | None = Field(None, max_length=64)
    timestamp: str | None = Field(None, description="ISO-8601 client timestamp")


class BatchEventsPayload(BaseModel):
    events: list[AnalyticsEventPayload] = Field(..., max_length=100)


@router.post("/events")
async def ingest_events(
    payload: BatchEventsPayload,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a batch of analytics events from the frontend.

    This endpoint is intentionally public (no auth) to avoid blocking
    telemetry with 401 responses. Events include a session_id for
    correlation but no PII.
    """
    svc = AnalyticsService(db)
    raw_events = [
        {
            "event_name": e.event_name,
            "properties": e.properties,
            "session_id": e.session_id,
        }
        for e in payload.events
    ]
    result = await svc.log_events_batch(raw_events)
    logger.debug("Analytics batch: accepted=%d rejected=%d", result["accepted"], result["rejected"])
    return result


@router.get("/stats")
async def get_stats(
    days: int = 30,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate analytics stats (admin only)."""
    svc = AnalyticsService(db)
    return await svc.get_stats(days=days)
