"""
Codebook Service — CRUD for qualitative coding codebooks + AI-assisted coding.

Manages: CodebookCode (hierarchical codes), CodingAssignment (code-text links),
and CodebookVersion (historical snapshots).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import CodebookCode, CodingAssignment, CodebookVersion

if TYPE_CHECKING:
    from app.services.ai import AIService

logger = logging.getLogger(__name__)

COLOUR_PALETTE = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#06B6D4", "#F97316", "#6366F1", "#14B8A6",
    "#E11D48", "#0EA5E9", "#84CC16", "#A855F7", "#78716C",
]


async def _count_codes(db: AsyncSession, project_id: int) -> int:
    result = await db.execute(
        select(func.count(CodebookCode.id)).where(CodebookCode.project_id == project_id)
    )
    return result.scalar() or 0


async def create_code(
    db: AsyncSession, project_id: int, name: str,
    definition: str = "", example: str = "", exclusion_criteria: str = "",
    parent_code_id: int | None = None, paradigm: str = "thematic_analysis",
    color: str = "", created_by_profile_id: int | None = None,
) -> CodebookCode:
    if not color:
        existing_count = await _count_codes(db, project_id)
        color = COLOUR_PALETTE[existing_count % len(COLOUR_PALETTE)]
    code = CodebookCode(
        project_id=project_id, name=name, definition=definition,
        example=example, exclusion_criteria=exclusion_criteria,
        parent_code_id=parent_code_id, paradigm=paradigm, color=color,
        sort_order=await _count_codes(db, project_id),
        created_by_profile_id=created_by_profile_id,
    )
    db.add(code)
    await db.commit()
    await db.refresh(code)
    return code


async def list_codes(db: AsyncSession, project_id: int, paradigm: str | None = None) -> list[CodebookCode]:
    stmt = select(CodebookCode).where(CodebookCode.project_id == project_id)
    if paradigm:
        stmt = stmt.where(CodebookCode.paradigm == paradigm)
    stmt = stmt.order_by(CodebookCode.sort_order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_code(db: AsyncSession, code_id: int, **fields) -> CodebookCode | None:
    result = await db.execute(select(CodebookCode).where(CodebookCode.id == code_id))
    code = result.scalar_one_or_none()
    if code is None:
        return None
    for key, val in fields.items():
        if hasattr(code, key):
            setattr(code, key, val)
    await db.commit()
    await db.refresh(code)
    return code


async def delete_code(db: AsyncSession, code_id: int) -> bool:
    result = await db.execute(select(CodebookCode).where(CodebookCode.id == code_id))
    code = result.scalar_one_or_none()
    if code is None:
        return False
    await db.delete(code)
    await db.commit()
    return True


async def suggest_codes(
    db: AsyncSession, ai: "AIService", transcript: str,
    research_question: str, project_id: int, coding_paradigm: str = "auto",
) -> list[dict]:
    from app.skills.qualitative_coding import QualitativeCodingSkill
    skill = QualitativeCodingSkill()
    existing = await list_codes(db, project_id)
    existing_codes = [
        {"name": c.name, "definition": c.definition, "parent_code_name": ""}
        for c in existing
    ]
    result = await skill.execute(ai, {
        "transcript": transcript,
        "research_question": research_question,
        "coding_paradigm": coding_paradigm,
        "existing_codes": existing_codes,
    })
    try:
        text = result.content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(text).get("codes", [])
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse coding suggestions")
        return []


async def assign_code(
    db: AsyncSession, code_id: int, session_id: int,
    span_start: int = 0, span_end: int = 0, quote_text: str = "",
    coder_profile_id: int | None = None,
    is_ai_suggested: bool = False, confidence: float = 0.5,
) -> CodingAssignment:
    a = CodingAssignment(
        code_id=code_id, session_id=session_id,
        span_start=span_start, span_end=span_end, quote_text=quote_text,
        coder_profile_id=coder_profile_id,
        is_ai_suggested=is_ai_suggested, confidence=confidence,
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


async def list_assignments(db: AsyncSession, session_id: int) -> list[CodingAssignment]:
    result = await db.execute(
        select(CodingAssignment)
        .where(CodingAssignment.session_id == session_id)
        .order_by(CodingAssignment.span_start)
    )
    return list(result.scalars().all())


async def delete_assignment(db: AsyncSession, assignment_id: int) -> bool:
    result = await db.execute(select(CodingAssignment).where(CodingAssignment.id == assignment_id))
    a = result.scalar_one_or_none()
    if a is None:
        return False
    await db.delete(a)
    await db.commit()
    return True


async def calculate_intercoder_reliability(db: AsyncSession, session_id: int) -> dict:
    assignments = await list_assignments(db, session_id)
    if not assignments:
        return {"error": "No coding assignments found for this session"}
    by_code: dict[int, list[CodingAssignment]] = {}
    for a in assignments:
        by_code.setdefault(a.code_id, []).append(a)
    results = {}
    for code_id, code_assignments in by_code.items():
        coders = set(a.coder_profile_id for a in code_assignments if a.coder_profile_id)
        if len(coders) < 2:
            results[str(code_id)] = {"alpha": None, "note": "少于2位编码者，无法计算信度"}
            continue
        code_name = ""
        code_result = await db.execute(select(CodebookCode).where(CodebookCode.id == code_id))
        if code_obj := code_result.scalar_one_or_none():
            code_name = code_obj.name
        coder_segment_sets = {
            c: set((a.span_start, a.span_end) for a in code_assignments if a.coder_profile_id == c)
            for c in coders
        }
        coder_list = list(coders)
        total_pairs = len(coder_list) * (len(coder_list) - 1) / 2
        agreements = 0
        for i in range(len(coder_list)):
            for j in range(i + 1, len(coder_list)):
                s1, s2 = coder_segment_sets[coder_list[i]], coder_segment_sets[coder_list[j]]
                if s1 or s2:
                    intersection, union = len(s1 & s2), len(s1 | s2)
                    if union > 0 and intersection / union >= 0.5:
                        agreements += 1
        alpha = agreements / max(total_pairs, 1)
        results[str(code_id)] = {
            "code_name": code_name, "alpha": round(alpha, 3),
            "coders": len(coders), "assignments": len(code_assignments),
            "interpretation": (
                "良好信度" if alpha >= 0.80 else
                "可接受信度" if alpha >= 0.67 else
                "信度不足，建议讨论后重新编码"
            ),
        }
    return {"session_id": session_id, "reliability_by_code": results}


async def export_codebook(db: AsyncSession, project_id: int, fmt: str = "markdown") -> str:
    codes = await list_codes(db, project_id)
    if fmt == "json":
        return json.dumps([
            {"name": c.name, "definition": c.definition, "example": c.example,
             "exclusion_criteria": c.exclusion_criteria, "parent_code_id": c.parent_code_id,
             "paradigm": c.paradigm, "version": c.version}
            for c in codes
        ], ensure_ascii=False, indent=2)
    by_parent: dict[int | None, list[CodebookCode]] = {}
    for c in codes:
        by_parent.setdefault(c.parent_code_id, []).append(c)
    lines = ["# 编码簿", "", f"共 {len(codes)} 个编码", ""]
    root_codes = by_parent.get(None, [])
    def _render(code: CodebookCode, depth: int = 0):
        prefix = "  " * depth + ("- " if depth == 0 else "  - ")
        lines.append(f"{prefix}**{code.name}** `{code.paradigm}`")
        if code.definition:
            lines.append(f"{'  ' * (depth+1)}定义: {code.definition}")
        if code.example:
            lines.append(f"{'  ' * (depth+1)}示例: {code.example}")
        if code.exclusion_criteria:
            lines.append(f"{'  ' * (depth+1)}排除: {code.exclusion_criteria}")
        lines.append("")
        for child in by_parent.get(code.id, []):
            _render(child, depth + 1)
    for root in root_codes:
        _render(root)
    return "\n".join(lines)


async def create_version_snapshot(
    db: AsyncSession, project_id: int,
    created_by_profile_id: int | None = None, changelog: str = "",
) -> CodebookVersion:
    codes = await list_codes(db, project_id)
    snapshot = [
        {"name": c.name, "definition": c.definition, "example": c.example,
         "parent_code_id": c.parent_code_id, "paradigm": c.paradigm, "sort_order": c.sort_order}
        for c in codes
    ]
    result = await db.execute(
        select(func.max(CodebookVersion.version_number)).where(CodebookVersion.project_id == project_id)
    )
    max_ver = result.scalar() or 0
    version = CodebookVersion(
        project_id=project_id, version_number=max_ver + 1,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        created_by_profile_id=created_by_profile_id, changelog=changelog,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version
