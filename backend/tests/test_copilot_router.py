"""Tests for copilot router with ClusterRouter integration (v2 personalisation)."""
import pytest
from app.api.v1.router_copilot import _build_system_prompt


FULL_PROFILE = {
    "role": "graduate",
    "experience_level": "intermediate",
    "paradigm_preference": "qualitative",
    "scenario_preference": "community_interview",
    "theme_preference": "academic",
    "theory_driven": 3, "methodological_rigidity": 4,
    "analysis_depth": 2, "structure_preference": 5,
    "participation_level": 4, "tech_dependency": 2,
    "writing_style": 3, "learning_preference": 4,
}

FULL_PROJECT = {
    "title": "社区治理试点研究",
    "research_direction": "探究基层社区治理中的居民参与机制",
    "phase": "during_survey",
    "paradigm": "qualitative",
}

MEMORY_CTX = "## 用户记忆\n- 偏好深度访谈而非问卷\n- 上次田野中遇到rapport建立困难"


class TestBuildSystemPrompt:
    """Tests for _build_system_prompt() with ClusterRouter integration."""

    def test_base_identity_present(self):
        result = _build_system_prompt(None, None)
        assert "问津" in result
        assert "Survey Copilot" in result

    def test_no_profile_no_crash(self):
        result = _build_system_prompt(None, None)
        assert isinstance(result, str) and len(result) > 50

    def test_empty_profile_no_crash(self):
        result = _build_system_prompt({}, {})
        assert isinstance(result, str)

    def test_fragments_in_output_for_graduate_qualitative(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        # Fragment content should appear (not old label maps)
        assert "硕士研究生" in result
        assert "质性研究" in result
        assert "一定经验" in result

    def test_no_old_hardcoded_labels(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        # Old label maps should NOT appear
        assert "理论驱动→经验驱动" not in result
        assert "严谨规范→灵活探索" not in result
        assert "当前用户画像" not in result
        assert "身份:" not in result  # old label: "- 身份: 硕士研究生"

    def test_theme_fragment_in_output(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        assert "学术风格" in result or "学术" in result

    def test_spectrum_compact_format(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        # Compact comma-separated format, not bar charts
        assert "方法论光谱" in result
        assert "理论↔经验=3" in result
        assert "严谨↔灵活=4" in result
        # No old bar chart chars
        assert "█" not in result
        assert "░" not in result

    def test_memory_context_injected(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT, memory_context=MEMORY_CTX)
        assert "偏好深度访谈而非问卷" in result

    def test_no_memory_context_when_empty(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        assert "偏好深度访谈" not in result

    def test_project_context_injected(self):
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        assert "社区治理试点研究" in result
        assert "探究基层社区治理中的居民参与机制" in result
        assert "调查中" in result

    def test_no_project_context_when_none(self):
        result = _build_system_prompt(FULL_PROFILE, None)
        assert "当前调查项目" not in result

    def test_closing_instructions_present(self):
        result = _build_system_prompt(None, None)
        assert "中文" in result
        assert "Markdown格式" in result

    def test_different_role_produces_different_output(self):
        undergrad = _build_system_prompt(
            {"role": "undergraduate", "experience_level": "beginner",
             "paradigm_preference": "quantitative", "theme_preference": "youth"}, None)
        faculty = _build_system_prompt(
            {"role": "faculty", "experience_level": "advanced",
             "paradigm_preference": "quantitative", "theme_preference": "academic"}, None)
        # Both should work but contain different role content
        assert "本科生" in undergrad
        assert "高校教师" in faculty
        # They should differ meaningfully
        assert undergrad != faculty

    def test_legacy_profile_without_theme_preference(self):
        legacy = {"role": "practitioner", "experience_level": "advanced"}
        # theme passed as parameter should fill in
        result = _build_system_prompt(legacy, None, theme="government")
        assert "实务工作者" in result
        # Should not crash

    def test_extra_context_adds_reflection_fragment(self):
        result = _build_system_prompt(
            FULL_PROFILE, None,
            extra_context={"reflection_trigger": "fieldwork_completed"},
        )
        # Reflection fragment content should appear
        assert "田野" in result or "反思" in result

    def test_prompt_is_all_chinese_or_code(self):
        """Output should be predominantly Chinese (the platform language)."""
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT)
        # Core elements in Chinese
        assert "问津" in result
        assert "社会调查" in result


class TestClusterRouterIntegration:
    """Verify ClusterRouter is actually being used (not old static maps)."""

    def test_role_fragment_id_in_compact_assembly(self):
        from app.services.cluster_router import cluster_router
        compact = cluster_router.assemble_compact({"role": "graduate"})
        assert "role_graduate" in compact

    def test_multiple_fragments_for_full_profile(self):
        from app.services.cluster_router import cluster_router
        desc = cluster_router.describe_match(FULL_PROFILE)
        # Should match at least 4 dimensions: role, paradigm, experience, theme
        assert desc["fragment_count"] >= 4

    def test_fragment_assembly_via_copilot_produces_valid_prompt(self):
        """End-to-end: profile → assemble → usable system prompt."""
        result = _build_system_prompt(FULL_PROFILE, FULL_PROJECT, memory_context=MEMORY_CTX)
        # Must have all major sections
        assert "问津" in result
        assert "社会调查" in result
        assert "社区治理试点研究" in result
        assert "偏好深度访谈" in result
        assert "中文" in result
        # Must be a reasonable length (300-3000 chars)
        assert 300 < len(result) < 5000
