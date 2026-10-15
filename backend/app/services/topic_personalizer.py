"""
P1 — Topic Personalizer service.

Reads UserProfile + ResearchInterestProfile and generates personalised
parameters that drive the enhanced topic argumentation pipeline.

The personalised "memory" competitive barrier: each user's guidance gets
increasingly tailored across projects as their ResearchInterestProfile
accumulates topic, methodology, and theory preference data.
"""
import json
import logging
import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import UserProfile, ResearchInterestProfile

logger = logging.getLogger(__name__)


@dataclass
class PersonalizationParams:
    """Personalised parameters injected into topic argumentation prompts."""
    argumentation_depth: str = "balanced"       # shallow | balanced | deep
    argumentation_breadth: str = "moderate"      # focused | moderate | wide
    method_rigidity: str = "flexible"            # rigorous | balanced | flexible
    favored_methods: list[str] = field(default_factory=list)
    disfavored_methods: list[str] = field(default_factory=list)
    writing_style: str = "balanced"              # formal | balanced | accessible
    instruction_density: str = "standard"        # minimal | standard | detailed
    citation_depth: str = "moderate"             # light | moderate | heavy
    preferred_paradigm: str = "qualitative"
    theory_inclination: str = "practical"        # theoretical | balanced | practical
    recommended_theories: list[str] = field(default_factory=list)
    interest_disciplines: list[str] = field(default_factory=list)
    interest_topics: list[str] = field(default_factory=list)
    citation_comfort_level: int = 3

    def to_prompt_block(self) -> str:
        """Render personalization params as a system prompt injection block."""
        depth_map = {
            "shallow": "简明扼要，抓核心要点",
            "balanced": "深度与广度兼顾",
            "deep": "深度分析，充分展开",
        }
        breadth_map = {
            "focused": "聚焦核心问题深入分析",
            "moderate": "适度展开相关维度",
            "wide": "广泛覆盖多个相关维度",
        }
        rig_map = {
            "rigorous": "偏好严谨规范的方法，重视信效度和可复制性",
            "balanced": "规范性与灵活性兼顾",
            "flexible": "偏好灵活适应的方法，重视情境适配",
        }
        style_map = {
            "formal": "学术正式风格，注重术语精确和逻辑严密",
            "balanced": "学术性与可读性平衡",
            "accessible": "通俗易懂，注重可操作性",
        }
        inst_map = {
            "minimal": "精简指导，给核心方向即可",
            "standard": "标准指导，提供具体建议和示例",
            "detailed": "详尽指导，逐步拆解操作细节",
        }
        cit_map = {
            "light": "少量关键文献引用即可",
            "moderate": "适度引用相关文献支撑论点",
            "heavy": "充分引用文献，展示学术脉络",
        }
        theory_map = {
            "theoretical": "偏好理论建构和概念分析",
            "balanced": "理论与经验并重",
            "practical": "偏好经验导向和实操指导",
        }

        lines = ["## 个性化参数（根据您的画像自动调整）", ""]
        lines.append(f"- 论证深度: {depth_map.get(self.argumentation_depth, '适中')}")
        lines.append(f"- 论证广度: {breadth_map.get(self.argumentation_breadth, '适中')}")
        lines.append(f"- 方法论倾向: {rig_map.get(self.method_rigidity, '灵活')}")
        if self.favored_methods:
            lines.append(f"- 推荐方法: {', '.join(self.favored_methods)}")
        if self.disfavored_methods:
            lines.append(f"- 慎用方法: {', '.join(self.disfavored_methods)}")
        lines.append(f"- 语言风格: {style_map.get(self.writing_style, '平衡')}")
        lines.append(f"- 指导密度: {inst_map.get(self.instruction_density, '标准')}")
        lines.append(f"- 文献引用: {cit_map.get(self.citation_depth, '适中')}")
        lines.append(f"- 研究范式: {self.preferred_paradigm}")
        lines.append(f"- 理论倾向: {theory_map.get(self.theory_inclination, '平衡')}")
        if self.recommended_theories:
            lines.append(f"- 推荐理论视角: {', '.join(self.recommended_theories)}")
        if self.interest_disciplines:
            lines.append(f"- 关注学科: {', '.join(self.interest_disciplines)}")
        if self.interest_topics:
            lines.append(f"- 关注主题: {', '.join(self.interest_topics[:10])}")
        lines.append("")
        lines.append("请严格按照以上参数调整输出。")
        return "\n".join(lines)


class TopicPersonalizer:
    """Generates PersonalizationParams from user profile data.

    Combines explicit preferences (UserProfile) with accumulated behavioural
    data (ResearchInterestProfile) to produce a rich parameter set that
    tailors every topic argumentation session.
    """

    @staticmethod
    def _json_list(raw: str, default: list | None = None) -> list:
        if default is None:
            default = []
        try:
            val = json.loads(raw)
            return val if isinstance(val, list) else default
        except (json.JSONDecodeError, TypeError):
            return default

    async def personalize(
        self, db: AsyncSession, profile_id: int,
    ) -> PersonalizationParams:
        """Build personalised parameters for a given user profile."""
        params = PersonalizationParams()

        # 1. Load UserProfile
        profile: UserProfile | None = None
        try:
            result = await db.execute(
                select(UserProfile).where(UserProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
        except Exception as e:
            logger.warning("Profile lookup failed: %s", e)

        if profile is None:
            logger.info("No UserProfile for id=%s, returning defaults", profile_id)
            return params

        # 2. Load ResearchInterestProfile (may not exist yet)
        interest: ResearchInterestProfile | None = None
        try:
            result = await db.execute(
                select(ResearchInterestProfile).where(
                    ResearchInterestProfile.profile_id == profile_id
                )
            )
            interest = result.scalar_one_or_none()
        except Exception:
            logger.debug("ResearchInterestProfile lookup failed (table may not exist)")

        # 3. Derive from UserProfile spectrum dimensions
        params.preferred_paradigm = profile.paradigm_preference

        ad = profile.analysis_depth
        if ad <= 2:
            params.argumentation_depth, params.argumentation_breadth = "shallow", "wide"
        elif ad >= 4:
            params.argumentation_depth, params.argumentation_breadth = "deep", "focused"

        mr = profile.methodological_rigidity
        if mr <= 2:
            params.method_rigidity = "rigorous"
        elif mr >= 4:
            params.method_rigidity = "flexible"

        ws = profile.writing_style
        if ws <= 2:
            params.writing_style = "formal"
        elif ws >= 4:
            params.writing_style = "accessible"

        lp = profile.learning_preference
        if lp <= 2 or profile.experience_level == "beginner":
            params.instruction_density = "detailed"
        elif lp >= 4 and profile.experience_level == "advanced":
            params.instruction_density = "minimal"

        td = profile.theory_driven
        if td <= 2:
            params.theory_inclination = "theoretical"
        elif td >= 4:
            params.theory_inclination = "practical"

        cd = profile.tech_dependency
        if cd <= 2:
            params.citation_depth = "light"
        elif cd >= 4:
            params.citation_depth = "heavy"

        # 4. Enrich from ResearchInterestProfile
        if interest is not None:
            params.interest_disciplines = self._json_list(interest.discipline_tags_json)
            params.interest_topics = self._json_list(interest.topic_keywords_json)
            method_history = self._json_list(interest.methodology_history_json)
            if method_history:
                params.favored_methods = list(dict.fromkeys(method_history))[:5]
            theories = self._json_list(interest.theory_preferences_json)
            if theories:
                params.recommended_theories = list(dict.fromkeys(theories))[:5]
            if interest.previous_projects_count >= 3:
                params.argumentation_depth = "deep"
            if interest.completed_projects_count >= 2:
                if params.instruction_density == "standard":
                    params.instruction_density = "minimal"
            params.citation_comfort_level = interest.citation_comfort_level
            if interest.citation_comfort_level >= 4:
                params.citation_depth = "heavy"

        # 5. Paradigm-specific method defaults
        if profile.paradigm_preference == "qualitative":
            if not params.favored_methods:
                params.favored_methods = ["深度访谈", "参与观察", "焦点小组", "个案研究"]
            params.disfavored_methods = ["大规模问卷调查", "实验设计", "结构方程模型"]
        elif profile.paradigm_preference == "quantitative":
            if not params.favored_methods:
                params.favored_methods = ["问卷调查", "统计分析", "量表开发", "实验设计"]
            params.disfavored_methods = ["民族志", "深度访谈", "叙事分析"]

        logger.info(
            "Personalized for profile %s: depth=%s paradigm=%s methods=%d",
            profile_id, params.argumentation_depth,
            params.preferred_paradigm, len(params.favored_methods),
        )
        return params

    async def update_interests(
        self,
        db: AsyncSession,
        profile_id: int,
        topic: str,
        paradigm: str,
        project_id: int | None = None,
        discipline_tags: list[str] | None = None,
        methodology_used: list[str] | None = None,
        theories_referenced: list[str] | None = None,
    ) -> ResearchInterestProfile | None:
        """Update or create ResearchInterestProfile after topic argumentation."""
        try:
            result = await db.execute(
                select(ResearchInterestProfile).where(
                    ResearchInterestProfile.profile_id == profile_id
                )
            )
            interest = result.scalar_one_or_none()
            is_new = interest is None

            if is_new:
                interest = ResearchInterestProfile(profile_id=profile_id)
                db.add(interest)

            if discipline_tags:
                existing = self._json_list(interest.discipline_tags_json)
                merged = list(dict.fromkeys(existing + discipline_tags))[:15]
                interest.discipline_tags_json = json.dumps(merged, ensure_ascii=False)

            if topic:
                existing_topics = self._json_list(interest.topic_keywords_json)
                extracted = re.findall(r'[一-鿿]{2,4}', topic)
                merged_topics = list(dict.fromkeys(
                    existing_topics + [t for t in extracted if t not in existing_topics]
                ))[:30]
                interest.topic_keywords_json = json.dumps(merged_topics, ensure_ascii=False)

            if methodology_used:
                existing_methods = self._json_list(interest.methodology_history_json)
                merged_methods = list(dict.fromkeys(
                    existing_methods + methodology_used
                ))[:20]
                interest.methodology_history_json = json.dumps(
                    merged_methods, ensure_ascii=False,
                )

            if theories_referenced:
                existing_theories = self._json_list(interest.theory_preferences_json)
                merged_theories = list(dict.fromkeys(
                    existing_theories + theories_referenced
                ))[:15]
                interest.theory_preferences_json = json.dumps(
                    merged_theories, ensure_ascii=False,
                )

            if is_new:
                interest.previous_projects_count = 1
            interest.topic_refinement_iterations += 1
            interest.last_topic = topic[:200]
            interest.last_paradigm = paradigm
            if project_id:
                interest.last_project_id = project_id

            await db.commit()
            await db.refresh(interest)

            logger.info(
                "Updated ResearchInterestProfile profile=%s new=%s",
                profile_id, is_new,
            )
            return interest
        except Exception as e:
            logger.warning("Failed to update ResearchInterestProfile: %s", e)
            await db.rollback()
            return None


# Singleton
_topic_personalizer: TopicPersonalizer | None = None


def get_topic_personalizer() -> TopicPersonalizer:
    global _topic_personalizer
    if _topic_personalizer is None:
        _topic_personalizer = TopicPersonalizer()
    return _topic_personalizer
