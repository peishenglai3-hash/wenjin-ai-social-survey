"""ClusterRouter — intelligently assembles prompt fragments for personalized AI guidance.

Architecture:
  User Profile → ClusterRouter.match(profile) → assembled system prompt
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
  role frag     paradigm frag  experience frag
  scenario frag theme frag    spectrum frags
                   │
                   ▼
        Sorted by priority → merged prompt
"""

from __future__ import annotations

import logging
from typing import Any

from app.skills.prompt_fragments import (
    PromptFragment,
    ALL_FRAGMENTS,
    find_fragment,
    list_all_fragments,
)

logger = logging.getLogger(__name__)

PROFILE_TO_DIMENSION = {
    "role": "role",
    "paradigm_preference": "paradigm",
    "experience_level": "experience",
    "scenario_preference": "scenario",
    "theme_preference": "theme",
}


class ClusterRouter:
    """Assembles prompt fragments based on user identity dimensions."""

    def __init__(self):
        self._fragments: dict[str, list[PromptFragment]] = dict(ALL_FRAGMENTS)

    def match(self, profile: dict[str, Any]) -> list[PromptFragment]:
        """Match all applicable fragments for a given profile, sorted by priority (highest first)."""
        matched: list[PromptFragment] = []
        for profile_field, dim_name in PROFILE_TO_DIMENSION.items():
            value = profile.get(profile_field)
            if not value:
                continue
            frag = find_fragment(dim_name, value)
            if frag:
                matched.append(frag)
        return sorted(matched, key=lambda f: f.priority, reverse=True)

    def match_with_context(
        self, profile: dict[str, Any], extra_context: dict[str, str] | None = None,
    ) -> list[PromptFragment]:
        """Match fragments with extra context dimensions (e.g., reflection_trigger)."""
        matched = self.match(profile)
        if extra_context:
            for dim_name, value in extra_context.items():
                if not value:
                    continue
                frag = find_fragment(dim_name, value)
                if frag:
                    matched.append(frag)
        return sorted(matched, key=lambda f: f.priority, reverse=True)

    def assemble(
        self, profile: dict[str, Any],
        extra_context: dict[str, str] | None = None,
        base_prompt: str = "",
        separator: str = "\n\n",
    ) -> str:
        """Assemble a full personalized system prompt from matched fragments."""
        fragments = self.match_with_context(profile, extra_context)
        if not fragments:
            return base_prompt
        parts = []
        if base_prompt:
            parts.append(base_prompt)
        parts.append("## 用户个性化引导\n")
        for frag in fragments:
            parts.append(frag.content)
        result = separator.join(parts)
        logger.debug("Assembled prompt from %d fragments (%d chars)", len(fragments), len(result))
        return result

    def assemble_compact(
        self, profile: dict[str, Any],
        extra_context: dict[str, str] | None = None,
    ) -> str:
        """Compact assembly — one line, suitable for token-constrained contexts."""
        fragments = self.match_with_context(profile, extra_context)
        if not fragments:
            return ""
        return "[个性化引导] " + " | ".join(f"#{f.id}" for f in fragments)

    def describe_match(self, profile: dict[str, Any]) -> dict:
        """Return a descriptive summary of which fragments matched."""
        fragments = self.match(profile)
        return {
            "profile_summary": {
                k: profile.get(k) for k in
                ["role", "paradigm_preference", "experience_level",
                 "scenario_preference", "theme_preference"] if k in profile
            },
            "matched_fragments": [
                {"id": f.id, "dimension": f.dimension, "value": f.value, "priority": f.priority}
                for f in fragments
            ],
            "fragment_count": len(fragments),
        }

    def list_available_clusters(self) -> dict[str, list[str]]:
        """List all available fragment clusters by dimension."""
        return {dim: [f.value for f in frags] for dim, frags in self._fragments.items()}


cluster_router = ClusterRouter()
