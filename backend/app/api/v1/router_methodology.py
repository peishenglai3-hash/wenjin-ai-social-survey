"""
P1 — Methodology matching API endpoints.

POST /api/v1/methodology/match    — Match research question to methodology
GET  /api/v1/methodology/tags     — List available methodology tags
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.methodology_matcher import get_methodology_matcher

router = APIRouter(prefix="/methodology", tags=["Methodology Matching"])


class MatchRequest(BaseModel):
    research_question: str = Field(..., min_length=5)
    paradigm_preference: str = Field("qualitative")
    field_conditions: dict | None = Field(None)


@router.post("/match")
async def match_methodology(payload: MatchRequest):
    """Match a research question to recommended methodology combination.

    Returns the methodology trinity: primary/secondary methods,
    sampling strategy with sample size estimates, instruments,
    validity strategies, ethical considerations, and caveats.
    """
    matcher = get_methodology_matcher()
    result = matcher.match(
        research_question=payload.research_question,
        paradigm_preference=payload.paradigm_preference,
        field_conditions=payload.field_conditions,
    )
    return result.to_dict()


@router.get("/tags")
async def list_methodology_tags():
    """List available methodology tags for UI filter display."""
    matcher = get_methodology_matcher()
    return {"tags": matcher.list_available_tags()}


@router.get("/quick")
async def quick_match(
    q: str = Query(..., min_length=5),
    paradigm: str = Query("qualitative"),
):
    """Quick GET-based methodology match (convenience endpoint)."""
    matcher = get_methodology_matcher()
    result = matcher.match(research_question=q, paradigm_preference=paradigm)
    return result.to_dict()
