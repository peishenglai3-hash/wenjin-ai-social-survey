"""Reference Membrane — 隔膜式参考资料系统。

A semi-permeable reference layer between researcher and field that:
1. Filters raw observations through domain-specific frameworks
2. Provides contextual knowledge at the right level of abstraction
3. Acts as a "theoretical membrane" — selectively permeable to different
   types of information based on the research mode

Each mode gets its own membrane configuration:
- Academic: theory-first → empirical grounding
- Government: problem-first → policy alignment
- Youth: curiosity-first → guided discovery
"""

from dataclasses import dataclass, field
from typing import Literal

Mode = Literal["academic", "government", "youth"]


@dataclass
class MembraneLayer:
    """One layer of the reference membrane — a specific analytical lens."""
    name: str
    description: str
    canonical_texts: list[str] = field(default_factory=list)
    guiding_questions: list[str] = field(default_factory=list)
    filter_rules: list[str] = field(default_factory=list)


# ── Academic Mode Membrane ─────────────────────────────────────────────

ACADEMIC_MEMBRANE = [
    MembraneLayer(
        name="理论透镜 (Theoretical Lens)",
        description="将田野观察与既有社会学理论建立对话",
        canonical_texts=[
            "布迪厄《实践感》— 惯习、场域、资本",
            "吉登斯《社会的构成》— 结构化理论",
            "戈夫曼《日常生活中的自我呈现》— 拟剧论",
            "格兰诺维特《镶嵌》— 社会网络理论",
            "斯科特《弱者的武器》— 日常抵抗",
        ],
        guiding_questions=[
            "这个现象与哪些既有理论对话？是印证、修正还是挑战？",
            "如何将本土经验概念化，使其具备理论贡献潜力？",
            "研究发现的边界条件是什么？在何种情境下可推广？",
        ],
        filter_rules=[
            "通过：有理论脉络的现象描述、可操作化的概念、可比较的数据",
            "阻挡：纯轶事描述、无理论定位的发现、无法验证的主张",
        ],
    ),
    MembraneLayer(
        name="方法论审视 (Methodological Scrutiny)",
        description="确保研究过程的方法论严谨性",
        canonical_texts=[
            "陈向明《质的研究方法与社会科学研究》",
            "巴比《社会研究方法》",
            "格尔茨《文化的解释》— 深描",
        ],
        guiding_questions=[
            "当前证据的强度如何？是否存在替代解释？",
            "样本/案例的选择是否存在偏差？对结论的影响？",
            "研究者自身的立场和预设如何影响观察？",
        ],
        filter_rules=[
            "通过：有方法论自觉的发现、可追溯的推理过程",
            "阻挡：无根据的因果断言、无反思的研究者立场",
        ],
    ),
    MembraneLayer(
        name="文献定位 (Literature Positioning)",
        description="将发现锚定在学术文献脉络中",
        canonical_texts=[
            "定期检索 Web of Science / CNKI / Google Scholar",
            "跟踪关键期刊的最新发表",
        ],
        guiding_questions=[
            "类似主题已有哪些研究？本研究填补了什么空白？",
            "与已有研究的一致点和分歧点在哪里？",
            "是否可以与相邻学科的研究对话？",
        ],
        filter_rules=[
            "通过：有文献定位的发现、有引证价值的结论",
            "阻挡：已知常识的重述、已经被充分研究的话题",
        ],
    ),
]

# ── Government Mode Membrane ───────────────────────────────────────────

GOVERNMENT_MEMBRANE = [
    MembraneLayer(
        name="政策对齐 (Policy Alignment)",
        description="将调研发现与现行政策体系对接",
        canonical_texts=[
            "最新年度政府工作报告",
            "相关领域五年规划文件",
            "所属省市政策文件与实施细则",
            "国务院相关指导意见",
        ],
        guiding_questions=[
            "调研中发现的问题是否已有政策覆盖？政策落地的堵点在哪里？",
            "基层执行中存在哪些'最后一公里'问题？",
            "调研发现能为政策完善提供什么具体建议？",
        ],
        filter_rules=[
            "通过：有政策对应关系的发现、可操作的对策建议",
            "阻挡：脱离政策语境的批评、无建设性的抱怨",
        ],
    ),
    MembraneLayer(
        name="利益相关方图谱 (Stakeholder Mapping)",
        description="识别和分析所有受影响的利益群体",
        canonical_texts=[
            "基层治理案例汇编",
            "群众工作方法论",
        ],
        guiding_questions=[
            "谁受益？谁受损？谁有话语权？谁被忽视？",
            "不同利益群体的诉求如何平衡？",
            "政策的'非意图后果'可能影响哪些群体？",
        ],
        filter_rules=[
            "通过：有利益相关方分析的发现、有成本收益考量的建议",
            "阻挡：只考虑单一视角的分析、忽视弱势群体的方案",
        ],
    ),
    MembraneLayer(
        name="可行性评估 (Feasibility Assessment)",
        description="评估建议的行政可行性和资源约束",
        canonical_texts=[
            "地方政府财政预算报告",
            "基层干部访谈记录",
        ],
        guiding_questions=[
            "建议在现有行政体系下是否可操作？需要哪些资源？",
            "实施难度和优先级如何排序？",
            "是否有可复制的成功案例？",
        ],
        filter_rules=[
            "通过：有实施路径的建议、有资源估算的方案",
            "阻挡：脱离行政现实的一厢情愿、不考虑财政约束的建议",
        ],
    ),
]

# ── Youth Mode Membrane ────────────────────────────────────────────────

YOUTH_MEMBRANE = [
    MembraneLayer(
        name="概念桥接 (Concept Bridging)",
        description="将日常生活现象与学术概念建立联系",
        canonical_texts=[
            "吉登斯《社会学》基础版",
            "费孝通《乡土中国》— 入门必读",
            "马克思《资本论》通俗解读",
            "当代社会热点事件报道与分析",
        ],
        guiding_questions=[
            "你观察到的现象和社会学课上学过的哪个概念有关？",
            "能不能用你自己的话解释这个现象的深层原因？",
            "如果你要向同学介绍这个发现，你会怎么说？",
        ],
        filter_rules=[
            "通过：有学习价值的观察、可关联课程内容的发现",
            "阻挡：纯主观判断、无分析的努力、脱离语境的结论",
        ],
    ),
    MembraneLayer(
        name="反思性对话 (Reflective Dialogue)",
        description="通过提问引导学习者自我发现和批判性思考",
        canonical_texts=[
            "弗莱雷《被压迫者教育学》— 提问式教育",
            "杜威《我们如何思维》— 反思性思维",
        ],
        guiding_questions=[
            "看到这个现象，你的第一反应是什么？为什么会这样反应？",
            "如果你的立场不同（换个阶层/性别/地域），会看到什么不同？",
            "这个现象让你想到了自己生活中的什么经历？",
        ],
        filter_rules=[
            "通过：有自我反思的观察、有批判意识的思考",
            "阻挡：不经反思的刻板印象复制、人云亦云的判断",
        ],
    ),
    MembraneLayer(
        name="实践导向 (Action Orientation)",
        description="将知识学习转化为实践行动",
        canonical_texts=[
            "毛泽东《实践论》《矛盾论》",
            "社区服务学习指南",
        ],
        guiding_questions=[
            "了解了这个现象后，你觉得可以做什么（哪怕是小事）？",
            "如果要更深入了解，下一步可以找谁聊聊？去哪里看看？",
            "你的观察是否可以转化为一个小型研究项目？",
        ],
        filter_rules=[
            "通过：有实践意愿的反思、有下一步行动计划的思考",
            "阻挡：纯书斋式的空谈、无实践连接的理论推演",
        ],
    ),
]


# ── Membrane Registry ──────────────────────────────────────────────────

MEMBRANES: dict[Mode, list[MembraneLayer]] = {
    "academic": ACADEMIC_MEMBRANE,
    "government": GOVERNMENT_MEMBRANE,
    "youth": YOUTH_MEMBRANE,
}


def get_membrane(theme: str) -> list[MembraneLayer]:
    """Return the reference membrane for a given mode."""
    return MEMBRANES.get(theme, ACADEMIC_MEMBRANE)


def build_membrane_prompt(theme: str, context: dict | None = None) -> str:
    """Build a system prompt that activates the reference membrane for the mode."""
    layers = get_membrane(theme)
    if not layers:
        return ""

    ctx_str = ""
    if context:
        research_topic = context.get("research_topic", "")
        field_phase = context.get("phase", "")
        if research_topic:
            ctx_str += f"\n当前研究主题：{research_topic}"
        if field_phase:
            ctx_str += f"\n当前工作阶段：{field_phase}"

    lines = [
        "## 参考资料隔膜 (Reference Membrane)\n",
        "你作为'隔膜式参考系统'，在半透膜的一侧提供领域知识，"
        "让用户在自己的田野情境中理解和应用这些知识。\n",
        "原则：",
        "- 选择性渗透：只提供与当前需求相关的参考，不信息过载",
        "- 情境转化：将抽象理论转化为用户可理解、可应用的形式",
        "- 双向调节：既提供上位知识（理论/政策），也吸收下位经验（田野观察）",
        "- 保持间距：提供参考框架但不替代用户自己的分析判断\n",
        f"当前模式：{theme}{ctx_str}\n",
        "可用参考层：",
    ]

    for i, layer in enumerate(layers, 1):
        lines.append(f"\n### 第{i}层：{layer.name}")
        lines.append(f"\n{layer.description}\n")
        if layer.canonical_texts:
            lines.append("**经典参考**：")
            for text in layer.canonical_texts:
                lines.append(f"- {text}")
            lines.append("")
        if layer.guiding_questions:
            lines.append("**引导问题**：")
            for q in layer.guiding_questions:
                lines.append(f"- {q}")
            lines.append("")

    return "\n".join(lines)


def apply_membrane_filter(theme: str, raw_content: str) -> str:
    """Apply the membrane filter to raw content, annotating context."""
    layers = get_membrane(theme)
    annotations = []
    for layer in layers:
        annotations.append(f"[通过{layer.name}]")
    return f"{' '.join(annotations)}\n\n{raw_content}"


# ── Skill wrapper ─────────────────────────────────────────────────────

from app.skills.base import BaseSkill, SkillResult


class ReferenceMembraneSkill(BaseSkill):
    """Skill: activate the reference membrane for contextual analysis.

    Wraps user content through mode-specific membrane layers before
    passing to the LLM for analysis, ensuring mode-appropriate framing.
    """

    name = "reference_membrane"
    description = "隔膜式参考资料：通过模式特定的理论/政策/学习透镜过滤和增强分析"
    version = "1.0.0"

    def system_prompt(self, context: dict | None = None) -> str:
        theme = (context or {}).get("theme", "academic")
        return build_membrane_prompt(theme, context)

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "待分析的原始内容"},
                "theme": {"type": "string", "enum": ["academic", "government", "youth"]},
                "stage": {"type": "string", "description": "当前工作阶段ID"},
            },
            "required": ["content"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "参考", "理论", "框架", "膜", "透镜", "视角", "分析框架",
            "reference", "framework", "lens", "membrane",
            "用什么理论", "怎么分析", "从什么角度", "怎么理解",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.15, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        theme = user_input.get("theme", (context or {}).get("theme", "academic"))
        content = user_input.get("content", "")
        stage = user_input.get("stage", "")

        membrane_prompt = self.system_prompt({"theme": theme, "phase": stage})

        from app.skills.mode_prompts import build_deep_heterogeneity_prompt
        hetero_prompt = build_deep_heterogeneity_prompt(theme, stage)

        messages = [
            {"role": "system", "content": f"{membrane_prompt}\n\n{hetero_prompt}"},
            {"role": "user", "content": content},
        ]

        response = await ai_service.chat(messages, temperature=0.5, max_tokens=4096)
        return SkillResult(content=response, metadata={"theme": theme, "stage": stage})
