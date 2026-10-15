"""Pydantic request/response schemas for all API endpoints."""

from datetime import datetime
from typing import Optional


# ── Profile ──────────────────────────────────────────────────────

class ProfileCreate:
    mode: str = "personal"
    gender: Optional[str] = None
    role: str = "undergraduate"
    experience_level: str = "beginner"
    age_range: Optional[str] = None
    mbti: Optional[str] = None
    paradigm_preference: str = "qualitative"
    scenario_preference: str = "community_interview"


# ── Project ──────────────────────────────────────────────────────

class ProjectCreate:
    profile_id: int
    title: str = "未命名项目"
    research_direction: Optional[str] = None
    paradigm: str = "qualitative"


# ── Session ──────────────────────────────────────────────────────

class SessionCreate:
    project_id: int
    transcript_text: Optional[str] = None
    notes: Optional[str] = None


# ── Analysis ─────────────────────────────────────────────────────

class AnalysisRequest:
    project_id: int = 0
    type: str = "interview"
    content: str = ""
    paradigm: str = "qualitative"


# ── Export ───────────────────────────────────────────────────────

class ExportRequest:
    project_id: int = 0
    format: str = "report"
    content: str = ""
    notes: str = ""
