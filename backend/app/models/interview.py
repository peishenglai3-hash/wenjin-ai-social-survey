"""Interview data models — emotion timelines, speaker segments, quality scores."""

from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class InterviewSegment(Base, TimestampMixin):
    __tablename__ = "interview_segments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_sessions.id"), nullable=False, index=True)
    start_ms: Mapped[int] = mapped_column(Integer, default=0)
    end_ms: Mapped[int] = mapped_column(Integer, default=0)
    speaker_id: Mapped[int] = mapped_column(Integer, default=-1)
    speaker_label: Mapped[str] = mapped_column(String(50), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    emotion: Mapped[str] = mapped_column(String(20), default="neutral")
    emotion_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    language: Mapped[str] = mapped_column(String(10), default="zh")

class EmotionSnapshot(Base, TimestampMixin):
    __tablename__ = "emotion_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_sessions.id"), nullable=False, index=True)
    timestamp_ms: Mapped[int] = mapped_column(Integer, default=0)
    voice_emotion: Mapped[str] = mapped_column(String(20), default="neutral")
    voice_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_sentiment: Mapped[str] = mapped_column(String(20), default="neutral")
    semantic_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    speech_rate_wpm: Mapped[float] = mapped_column(Float, default=0.0)
    pause_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    volume_peak: Mapped[float] = mapped_column(Float, default=0.0)
    fused_emotion: Mapped[str] = mapped_column(String(20), default="neutral")
    fused_intensity: Mapped[float] = mapped_column(Float, default=0.0)

class InterviewQualityScore(Base, TimestampMixin):
    __tablename__ = "interview_quality_scores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_sessions.id"), nullable=False, unique=True, index=True)
    openness_ratio: Mapped[int] = mapped_column(Integer, default=0)
    follow_up_depth: Mapped[int] = mapped_column(Integer, default=0)
    respondent_talk_ratio: Mapped[int] = mapped_column(Integer, default=0)
    neutrality: Mapped[int] = mapped_column(Integer, default=0)
    coverage_breadth: Mapped[int] = mapped_column(Integer, default=0)
    emotional_attunement: Mapped[int] = mapped_column(Integer, default=0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    raw_analysis_json: Mapped[str] = mapped_column(Text, default="{}")

class SessionEmotionSummary(Base, TimestampMixin):
    __tablename__ = "session_emotion_summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("survey_sessions.id"), nullable=False, unique=True, index=True)
    overall_mood: Mapped[str] = mapped_column(String(20), default="neutral")
    mood_stability: Mapped[float] = mapped_column(Float, default=0.0)
    angry_pct: Mapped[float] = mapped_column(Float, default=0.0)
    happy_pct: Mapped[float] = mapped_column(Float, default=0.0)
    neutral_pct: Mapped[float] = mapped_column(Float, default=0.0)
    sad_pct: Mapped[float] = mapped_column(Float, default=0.0)
    emotional_peaks_json: Mapped[str] = mapped_column(Text, default="[]")
    timeline_json: Mapped[str] = mapped_column(Text, default="[]")
