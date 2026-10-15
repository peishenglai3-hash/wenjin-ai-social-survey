"""Pydantic schemas for questionnaire CRUD, responses, and statistics."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class QuestionnaireSave(BaseModel):
    """Request body for saving a parsed AI-generated questionnaire."""
    project_id: int
    title: str = "未命名问卷"
    constructs_json: str = "[]"
    questions_json: str = "[]"
    scales_json: str = "[]"
    total_items: int = 0
    estimated_time_minutes: int = 0
    raw_output: str = ""
    paradigm: str = "quantitative"


class QuestionnaireOut(BaseModel):
    """Response model for questionnaire queries."""
    id: int
    project_id: int
    title: str
    constructs_json: str
    questions_json: str
    scales_json: str
    total_items: int
    estimated_time_minutes: int
    is_active: bool
    paradigm: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    """A single answer within a response submission."""
    question_id: str
    question_text: str = ""
    value: str = ""
    option_index: Optional[int] = None
    is_skipped: bool = False


class ResponseSubmit(BaseModel):
    """Request body for submitting a filled questionnaire."""
    respondent_label: str = ""
    respondent_metadata_json: Optional[str] = None
    session_id: Optional[int] = None
    answers: list[AnswerSubmit]
    interview_duration_s: Optional[int] = None


class ResponseOut(BaseModel):
    """Response model for a submitted questionnaire."""
    id: int
    questionnaire_id: int
    respondent_label: str
    answers_json: str
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionStat(BaseModel):
    """Per-question statistics."""
    question_id: str
    question_text: str
    scale_type: str
    frequencies: dict[str, int] = {}
    skip_count: int = 0


class QuestionnaireStats(BaseModel):
    """Descriptive statistics for a questionnaire."""
    questionnaire_id: int
    title: str
    total_responses: int
    question_stats: list[QuestionStat]
