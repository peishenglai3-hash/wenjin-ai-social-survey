"""Iteration Knowledge Base — structured development retrospective.

Schema per 构想三:
  iterations      — 开发迭代记录
  case_points     — 可复用案例点
  micro_innovations — 微创新
  failure_points  — 失败点与修复
  implications    — 跨迭代推论
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class IterationRecord(Base, TimestampMixin):
    """One development iteration / sprint / debugging session."""

    __tablename__ = "iteration_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    phase: Mapped[str] = mapped_column(String(50), default="development")  # debugging | feature | refactor | deployment
    version: Mapped[str] = mapped_column(String(20), default="v0.2.1")
    summary: Mapped[str] = mapped_column(Text, default="")
    context_before: Mapped[str] = mapped_column(Text, default="")   # 什么触发了这次迭代
    context_after: Mapped[str] = mapped_column(Text, default="")    # 迭代后的状态
    lessons_learned: Mapped[str] = mapped_column(Text, default="")  # 核心教训
    tags: Mapped[str] = mapped_column(String(500), default="")       # comma-separated

    case_points: Mapped[list["CasePoint"]] = relationship(back_populates="iteration", cascade="all, delete-orphan")
    micro_innovations: Mapped[list["MicroInnovation"]] = relationship(back_populates="iteration", cascade="all, delete-orphan")
    failure_points: Mapped[list["FailurePoint"]] = relationship(back_populates="iteration", cascade="all, delete-orphan")


class CasePoint(Base, TimestampMixin):
    """Reusable pattern / solution extracted from an iteration."""

    __tablename__ = "case_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iteration_id: Mapped[int] = mapped_column(Integer, ForeignKey("iteration_records.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="")       # api | config | protocol | docker | permission
    pattern: Mapped[str] = mapped_column(Text, default="")              # 可复用的模式描述
    example: Mapped[str] = mapped_column(Text, default="")              # 具体代码/配置示例
    reuse_count: Mapped[int] = mapped_column(Integer, default=0)

    iteration: Mapped["IterationRecord"] = relationship(back_populates="case_points")


class MicroInnovation(Base, TimestampMixin):
    """A small innovation discovered during development."""

    __tablename__ = "micro_innovations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iteration_id: Mapped[int] = mapped_column(Integer, ForeignKey("iteration_records.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    impact_score: Mapped[float] = mapped_column(Float, default=1.0)      # 1-5
    status: Mapped[str] = mapped_column(String(20), default="adopted")   # proposed | adopted | deprecated

    iteration: Mapped["IterationRecord"] = relationship(back_populates="micro_innovations")


class FailurePoint(Base, TimestampMixin):
    """A failure encountered, its root cause, fix, and prevention."""

    __tablename__ = "failure_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iteration_id: Mapped[int] = mapped_column(Integer, ForeignKey("iteration_records.id"), nullable=False)
    symptom: Mapped[str] = mapped_column(Text, default="")            # 表面症状
    root_cause: Mapped[str] = mapped_column(Text, default="")         # 根本原因
    fix: Mapped[str] = mapped_column(Text, default="")                # 修复方案
    prevention: Mapped[str] = mapped_column(Text, default="")         # 预防措施
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low | medium | high | critical

    iteration: Mapped["IterationRecord"] = relationship(back_populates="failure_points")


class Implication(Base, TimestampMixin):
    """Cross-iteration implication /推论 — links to any source type."""

    __tablename__ = "implications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(50), default="")    # iteration | failure_point | case_point
    source_id: Mapped[int] = mapped_column(Integer, default=0)
    implication: Mapped[str] = mapped_column(Text, default="")          # 推论内容
    actionable: Mapped[str] = mapped_column(Text, default="")           # 可操作建议
    priority: Mapped[str] = mapped_column(String(20), default="medium") # low | medium | high | critical
