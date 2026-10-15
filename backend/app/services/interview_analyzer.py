"""
Post-Interview Deep Analyzer — multi-dimensional qualitative analysis.

Combines: transcript + speaker segments + emotion timeline
→ thematic analysis + quality scoring + theory coding + cross-interview aggregation.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class InterviewAnalysis:
    session_id: str = ""
    duration_s: int = 0
    speaker_count: int = 0
    total_words: int = 0
    overall_mood: str = "neutral"
    mood_stability: float = 0.0
    emotional_peaks: list = field(default_factory=list)
    emotion_timeline_chart: list = field(default_factory=list)
    core_themes: list = field(default_factory=list)
    key_quotes: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)
    unaddressed_topics: list = field(default_factory=list)
    quality_scores: dict = field(default_factory=dict)
    theory_connections: list = field(default_factory=list)
    method_suggestions: list = field(default_factory=list)
    next_steps: list = field(default_factory=list)
    full_analysis_text: str = ""


@dataclass
class CrossInterviewReport:
    interview_count: int = 0
    total_duration_s: int = 0
    shared_themes: list = field(default_factory=list)
    divergent_themes: list = field(default_factory=list)
    emotion_comparison: list = field(default_factory=list)
    quality_comparison: list = field(default_factory=list)
    saturation_assessment: str = ""
    overall_insights: str = ""


class InterviewAnalyzer:
    """Deep qualitative analysis of interview transcripts.

    Usage:
        analyzer = InterviewAnalyzer()
        analysis = await analyzer.analyze(
            transcript="...",
            segments=[...],
            emotion_timeline={...},
            theme="academic",
        )
    """

    async def analyze(
        self,
        transcript: str,
        segments: list | None = None,
        emotion_timeline: dict | None = None,
        theme: str = "academic",
        scenario: str = "community_interview",
    ) -> InterviewAnalysis:
        start = time.time()
        a = InterviewAnalysis()
        a.duration_s = self._compute_duration(segments or [])
        a.speaker_count = self._count_speakers(segments or [])
        a.total_words = len(transcript)

        if emotion_timeline:
            a.overall_mood = emotion_timeline.get("overall_mood", "neutral")
            a.mood_stability = emotion_timeline.get("mood_stability", 0.0)
            a.emotional_peaks = emotion_timeline.get("emotional_peaks", [])

        if transcript.strip():
            content = await self._analyze_content(transcript, theme)
            a.core_themes = content.get("themes", [])
            a.key_quotes = content.get("key_quotes", [])
            a.contradictions = content.get("contradictions", [])
            a.unaddressed_topics = content.get("unaddressed_topics", [])
            a.quality_scores = await self._score_quality(transcript, segments or [])
            meta = await self._methodology_analysis(transcript, theme)
            a.theory_connections = meta.get("theory_connections", [])
            a.method_suggestions = meta.get("method_suggestions", [])
            a.next_steps = meta.get("next_steps", [])

        a.full_analysis_text = self._render(a)
        logger.info(
            f"InterviewAnalyzer: done in {time.time()-start:.1f}s "
            f"({len(a.core_themes)} themes, {len(a.key_quotes)} quotes)"
        )
        return a

    async def cross_analyze(
        self, interviews: list, theme: str = "academic"
    ) -> CrossInterviewReport:
        if not interviews:
            return CrossInterviewReport()
        report = CrossInterviewReport(
            interview_count=len(interviews),
            total_duration_s=sum(i.get("duration_s", 0) for i in interviews),
        )
        all_text = "\n\n---\n\n".join(
            f"[{i.get('session_id','?')}]\n{i.get('transcript','')[:3000]}"
            for i in interviews[:10]
        )
        if all_text.strip():
            try:
                cross = await self._cross_theme_analysis(all_text, theme)
                report.shared_themes = cross.get("shared_themes", [])
                report.divergent_themes = cross.get("divergent_themes", [])
                report.saturation_assessment = cross.get("saturation_assessment", "")
                report.overall_insights = cross.get("overall_insights", "")
            except Exception as e:
                logger.error(f"Cross analysis failed: {e}")
        report.emotion_comparison = [
            {
                "session_id": i.get("session_id", "?"),
                "mood": i.get("overall_mood", "neutral"),
                "stability": i.get("mood_stability", 0.0),
            }
            for i in interviews
        ]
        return report

    # ── LLM-powered analysis methods ─────────────────────────────────

    async def _analyze_content(self, transcript: str, theme: str) -> dict:
        from app.services.ai import AIService
        ai = AIService(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model="deepseek-v4-pro",
        )
        prompt = (
            f"分析以下访谈文本，输出JSON（不要其他内容）：\n\n{transcript[:6000]}\n\n"
            '{"themes": [{"name": "...", "confidence": 0.8, "quotes": ["..."]}], '
            '"key_quotes": ["..."], '
            '"contradictions": [{"topic": "...", "statement_a": "...", "statement_b": "..."}], '
            '"unaddressed_topics": ["..."]}'
        )
        messages = [
            {"role": "system", "content": "你是质性数据分析专家。只输出JSON，不输出其他内容。"},
            {"role": "user", "content": prompt},
        ]
        try:
            result = await ai.chat(messages, temperature=0.3, max_tokens=4096, task="analysis")
            return json.loads(result.strip())
        except Exception as e:
            logger.warning(f"Content analysis parse failed: {e}")
            return {}

    async def _score_quality(self, transcript: str, segments: list) -> dict:
        from app.services.ai import AIService
        ai = AIService(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model="deepseek-v4-flash",
        )
        prompt = (
            f"评估以下访谈质量，为每个维度打分（0-100），输出JSON：\n\n{transcript[:4000]}\n\n"
            "维度：openness_ratio, follow_up_depth, respondent_talk_ratio, "
            "neutrality, coverage_breadth, emotional_attunement\n"
            '输出如：{"openness_ratio": 75, "follow_up_depth": 60, ...}'
        )
        messages = [
            {"role": "system", "content": "你是访谈质量评估专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]
        try:
            result = await ai.chat(messages, temperature=0.2, max_tokens=512, task="analysis")
            return json.loads(result.strip())
        except Exception:
            logger.warning("Interview quality analysis failed", exc_info=True)
            return {}

    async def _methodology_analysis(self, transcript: str, theme: str) -> dict:
        from app.services.ai import AIService
        ai = AIService(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model="deepseek-v4-pro",
        )
        prompt = (
            f"基于以下访谈内容，输出JSON：\n\n{transcript[:4000]}\n\n"
            '{"theory_connections": [{"concept": "...", "relevance": "..."}], '
            '"method_suggestions": ["..."], '
            '"next_steps": ["..."]}'
        )
        messages = [
            {"role": "system", "content": "你是社会学方法论专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]
        try:
            result = await ai.chat(messages, temperature=0.4, max_tokens=2048, task="analysis")
            return json.loads(result.strip())
        except Exception:
            logger.warning("Methodology analysis failed", exc_info=True)
            return {}

    async def _cross_theme_analysis(self, transcripts: str, theme: str) -> dict:
        from app.services.ai import AIService
        ai = AIService(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model="deepseek-v4-pro",
        )
        prompt = (
            f"以下是多场访谈的汇总，请进行跨访谈主题分析，输出JSON：\n\n{transcripts[:10000]}\n\n"
            '{"shared_themes": [{"theme": "...", "frequency": 5, "interviews": ["id1","id2"]}], '
            '"divergent_themes": [{"theme": "...", "interview_a": "...", "interview_b": "..."}], '
            '"saturation_assessment": "新主题仍在涌现 / 接近理论饱和 / 已饱和", '
            '"overall_insights": "2-3句话的整体洞察"}'
        )
        messages = [
            {"role": "system", "content": "你是质性元分析专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]
        try:
            result = await ai.chat(messages, temperature=0.3, max_tokens=4096, task="analysis")
            return json.loads(result.strip())
        except Exception:
            logger.warning("Cross-theme analysis failed", exc_info=True)
            return {}

    # ── Static helpers ────────────────────────────────────────────────

    @staticmethod
    def _compute_duration(segments: list) -> int:
        if not segments:
            return 0
        return max(s.get("end_ms", s.get("end_time", 0)) for s in segments) // 1000

    @staticmethod
    def _count_speakers(segments: list) -> int:
        ids = {s.get("speaker_id", s.get("spk", -1)) for s in segments}
        return len(ids - {-1})

    def _render(self, a: InterviewAnalysis) -> str:
        parts = [
            "# 访谈深度分析报告",
            f"- 时长: {a.duration_s//60}分{a.duration_s%60}秒",
            f"- 发言人: {a.speaker_count}人",
            f"- 整体情绪: {a.overall_mood}（稳定性: {a.mood_stability}）",
            "",
            "## 核心主题",
        ]
        for t in a.core_themes:
            parts.append(f"- **{t.get('name','?')}** (置信度: {t.get('confidence',0)})")
            for q in t.get("quotes", [])[:2]:
                parts.append(f"  > {q}")

        parts.append("\n## 关键引述")
        for q in a.key_quotes[:8]:
            parts.append(f'- "{q}"')

        parts.append("\n## 访谈质量评分")
        for dim, score in a.quality_scores.items():
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            parts.append(f"- {dim}: {bar} {score}/100")

        parts.append("\n## 理论关联")
        for tc in a.theory_connections:
            parts.append(f"- **{tc.get('concept','?')}**: {tc.get('relevance','')}")

        parts.append("\n## 方法建议")
        for s in a.method_suggestions:
            parts.append(f"- {s}")

        parts.append("\n## 下一步行动")
        for s in a.next_steps:
            parts.append(f"- {s}")

        return "\n".join(parts)


interview_analyzer = InterviewAnalyzer()
