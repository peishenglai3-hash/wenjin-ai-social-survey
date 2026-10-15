"""Unit tests for SkillRegistry — registration, matching, routing."""

import pytest
from unittest.mock import AsyncMock

from app.skills.registry import SkillRegistry, skill_registry
from app.skills.base import BaseSkill, SkillResult
from app.skills.questionnaire import QuestionnaireSkill
from app.skills.topic_argumentation import TopicArgumentationSkill
from app.skills.transcript_analysis import TranscriptAnalysisSkill


class TestSkillRegistryBasic:
    """Test registration and listing."""

    def test_register_and_get_skill(self):
        reg = SkillRegistry()
        skill = QuestionnaireSkill()
        reg.register(skill)

        retrieved = reg.get("questionnaire")
        assert retrieved is skill
        assert retrieved.name == "questionnaire"
        assert "问卷" in retrieved.description

    def test_get_nonexistent_skill_returns_none(self):
        reg = SkillRegistry()
        assert reg.get("nonexistent") is None

    def test_list_skills_returns_all_registered(self):
        reg = SkillRegistry()
        reg.register(QuestionnaireSkill())
        reg.register(TopicArgumentationSkill())

        skills = reg.list_skills()
        assert len(skills) == 2
        names = [s["name"] for s in skills]
        assert "questionnaire" in names
        assert "topic_argumentation" in names


class TestSkillMatching:
    """Test intent → skill matching."""

    def test_questionnaire_skill_matches_design_intent(self):
        skill = QuestionnaireSkill()
        # "问卷" + "量表" = 2 hits → 2/3.6 ≈ 0.556 > 0.5
        score = skill.match("帮我设计一份关于社区治理的量表和问卷")
        assert score > 0.5

    def test_questionnaire_skill_low_on_irrelevant_intent(self):
        skill = QuestionnaireSkill()
        score = skill.match("分析这段访谈录音")
        assert score < 0.5

    def test_topic_argumentation_matches_topic_intent(self):
        skill = TopicArgumentationSkill()
        # "论证" + "选题" + "研究方向" = 3 hits → 3/4.2 ≈ 0.714 > 0.5
        score = skill.match("论证这个研究选题和研究方向的社会价值")
        assert score > 0.5

    def test_transcript_analysis_matches_analysis_intent(self):
        skill = TranscriptAnalysisSkill()
        # "文本分析" + "编码" = 2 hits → 2/3.3 ≈ 0.606 > 0.5
        score = skill.match("帮我做这段访谈的文本分析和主题编码")
        assert score > 0.5


class TestSkillRouting:
    """Test the route() method dispatches to the right skill."""

    @pytest.mark.asyncio
    async def test_direct_match_dispatches_to_best_skill(self):
        reg = SkillRegistry()
        reg.register(QuestionnaireSkill())
        reg.register(TopicArgumentationSkill())

        ai = AsyncMock()
        ai.chat.return_value = "问卷生成结果"

        result = await reg.route(
            ai,
            user_intent="帮我设计一份社区治理的量表和问卷",
            user_input={"topic": "社区治理"},
        )

        assert isinstance(result, SkillResult)
        assert "问卷生成结果" in result.content

    @pytest.mark.asyncio
    async def test_fallback_uses_llm_classification(self):
        """When no skill matches above threshold, use LLM to classify."""
        # Create a registry with skills that won't match
        reg = SkillRegistry()
        # TranscriptAnalysisSkill uses keywords like "分析", "访谈" —
        # use an intent that won't match those
        reg.register(TranscriptAnalysisSkill())

        ai = AsyncMock()
        ai.chat.return_value = "transcript_analysis"  # LLM picks this

        result = await reg.route(
            ai,
            user_intent="some vague request",
            user_input={"text": "hello"},
        )

        # Should have called the LLM to classify
        assert ai.chat.called
        assert isinstance(result, SkillResult)

    @pytest.mark.asyncio
    async def test_no_match_returns_error_message(self):
        """When neither direct match nor LLM classification works."""
        reg = SkillRegistry()
        reg.register(QuestionnaireSkill())

        ai = AsyncMock()
        ai.chat.return_value = "nonexistent_skill_name"

        result = await reg.route(
            ai,
            user_intent="random gibberish xyz123",
            user_input={},
        )

        assert isinstance(result, SkillResult)
        assert "No matching skill found" in result.content


class TestGlobalSingleton:
    """Sanity check on the global skill_registry singleton."""

    def test_global_registry_is_singleton(self):
        from app.skills.registry import skill_registry as sr1
        from app.skills.registry import skill_registry as sr2
        assert sr1 is sr2

    def test_global_registry_has_skills(self):
        """After the router imports and registers all skills, verify."""
        from app.api.v1.router import skill_registry as sr
        skills = sr.list_skills()
        # v0.4.0 registers 10 skills
        assert len(skills) == 10
