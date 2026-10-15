"""Tests for ClusterRouter + Prompt Fragment Library."""
import pytest
from app.services.cluster_router import ClusterRouter, cluster_router
from app.skills.prompt_fragments import list_all_fragments, find_fragment, get_fragments_by_dimension


class TestPromptFragments:
    def test_all_fragments_not_empty(self):
        assert len(list_all_fragments()) >= 20

    def test_each_dimension_has_fragments(self):
        for dim in ["role", "paradigm", "experience", "scenario", "theme", "reflection_trigger"]:
            assert len(get_fragments_by_dimension(dim)) >= 2

    def test_find_fragment_correct(self):
        f = find_fragment("role", "undergraduate")
        assert f is not None and "本科生" in f.content and f.priority == 5

    def test_find_nonexistent(self):
        assert find_fragment("role", "alien") is None

    def test_valid_priorities(self):
        for f in list_all_fragments():
            assert 1 <= f["priority"] <= 5


class TestClusterRouter:
    def test_match_graduate_qualitative(self):
        m = cluster_router.match({"role": "graduate", "paradigm_preference": "qualitative", "experience_level": "intermediate", "theme_preference": "academic"})
        assert len(m) >= 4
        for i in range(len(m) - 1):
            assert m[i].priority >= m[i + 1].priority

    def test_match_with_reflection_context(self):
        m = cluster_router.match_with_context({"role": "undergraduate", "paradigm_preference": "mixed"}, {"reflection_trigger": "fieldwork_completed"})
        ids = [f.id for f in m]
        assert "role_undergraduate" in ids and "reflect_fieldwork" in ids

    def test_unknown_values_no_error(self):
        assert len(cluster_router.match({"role": "astronaut"})) == 0

    def test_assemble_produces_full_prompt(self):
        r = cluster_router.assemble({"role": "faculty", "paradigm_preference": "quantitative", "experience_level": "advanced"}, base_prompt="BASE")
        assert "BASE" in r and "高校教师" in r

    def test_assemble_empty_profile(self):
        assert cluster_router.assemble({}, base_prompt="ONLY") == "ONLY"

    def test_assemble_compact(self):
        assert "role_undergraduate" in cluster_router.assemble_compact({"role": "undergraduate"})

    def test_describe_match(self):
        d = cluster_router.describe_match({"role": "practitioner", "theme_preference": "government"})
        assert d["fragment_count"] >= 2

    def test_list_clusters(self):
        assert "role" in cluster_router.list_available_clusters()
