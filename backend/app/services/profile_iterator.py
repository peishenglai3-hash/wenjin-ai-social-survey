"""ProfileIterator — gradual, evidence-based profile evolution from reflection insights.

Implements the "迭代画像" (iterative profiling) mechanism:
  1. Accumulates reflection insights (IterationInsight rows)
  2. Applies a stability guard to prevent over-rapid profile drift
  3. When confidence × consensus exceeds threshold, applies adjustment
  4. Maintains a traceable evolution history

Design principles:
  - Each reflection session can produce at most ±1 shift per dimension
  - Multiple consistent insights are required for a ±2 cumulative shift
  - Stability parameter (0.7 default) controls resistance to change
  - All adjustments are logged to IterationInsight for audit
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import UserProfile, IterationInsight

logger = logging.getLogger(__name__)

# Spectrum dimensions with their 1-5 ranges
SPECTRUM_DIMS = [
    "theory_driven", "methodological_rigidity", "analysis_depth",
    "structure_preference", "participation_level", "tech_dependency",
    "writing_style", "learning_preference",
]

# How many consistent insights (same dimension, same direction) are needed
# before a shift of a given magnitude is applied:
#   magnitude=1: 2 consistent insights
#   magnitude=2: 4 consistent insights
CONSENSUS_THRESHOLDS = {1: 2, 2: 4}


class ProfileIterator:
    """Manages gradual, consensus-based profile spectrum evolution."""

    # ── Insight Recording ───────────────────────────────────────────────────

    @staticmethod
    async def record_insights(
        db: AsyncSession,
        profile_id: int,
        insights: list[dict],
        source_reflection_id: int | None = None,
        source_project_id: int | None = None,
    ) -> list[IterationInsight]:
        """Record reflection insights as pending IterationInsight rows.

        Each insight is saved with is_applied=False.  The apply_pending()
        method later evaluates which ones meet the consensus threshold.
        """
        saved = []
        for insight in insights:
            row = IterationInsight(
                profile_id=profile_id,
                source_reflection_id=source_reflection_id,
                source_project_id=source_project_id,
                dimension=insight.get("dimension", ""),
                direction=insight.get("direction", 0),
                confidence=insight.get("confidence", 0.5),
                rationale=insight.get("rationale", ""),
                evidence=insight.get("evidence", ""),
                is_applied=False,
            )
            db.add(row)
            saved.append(row)

        if saved:
            await db.commit()
            logger.info("Recorded %d iteration insights for profile %d", len(saved), profile_id)

        return saved

    # ── Consensus Check ─────────────────────────────────────────────────────

    @staticmethod
    async def _count_consistent_insights(
        db: AsyncSession,
        profile_id: int,
        dimension: str,
        direction_sign: int,
    ) -> int:
        """Count how many unapplied insights agree on shifting `dimension`
        in the same direction (positive or negative)."""
        result = await db.execute(
            select(func.count(IterationInsight.id)).where(
                and_(
                    IterationInsight.profile_id == profile_id,
                    IterationInsight.dimension == dimension,
                    IterationInsight.is_applied == False,
                    # Same sign direction (both positive or both negative)
                    IterationInsight.direction * direction_sign > 0,
                )
            )
        )
        return result.scalar() or 0

    # ── Applying Adjustments ────────────────────────────────────────────────

    @staticmethod
    async def apply_pending(
        db: AsyncSession,
        profile_id: int,
        stability: float = 0.7,
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        """Evaluate all pending insights and apply those meeting consensus threshold.

        Returns a summary of applied adjustments.

        Args:
            db: database session
            profile_id: user profile ID
            stability: 0-1, higher = more resistant to change
            auto_commit: if True, commits after applying adjustments
        """
        # Get current profile spectrum
        result = await db.execute(
            select(UserProfile).where(UserProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return {"error": "Profile not found", "applied": []}

        current_spectrum = {
            dim: getattr(profile, dim, 3) for dim in SPECTRUM_DIMS
        }

        # Get all unapplied insights
        result = await db.execute(
            select(IterationInsight)
            .where(
                and_(
                    IterationInsight.profile_id == profile_id,
                    IterationInsight.is_applied == False,
                )
            )
            .order_by(IterationInsight.created_at.desc())
        )
        pending_insights = list(result.scalars().all())

        if not pending_insights:
            return {"message": "No pending insights to apply", "applied": []}

        # Group by dimension and direction sign
        by_dimension: dict[str, dict[int, list[IterationInsight]]] = {}
        for ins in pending_insights:
            if ins.dimension not in by_dimension:
                by_dimension[ins.dimension] = {1: [], -1: []}
            sign = 1 if ins.direction > 0 else -1
            by_dimension[ins.dimension][sign].append(ins)

        applied = []
        now = datetime.now(timezone.utc)

        for dim, sign_groups in by_dimension.items():
            current_val = current_spectrum.get(dim, 3)
            if current_val is None:
                continue

            for sign, insights_list in sign_groups.items():
                if not insights_list:
                    continue

                # Determine the net direction and magnitude
                # Sum the directions (each is -2 to +2)
                total_direction = sum(ins.direction for ins in insights_list)
                avg_confidence = sum(ins.confidence for ins in insights_list) / len(insights_list)

                # Normalize to -2..+2
                net_direction = max(-2, min(2, round(total_direction / len(insights_list))))
                abs_magnitude = abs(net_direction)

                if abs_magnitude == 0:
                    continue

                # Check consensus threshold
                required_insights = CONSENSUS_THRESHOLDS.get(abs_magnitude, 2)
                if len(insights_list) < required_insights:
                    logger.debug(
                        "Insufficient consensus for %s shift: %d/%d insights",
                        dim, len(insights_list), required_insights,
                    )
                    continue

                # Compute target value with stability guard
                adjustment = net_direction * avg_confidence * (1.0 - stability)
                new_val = round(current_val + adjustment)
                new_val = max(1, min(5, new_val))

                if new_val == current_val:
                    continue

                # Apply the adjustment
                setattr(profile, dim, new_val)

                # Mark all contributing insights as applied
                for ins in insights_list:
                    ins.is_applied = True
                    ins.applied_at = now
                    ins.previous_value = current_val
                    ins.new_value = new_val

                applied.append({
                    "dimension": dim,
                    "previous_value": current_val,
                    "new_value": new_val,
                    "adjustment": new_val - current_val,
                    "net_direction": net_direction,
                    "avg_confidence": round(avg_confidence, 2),
                    "contributing_insights": len(insights_list),
                    "rationale": insights_list[0].rationale or "多个反思洞察的共识结果",
                })

                logger.info(
                    "Applied profile shift: %s %d→%d (%d insights, conf=%.2f)",
                    dim, current_val, new_val, len(insights_list), avg_confidence,
                )

        if applied and auto_commit:
            await db.commit()

        return {
            "applied": applied,
            "total_pending_before": len(pending_insights),
            "remaining_pending": len(pending_insights) - sum(
                a["contributing_insights"] for a in applied
            ),
            "stability": stability,
        }

    # ── Evolution History ────────────────────────────────────────────────────

    @staticmethod
    async def get_evolution_history(
        db: AsyncSession,
        profile_id: int,
        dimension: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get the profile evolution timeline as a list of applied insights."""
        stmt = (
            select(IterationInsight)
            .where(
                and_(
                    IterationInsight.profile_id == profile_id,
                    IterationInsight.is_applied == True,
                )
            )
            .order_by(IterationInsight.applied_at.desc())
            .limit(limit)
        )
        if dimension:
            stmt = stmt.where(IterationInsight.dimension == dimension)

        result = await db.execute(stmt)
        insights = result.scalars().all()

        return [
            {
                "id": ins.id,
                "dimension": ins.dimension,
                "direction": ins.direction,
                "confidence": ins.confidence,
                "previous_value": ins.previous_value,
                "new_value": ins.new_value,
                "rationale": ins.rationale,
                "evidence": ins.evidence,
                "applied_at": ins.applied_at.isoformat() if ins.applied_at else None,
                "source_reflection_id": ins.source_reflection_id,
            }
            for ins in insights
        ]

    @staticmethod
    async def get_evolution_summary(
        db: AsyncSession,
        profile_id: int,
    ) -> dict:
        """Get a summary of the user's methodological evolution."""
        history = await ProfileIterator.get_evolution_history(db, profile_id)

        if not history:
            return {"message": "尚未有画像迭代记录", "total_shifts": 0, "by_dimension": {}}

        by_dim: dict[str, list] = {}
        for entry in history:
            dim = entry["dimension"]
            if dim not in by_dim:
                by_dim[dim] = []
            by_dim[dim].append(entry)

        summary = {
            "total_shifts": len(history),
            "by_dimension": {
                dim: {
                    "shift_count": len(entries),
                    "net_change": sum(e["new_value"] - e["previous_value"] for e in entries if e["new_value"] is not None and e["previous_value"] is not None),
                    "latest": entries[0] if entries else None,
                    "first": entries[-1] if entries else None,
                }
                for dim, entries in by_dim.items()
            },
        }
        return summary
