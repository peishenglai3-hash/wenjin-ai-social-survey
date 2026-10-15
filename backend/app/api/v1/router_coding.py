"""Coding endpoints — codebook CRUD, AI coding suggestions, inter-coder reliability."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ai_service, get_db
from app.services.ai import AIService
from app.services.codebook_service import (
    create_code, list_codes, update_code, delete_code,
    suggest_codes, assign_code, list_assignments, delete_assignment,
    calculate_intercoder_reliability, export_codebook, create_version_snapshot,
)

router = APIRouter(prefix="/coding", tags=["coding"])


@router.get("/codebooks/{project_id}")
async def get_codebook(project_id: int, paradigm: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    codes = await list_codes(db, project_id, paradigm=paradigm)
    return {
        "codes": [
            {"id": c.id, "name": c.name, "definition": c.definition,
             "example": c.example, "exclusion_criteria": c.exclusion_criteria,
             "parent_code_id": c.parent_code_id, "paradigm": c.paradigm,
             "color": c.color, "sort_order": c.sort_order, "version": c.version,
             "created_at": str(c.created_at) if c.created_at else None}
            for c in codes
        ], "total": len(codes),
    }


@router.post("/codebooks/{project_id}/codes")
async def add_code(project_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    code = await create_code(
        db, project_id, name=payload.get("name", ""),
        definition=payload.get("definition", ""),
        example=payload.get("example", ""),
        exclusion_criteria=payload.get("exclusion_criteria", ""),
        parent_code_id=payload.get("parent_code_id"),
        paradigm=payload.get("paradigm", "thematic_analysis"),
        color=payload.get("color", ""),
        created_by_profile_id=payload.get("created_by_profile_id"),
    )
    return {"id": code.id, "name": code.name, "paradigm": code.paradigm}


@router.patch("/codebooks/codes/{code_id}")
async def edit_code(code_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    code = await update_code(db, code_id, **payload)
    if code is None:
        return {"error": "Code not found"}
    return {"id": code.id, "name": code.name, "definition": code.definition}


@router.delete("/codebooks/codes/{code_id}")
async def remove_code(code_id: int, db: AsyncSession = Depends(get_db)):
    ok = await delete_code(db, code_id)
    if not ok:
        return {"error": "Code not found"}
    return {"deleted": True, "id": code_id}


@router.post("/suggest")
async def ai_suggest_codes(payload: dict, db: AsyncSession = Depends(get_db), ai: AIService = Depends(get_ai_service)):
    transcript = payload.get("transcript", "")
    research_question = payload.get("research_question", "")
    project_id = payload.get("project_id", 0)
    coding_paradigm = payload.get("coding_paradigm", "auto")
    suggestions = await suggest_codes(db, ai, transcript, research_question, project_id, coding_paradigm)
    return {"suggestions": suggestions, "count": len(suggestions)}


@router.post("/assign")
async def create_assignment(payload: dict, db: AsyncSession = Depends(get_db)):
    a = await assign_code(
        db, code_id=payload.get("code_id", 0), session_id=payload.get("session_id", 0),
        span_start=payload.get("span_start", 0), span_end=payload.get("span_end", 0),
        quote_text=payload.get("quote_text", ""),
        coder_profile_id=payload.get("coder_profile_id"),
        is_ai_suggested=payload.get("is_ai_suggested", False),
        confidence=payload.get("confidence", 0.5),
    )
    return {"id": a.id, "code_id": a.code_id, "session_id": a.session_id}


@router.get("/assignments/{session_id}")
async def get_assignments(session_id: int, db: AsyncSession = Depends(get_db)):
    assignments = await list_assignments(db, session_id)
    return {
        "assignments": [
            {"id": a.id, "code_id": a.code_id, "session_id": a.session_id,
             "span_start": a.span_start, "span_end": a.span_end,
             "quote_text": a.quote_text, "coder_profile_id": a.coder_profile_id,
             "is_ai_suggested": a.is_ai_suggested, "confidence": a.confidence}
            for a in assignments
        ], "total": len(assignments),
    }


@router.delete("/assignments/{assignment_id}")
async def remove_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    ok = await delete_assignment(db, assignment_id)
    if not ok:
        return {"error": "Assignment not found"}
    return {"deleted": True, "id": assignment_id}


@router.get("/reliability/{session_id}")
async def get_reliability(session_id: int, db: AsyncSession = Depends(get_db)):
    return await calculate_intercoder_reliability(db, session_id)


@router.get("/export/{project_id}")
async def export_codebook_endpoint(project_id: int, fmt: str = Query("markdown"), db: AsyncSession = Depends(get_db)):
    from fastapi.responses import PlainTextResponse
    result = await export_codebook(db, project_id, fmt=fmt)
    media = "application/json" if fmt == "json" else "text/markdown; charset=utf-8"
    return PlainTextResponse(content=result, media_type=media)


@router.post("/versions/{project_id}")
async def snapshot_codebook(project_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    version = await create_version_snapshot(
        db, project_id,
        created_by_profile_id=payload.get("created_by_profile_id"),
        changelog=payload.get("changelog", ""),
    )
    return {"id": version.id, "version_number": version.version_number, "changelog": version.changelog}
