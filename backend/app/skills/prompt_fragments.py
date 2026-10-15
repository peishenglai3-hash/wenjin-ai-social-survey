"""Small, public prompt-fragment library used by :mod:`cluster_router`.

The fragments are generic product configuration, not a bundled research corpus.
Deployments may extend this module with their own licensed prompts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PromptFragment:
    """One deterministic prompt fragment selected by a profile dimension."""

    id: str
    dimension: str
    value: str
    content: str
    priority: int = 3

    def to_dict(self) -> dict:
        return asdict(self)


_FRAGMENT_DEFINITIONS = [
    # Role
    {"id": "role_undergraduate", "dimension": "role", "value": "undergraduate", "priority": 5,
     "content": "当前使用者是本科生。解释关键概念，保留思考空间，并把建议拆成可执行的研究步骤。"},
    {"id": "role_graduate", "dimension": "role", "value": "graduate", "priority": 5,
     "content": "当前使用者是硕士研究生。优先澄清研究问题、理论对话、方法选择和证据边界。"},
    {"id": "role_faculty", "dimension": "role", "value": "faculty", "priority": 5,
     "content": "当前使用者是高校教师或研究指导者。突出可审阅的研究设计、证据质量和团队协作边界，面向高校教师组织输出。"},
    {"id": "role_practitioner", "dimension": "role", "value": "practitioner", "priority": 4,
     "content": "当前使用者是实务工作者。先给出场景、约束、行动步骤和风险，再补充必要的方法论说明。"},
    {"id": "role_researcher", "dimension": "role", "value": "researcher", "priority": 4,
     "content": "当前使用者是研究人员。优先呈现可核验的证据链、方法选择和研究限制。"},
    # Paradigm
    {"id": "paradigm_qualitative", "dimension": "paradigm", "value": "qualitative", "priority": 5,
     "content": "研究范式偏向质性研究。强调语境、过程、意义、反身性、引文证据和解释边界。"},
    {"id": "paradigm_quantitative", "dimension": "paradigm", "value": "quantitative", "priority": 5,
     "content": "研究范式偏向量化研究。明确变量、测量、样本、统计假设、不确定性和效应解释。"},
    {"id": "paradigm_mixed", "dimension": "paradigm", "value": "mixed", "priority": 4,
     "content": "研究范式采用混合方法。说明定性与定量证据如何互相补充，以及整合发生在哪个阶段。"},
    # Experience
    {"id": "experience_beginner", "dimension": "experience", "value": "beginner", "priority": 4,
     "content": "使用者刚开始研究。先说明术语，再提供最小可行步骤和一个低风险例子。"},
    {"id": "experience_intermediate", "dimension": "experience", "value": "intermediate", "priority": 3,
     "content": "使用者已有一定经验。可以直接讨论取舍、替代方案和验证方法。"},
    {"id": "experience_advanced", "dimension": "experience", "value": "advanced", "priority": 4,
     "content": "使用者具有较强研究经验。优先指出识别假设、反例、偏差和可复现性要求。"},
    # Scenario
    {"id": "scenario_fieldwork", "dimension": "scenario", "value": "fieldwork", "priority": 5,
     "content": "当前场景是田野工作。优先考虑知情同意、受访者安全、现场关系、记录最小化和撤回路径。"},
    {"id": "scenario_seminar", "dimension": "scenario", "value": "seminar", "priority": 3,
     "content": "当前场景是研究讨论。把主张、证据、反对意见和待验证问题分开呈现。"},
    {"id": "scenario_classroom", "dimension": "scenario", "value": "classroom", "priority": 3,
     "content": "当前场景是课程学习。使用清晰例子，鼓励独立判断，不把生成内容当成标准答案。"},
    # Theme
    {"id": "theme_academic", "dimension": "theme", "value": "academic", "priority": 4,
     "content": "输出采用学术研究语体，明确概念、来源、方法和局限，不夸大结论。"},
    {"id": "theme_government", "dimension": "theme", "value": "government", "priority": 4,
     "content": "输出面向治理实践，区分事实、判断和建议，给出可执行但不过度承诺的行动项。"},
    {"id": "theme_youth", "dimension": "theme", "value": "youth", "priority": 3,
     "content": "输出面向青年学习者，语言亲切但保留方法边界，鼓励提出下一步问题。"},
    # Reflection triggers
    {"id": "reflect_fieldwork", "dimension": "reflection_trigger", "value": "fieldwork_completed", "priority": 5,
     "content": "田野阶段刚结束。请回顾记录完整性、位置性、伦理事件、未追问线索和下一轮访谈计划。"},
    {"id": "reflect_analysis", "dimension": "reflection_trigger", "value": "analysis_completed", "priority": 4,
     "content": "分析阶段刚结束。请检查证据链、替代解释、负例、编码一致性和结论的适用范围。"},
    {"id": "reflect_project_start", "dimension": "reflection_trigger", "value": "project_started", "priority": 3,
     "content": "项目刚开始。请先定义研究问题、数据边界、角色责任、保留期限和成功标准。"},
]

_ALL = [PromptFragment(**item) for item in _FRAGMENT_DEFINITIONS]
ALL_FRAGMENTS: dict[str, list[PromptFragment]] = {}
for _fragment in _ALL:
    ALL_FRAGMENTS.setdefault(_fragment.dimension, []).append(_fragment)


def list_all_fragments() -> list[dict]:
    """Return serializable definitions for inspection and tests."""
    return [fragment.to_dict() for fragment in _ALL]


def get_fragments_by_dimension(dimension: str) -> list[PromptFragment]:
    """Return fragments in one dimension, or an empty list if unknown."""
    return list(ALL_FRAGMENTS.get(dimension, []))


def find_fragment(dimension: str, value: str) -> PromptFragment | None:
    """Find an exact profile/value match without fuzzy guessing."""
    for fragment in ALL_FRAGMENTS.get(dimension, []):
        if fragment.value == value:
            return fragment
    return None
