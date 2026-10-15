"""
Confidence Markers — trust indicators for AI-generated outputs.

Attaches a ConfidenceMarker to skill outputs so users can gauge reliability
at a glance. Three output categories:
  - methodology suggestions: matrix match quality
  - coding/literature suggestions: LLM self-assessment
  - analysis conclusions: heuristic evidence strength
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceMarker:
    """Trust indicator attached to AI-generated outputs.

    level:     "high" | "medium" | "low" — human-readable tier
    score:     0.0 – 1.0 numeric confidence
    rationale: Chinese explanation of why this confidence level was assigned
    source:    "heuristic" | "llm_self_assess" | "matrix_match" | "composite"
    """

    level: str = "medium"
    score: float = 0.5
    rationale: str = ""
    source: str = "heuristic"

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "score": round(self.score, 2),
            "rationale": self.rationale,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConfidenceMarker":
        return cls(
            level=d.get("level", "medium"),
            score=float(d.get("score", 0.5)),
            rationale=d.get("rationale", ""),
            source=d.get("source", "heuristic"),
        )


def _score_to_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def for_methodology(keyword_hits: int, max_possible: int = 10) -> ConfidenceMarker:
    if max_possible <= 0:
        score = 0.3
    else:
        score = min(1.0, keyword_hits / max(1, max_possible))
    level = _score_to_level(score)
    if score >= 0.8:
        rationale = "研究方法论矩阵高度匹配：研究问题关键词与推荐方法论体系精确对应"
    elif score >= 0.5:
        rationale = "研究方法论矩阵中等匹配：部分关键词命中，建议人工确认方法论选择"
    else:
        rationale = "研究方法论矩阵匹配度较低：研究问题描述较宽泛，建议细化后再获取方法论推荐"
    return ConfidenceMarker(level=level, score=score, rationale=rationale, source="matrix_match")


def for_methodology_match(purpose: str, data_type: str) -> ConfidenceMarker:
    score = 0.90 if (purpose and data_type) else 0.35
    level = _score_to_level(score)
    if score >= 0.8:
        rationale = f"研究方法论矩阵精确匹配：研究目的={purpose}, 数据类型={data_type}"
    else:
        rationale = "研究方法论矩阵未找到精确匹配键，已回退到最接近的默认方案"
    return ConfidenceMarker(level=level, score=score, rationale=rationale, source="matrix_match")


def from_llm_response(content: str) -> ConfidenceMarker:
    """Extract confidence from an LLM response that includes a confidence field."""
    try:
        text = content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        data = json.loads(text)
        if isinstance(data, dict):
            conf = data.get("confidence") or data.get("置信度")
            if conf is not None:
                score = float(conf)
                level = _score_to_level(score)
                return ConfidenceMarker(
                    level=level, score=score,
                    rationale="LLM自评估置信度（从输出JSON提取）",
                    source="llm_self_assess",
                )
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    patterns = [
        r'"confidence"\s*:\s*([\d.]+)',
        r'置信度[：:]\s*([\d.]+)',
        r'confidence[：:]\s*([\d.]+)',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            try:
                score = max(0.0, min(1.0, float(m.group(1))))
                return ConfidenceMarker(
                    level=_score_to_level(score), score=score,
                    rationale="LLM自评估置信度（从输出文本提取）",
                    source="llm_self_assess",
                )
            except ValueError:
                pass

    return ConfidenceMarker(
        level="medium", score=0.5,
        rationale="无法从LLM输出中提取明确置信度，默认中等",
        source="llm_self_assess",
    )


def for_literature(source_quality: int = 3, relevance_match: float = 0.5) -> ConfidenceMarker:
    score = (source_quality / 5.0) * 0.5 + relevance_match * 0.5
    level = _score_to_level(score)
    if source_quality >= 4 and relevance_match >= 0.7:
        rationale = "文献推荐置信度高：来源权威且与研究主题高度相关"
    elif source_quality >= 3 or relevance_match >= 0.5:
        rationale = "文献推荐置信度中等：来源质量或相关性存在一定不确定性"
    else:
        rationale = "文献推荐置信度较低：来源质量一般或相关性不足，建议补充检索"
    return ConfidenceMarker(level=level, score=score, rationale=rationale, source="heuristic")


def for_analysis(
    evidence_count: int = 0,
    sentiment_consistency: float = 0.5,
    coding_coverage: float = 0.5,
) -> ConfidenceMarker:
    score = (
        min(1.0, evidence_count / 5.0) * 0.4
        + sentiment_consistency * 0.3
        + coding_coverage * 0.3
    )
    level = _score_to_level(score)
    if score >= 0.8:
        rationale = f"分析结论置信度高：{evidence_count}条证据支持，情感一致性和编码覆盖率良好"
    elif score >= 0.5:
        rationale = f"分析结论置信度中等：证据链{evidence_count}条，建议交叉验证"
    else:
        rationale = "分析结论置信度较低：证据不足或存在矛盾，建议人工深入分析"
    return ConfidenceMarker(level=level, score=score, rationale=rationale, source="composite")


def generic_medium(rationale: str = "AI生成内容，建议人工审核") -> ConfidenceMarker:
    return ConfidenceMarker(level="medium", score=0.5, rationale=rationale, source="heuristic")
