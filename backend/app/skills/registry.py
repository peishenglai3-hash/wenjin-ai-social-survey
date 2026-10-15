"""Skill registry — stores available skills and routes requests."""

from app.skills.base import BaseSkill, SkillResult


class SkillRegistry:
    """Holds all registered skills and dispatches to the best match."""

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> BaseSkill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[dict]:
        return [
            {"name": s.name, "description": s.description, "version": s.version}
            for s in self._skills.values()
        ]

    async def route(
        self, ai_service, user_intent: str, user_input: dict, context: dict | None = None
    ) -> SkillResult:
        """Select the best-matching skill and execute it.

        Falls back to asking the LLM to classify the intent if no skill
        scores above threshold.
        """
        # Direct match first
        best, best_score = None, 0.0
        for skill in self._skills.values():
            score = skill.match(user_intent)
            if score > best_score:
                best_score = score
                best = skill

        if best and best_score > 0.5:
            return await best.execute(ai_service, user_input, context)

        # Fallback: use LLM to classify intent and pick skill
        skill_list = "\n".join(
            f"- {s.name}: {s.description}" for s in self._skills.values()
        )
        classify_prompt = (
            f"用户意图: {user_intent}\n\n"
            f"可用技能:\n{skill_list}\n\n"
            "选择最匹配的技能名（只回复技能名，不要解释）："
        )
        skill_name = await ai_service.chat(
            [{"role": "user", "content": classify_prompt}],
            temperature=0.0,
            max_tokens=32,
        )
        skill_name = skill_name.strip().lower()
        skill = self._skills.get(skill_name)
        if skill:
            return await skill.execute(ai_service, user_input, context)

        # Ultimate fallback
        return SkillResult(
            content=f"No matching skill found for intent '{user_intent}'. "
            f"Available skills: {list(self._skills.keys())}"
        )


# Global singleton
skill_registry = SkillRegistry()
