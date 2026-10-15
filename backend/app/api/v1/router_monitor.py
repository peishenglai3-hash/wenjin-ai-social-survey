"""Token usage monitoring endpoints — provides visibility into AI API costs.

All monitor endpoints require admin role to prevent sensitive cost/usage
data from being exposed to unauthorized users.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps_auth import require_admin
from app.middleware.token_logger import get_recent_usage, get_usage_summary

router = APIRouter(
    prefix="/monitor",
    tags=["monitor"],
    dependencies=[Depends(require_admin)],
)


@router.get("/tokens")
async def list_token_usage(
    hours: float = Query(24.0, description="Time window in hours"),
    limit: int = Query(100, le=500, description="Max records to return"),
):
    """Return recent token usage records (JSONL log tail).  Admin only."""
    records = get_recent_usage(hours=hours, limit=limit)
    return {
        "count": len(records),
        "hours": hours,
        "records": records,
    }


@router.get("/tokens/summary")
async def token_usage_summary(
    hours: float = Query(24.0, description="Time window in hours"),
):
    """Aggregated token usage: calls, tokens, estimated cost by model & task.  Admin only."""
    return get_usage_summary(hours=hours)
