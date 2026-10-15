"""Tests for ProfileIterator — gradual profile evolution from reflection insights.

Covers:
  - Insight recording to DB
  - Consensus checking (multiple consistent insights needed)
  - Pending insight application with stability guard
  - Evolution history retrieval
  - Evolution summary computation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.profile_iterator import ProfileIterator


@pytest.fixture
def mock_db():
    """Create a mock DB session that returns canned query results."""
    db = AsyncMock(spec=AsyncSession)
    return db


class TestInsightRecording:
    """Record reflection insights as IterationInsight rows."""

    @pytest.mark.asyncio
    async def test_record_insights_creates_db_rows(self, mock_db):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        insights = [
            {"dimension": "theory_driven", "direction": 1, "confidence": 0.8,
             "rationale": "test", "evidence": "ev"},
        ]

        result = await ProfileIterator.record_insights(
            db=mock_db,
            profile_id=1,
            insights=insights,
            source_reflection_id=5,
        )

        assert len(result) == 1
        assert result[0].profile_id == 1
        assert result[0].dimension == "theory_driven"
        assert result[0].is_applied is False
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_record_empty_insights_no_commit(self, mock_db):
        result = await ProfileIterator.record_insights(
            db=mock_db, profile_id=1, insights=[],
        )
        assert len(result) == 0
        mock_db.commit.assert_not_called()


class TestApplyPending:
    """Apply pending profile adjustments with consensus guard."""

    @pytest.mark.asyncio
    async def test_apply_pending_profile_not_found(self, mock_db):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await ProfileIterator.apply_pending(mock_db, profile_id=999)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_apply_pending_no_insights(self, mock_db):
        mock_profile = MagicMock()
        for dim in ["theory_driven", "methodological_rigidity", "analysis_depth",
                     "structure_preference", "participation_level", "tech_dependency",
                     "writing_style", "learning_preference"]:
            setattr(mock_profile, dim, 3)

        mock_db.execute = AsyncMock(side_effect=[
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_profile)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ])

        result = await ProfileIterator.apply_pending(mock_db, profile_id=1)
        assert result.get("message") == "No pending insights to apply"

    @pytest.mark.asyncio
    async def test_apply_pending_insufficient_consensus(self, mock_db):
        """Single insight shouldn't trigger adjustment (needs 2 for magnitude=1)."""
        from app.models.survey import IterationInsight

        mock_profile = MagicMock()
        for dim in ["theory_driven", "methodological_rigidity", "analysis_depth",
                     "structure_preference", "participation_level", "tech_dependency",
                     "writing_style", "learning_preference"]:
            setattr(mock_profile, dim, 3)

        insight = IterationInsight(
            profile_id=1, dimension="theory_driven", direction=1,
            confidence=0.8, rationale="test", is_applied=False,
        )
        insight.id = 1

        mock_db.execute = AsyncMock(side_effect=[
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_profile)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[insight])
            ))),
        ])

        result = await ProfileIterator.apply_pending(mock_db, profile_id=1)
        assert len(result["applied"]) == 0

    @pytest.mark.asyncio
    async def test_apply_pending_sufficient_consensus(self, mock_db):
        """Two consistent insights should apply."""
        from app.models.survey import IterationInsight

        mock_profile = MagicMock()
        for dim in ["theory_driven", "methodological_rigidity", "analysis_depth",
                     "structure_preference", "participation_level", "tech_dependency",
                     "writing_style", "learning_preference"]:
            setattr(mock_profile, dim, 3)

        i1 = IterationInsight(
            profile_id=1, dimension="participation_level", direction=1,
            confidence=0.8, rationale="用户越来越倾向深度参与", is_applied=False,
        )
        i1.id = 1
        i2 = IterationInsight(
            profile_id=1, dimension="participation_level", direction=1,
            confidence=0.7, rationale="多次反思显示参与度提升", is_applied=False,
        )
        i2.id = 2

        mock_db.execute = AsyncMock(side_effect=[
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_profile)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[i1, i2])
            ))),
            # 3rd: _count_consistent_insights → scalar()
            AsyncMock(scalar=MagicMock(return_value=2)),
        ])

        result = await ProfileIterator.apply_pending(mock_db, profile_id=1, stability=0.0)
        assert len(result["applied"]) == 1
        assert result["applied"][0]["dimension"] == "participation_level"

    @pytest.mark.asyncio
    async def test_apply_pending_high_stability_prevents_change(self, mock_db):
        """stability=0.95 prevents shift even with 2 insights."""
        from app.models.survey import IterationInsight

        mock_profile = MagicMock()
        for dim in ["theory_driven", "methodological_rigidity", "analysis_depth",
                     "structure_preference", "participation_level", "tech_dependency",
                     "writing_style", "learning_preference"]:
            setattr(mock_profile, dim, 3)

        i1 = IterationInsight(
            profile_id=1, dimension="writing_style", direction=1,
            confidence=0.9, rationale="test", is_applied=False,
        )
        i1.id = 1
        i2 = IterationInsight(
            profile_id=1, dimension="writing_style", direction=1,
            confidence=0.8, rationale="test", is_applied=False,
        )
        i2.id = 2

        mock_db.execute = AsyncMock(side_effect=[
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_profile)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[i1, i2])
            ))),
        ])

        result = await ProfileIterator.apply_pending(mock_db, profile_id=1, stability=0.95)
        assert len(result["applied"]) == 0

    @pytest.mark.asyncio
    async def test_apply_pending_marks_as_applied(self, mock_db):
        """Applied insights are marked is_applied=True."""
        from app.models.survey import IterationInsight

        mock_profile = MagicMock()
        for dim in ["theory_driven", "methodological_rigidity", "analysis_depth",
                     "structure_preference", "participation_level", "tech_dependency",
                     "writing_style", "learning_preference"]:
            setattr(mock_profile, dim, 3)

        i1 = IterationInsight(
            profile_id=1, dimension="learning_preference", direction=1,
            confidence=1.0, rationale="强", is_applied=False,
        )
        i1.id = 1
        i2 = IterationInsight(
            profile_id=1, dimension="learning_preference", direction=1,
            confidence=1.0, rationale="强", is_applied=False,
        )
        i2.id = 2

        mock_db.execute = AsyncMock(side_effect=[
            AsyncMock(scalar_one_or_none=MagicMock(return_value=mock_profile)),
            AsyncMock(scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=[i1, i2])
            ))),
            # 3rd: _count_consistent_insights for magnitude=1 → needs 2 consensus
            AsyncMock(scalar=MagicMock(return_value=2)),
        ])

        result = await ProfileIterator.apply_pending(mock_db, profile_id=1, stability=0.0)
        assert len(result["applied"]) >= 1
        assert i1.is_applied is True
        assert i2.is_applied is True


class TestEvolutionHistory:
    """Retrieve profile evolution timeline."""

    @pytest.mark.asyncio
    async def test_get_evolution_history_returns_data(self, mock_db):
        from app.models.survey import IterationInsight
        from datetime import datetime, timezone

        i1 = IterationInsight(
            profile_id=1, dimension="theory_driven", direction=1,
            confidence=0.8, is_applied=True,
        )
        i1.id = 1
        i1.applied_at = datetime.now(timezone.utc)
        i1.previous_value = 3
        i1.new_value = 4
        i1.rationale = "test"
        i1.evidence = "ev"

        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(
            all=MagicMock(return_value=[i1])
        ))
        mock_db.execute = AsyncMock(return_value=mock_result)

        history = await ProfileIterator.get_evolution_history(mock_db, profile_id=1)
        assert len(history) == 1
        assert history[0]["dimension"] == "theory_driven"
        assert history[0]["previous_value"] == 3
        assert history[0]["new_value"] == 4

    @pytest.mark.asyncio
    async def test_get_evolution_summary_empty(self, mock_db):
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(
            all=MagicMock(return_value=[])
        ))
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await ProfileIterator.get_evolution_summary(mock_db, profile_id=1)
        assert summary["total_shifts"] == 0
