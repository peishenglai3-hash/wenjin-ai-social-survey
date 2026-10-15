"""Prompt Distillation — structured extraction of design patterns from system prompts.

构想一的核心工具：从开源项目的 system prompt 中提取可复用的设计模式，
转化为"光谱化用户设计"的 prompt 构建知识。

Architecture:
  Source Prompts → Pattern Extractor → Design Pattern Catalog → Prompt Builder
  (open-source)    (LLM-assisted)     (structured JSON)       (mode_prompts.py)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PromptPattern:
    """One extracted design pattern from a source system prompt."""
    id: str
    name: str
    category: str  # role | structure | constraint | style | meta
    description: str
    source: str
    template: str
    applicability: list[str] = field(default_factory=list)
    strength: str = "medium"
    anti_pattern: str = ""


# ═══════════════════════════════════════════════════════════════════════════
# Distilled Patterns (15 patterns from open-source + in-house design)
# ═══════════════════════════════════════════════════════════════════════════

DISTILLED_PATTERNS: list[PromptPattern] = [
    PromptPattern(
        id="role-expertise-boundary",
        name="Expertise Boundary Declaration",
        category="role",
        description=(
            "明确定义AI的专业领域和能力边界。来源：LangChain Agent的"
            "'You are a helpful assistant with access to tools. "
            "Do not make up information you don't have.'"
        ),
        source="LangChain / LangGraph Agent",
        template=(
            "你是{domain}领域的专家，具备以下能力：\n{capabilities}\n\n"
            "重要限制：\n{limitations}\n\n"
            "遇到超出能力范围的问题时，请诚实告知而非编造。"
        ),
        applicability=["all_modes", "system_prompt"],
        strength="high",
        anti_pattern="不要只说'你是一个有用的助手'——太模糊。",
    ),
    PromptPattern(
        id="role-spectrum-positioning",
        name="Spectrum Self-Positioning",
        category="role",
        description=(
            "让AI在连续光谱上定位自己（而非选离散标签），产生更细腻的行为差异。"
            "来源：本项目构想一。"
        ),
        source="问津 v0.3 构想一",
        template=(
            "你在以下维度上的定位：\n{spectrum_dimensions}\n\n"
            "请根据你在每个维度上的位置调整分析风格和语言表达。"
        ),
        applicability=["all_modes", "personalization"],
        strength="high",
        anti_pattern="光谱维度不超过8个。",
    ),
    PromptPattern(
        id="struct-chain-of-thought",
        name="Chain-of-Thought Scaffolding",
        category="structure",
        description=(
            "嵌入思维链框架，引导模型按步骤推理而非直接给结论。"
            "来源：Wei et al. (2022) Chain-of-Thought Prompting。"
        ),
        source="Chain-of-Thought (Wei et al. 2022)",
        template=(
            "请按以下步骤分析问题：\n"
            "1. **理解问题**：用自己的话重述\n"
            "2. **分解要素**：识别关键变量和关系\n"
            "3. **推理过程**：逐步推演，每一步说明理由\n"
            "4. **得出结论**：基于推理的最终判断\n"
            "5. **不确定性说明**：指出结论的局限性和假设前提"
        ),
        applicability=["academic", "analysis", "topic_argumentation"],
        strength="high",
        anti_pattern="不要让模型跳过推理直接给答案。",
    ),
    PromptPattern(
        id="struct-format-constraint",
        name="Output Format Constraint",
        category="structure",
        description="明确指定输出格式，减少后处理成本。来源：Dify的Structured Output模式。",
        source="Dify / LangFlow",
        template="请严格按以下格式输出：\n\n{format_spec}\n\n不要输出格式之外的任何内容。",
        applicability=["all_modes", "export", "api_response"],
        strength="high",
        anti_pattern="不要同时指定多个互斥的格式。",
    ),
    PromptPattern(
        id="struct-few-shot-calibration",
        name="Few-Shot Example Calibration",
        category="structure",
        description=(
            "嵌入2-3个精心设计的示例，校准输出风格和深度。"
            "关键：示例必须覆盖'好'和'不够好'两种。来源：LangChain FewShotPromptTemplate。"
        ),
        source="LangChain FewShotPromptTemplate",
        template=(
            "以下是{task}的示例：\n\n"
            "✅ **好的回答**：\n{good_example}\n\n"
            "❌ **不够好的回答**（过于{deficiency}）：\n{bad_example}\n\n"
            "请以'好的回答'的标准完成任务。"
        ),
        applicability=["youth", "learning", "export"],
        strength="medium",
        anti_pattern="示例不要超过3个。",
    ),
    PromptPattern(
        id="constraint-negative",
        name="Negative Constraints",
        category="constraint",
        description="明确告诉模型不要做什么。来源：Anthropic Constitutional AI。",
        source="Anthropic Constitutional AI / Claude",
        template=(
            "在回复时，请严格遵守以下规则：\n"
            "✅ 你应该：\n{positive_rules}\n\n"
            "❌ 你不应该：\n{negative_rules}"
        ),
        applicability=["all_modes", "safety"],
        strength="high",
        anti_pattern="负向约束3-5条即可。",
    ),
    PromptPattern(
        id="constraint-progressive-disclosure",
        name="Progressive Disclosure of Context",
        category="constraint",
        description="将长prompt分层：核心指令→背景信息→示例。来源：OpenAI API最佳实践。",
        source="OpenAI API Best Practices",
        template=(
            "# 核心任务（必读）\n{core_instruction}\n\n"
            "# 背景信息\n{background}\n\n"
            "# 参考示例\n{examples}"
        ),
        applicability=["all_modes", "complex_tasks"],
        strength="medium",
        anti_pattern="不要把核心指令埋在背景信息后面。",
    ),
    PromptPattern(
        id="constraint-token-budget",
        name="Token Budget Enforcement",
        category="constraint",
        description="用具体字数/行数替代'简洁'等模糊表述。来源：AutoGPT/LangChain。",
        source="AutoGPT / LangChain",
        template=(
            "输出约束：\n- 最多{max_words}字\n- 最多{max_paragraphs}段\n"
            "- 如果信息不足以完成任务，请用1句话说明缺少什么信息"
        ),
        applicability=["all_modes", "hints", "summarize"],
        strength="medium",
        anti_pattern="不要同时要求'全面'和'简洁'。",
    ),
    PromptPattern(
        id="style-register-switching",
        name="Register Switching by Audience",
        category="style",
        description="根据目标受众切换语言语域（学术/政务/通俗）。来源：问津三种模式提炼。",
        source="问津 mode_prompts.py + Anthropic风格指南",
        template=(
            "你的目标受众是{audience_description}。\n"
            "请使用以下语域：\n"
            "- 词汇层面：{vocabulary_guidance}\n"
            "- 句式层面：{sentence_guidance}\n"
            "- 论证风格：{argumentation_guidance}\n"
            "- 情感基调：{tone_guidance}"
        ),
        applicability=["all_modes", "personalization"],
        strength="high",
        anti_pattern="不要让学术模式的AI使用口语化表达。",
    ),
    PromptPattern(
        id="style-socratic-questioning",
        name="Socratic Questioning for Learning",
        category="style",
        description="用层层追问引导用户自己发现，而非直接给答案。来源：Open Interpreter。",
        source="Open Interpreter / Socratic Method",
        template=(
            "你的目标是引导{user_description}自行发现答案。\n"
            "请遵循苏格拉底方法：\n"
            "1. 先理解用户当前的认识水平\n"
            "2. 提出挑战性问题，暴露认知盲点\n"
            "3. 引导用户重新审视自己的假设\n"
            "4. 在用户卡住时提供提示（而非直接答案）\n"
            "5. 最后帮助用户归纳总结自己的发现"
        ),
        applicability=["youth", "learning"],
        strength="medium",
        anti_pattern="不要对急迫的实务问题使用苏格拉底方法。",
    ),
    PromptPattern(
        id="style-marxist-lens",
        name="Marxist Historical Materialism Lens",
        category="style",
        description="用分析而非口号的方式融入马克思主义社会历史观。来源：问津Youth模式设计。",
        source="问津 Youth Mode + 马克思主义方法论",
        template=(
            "在分析{social_phenomenon}时，请自然地融入以下分析视角：\n"
            "1. **社会存在决定社会意识**：这个现象的物质基础是什么？\n"
            "2. **阶级分析**：不同社会群体在这个现象中处于什么位置？\n"
            "3. **历史唯物主义**：这个现象是哪个历史发展阶段的产物？\n"
            "4. **实践检验**：有什么经验证据支持或挑战这种分析？\n\n"
            "关键：用分析而非口号的方式融入这些视角。"
        ),
        applicability=["youth", "analysis"],
        strength="high",
        anti_pattern="不要使用政治口号式语言。",
    ),
    PromptPattern(
        id="meta-self-critique",
        name="Self-Critique Loop",
        category="meta",
        description="要求模型在输出后对自己的回答进行批判性审查。来源：Self-Refine (Madaan 2023)。",
        source="Self-Refine (Madaan et al. 2023) / Constitutional AI",
        template=(
            "在完成上述任务后，请进行自我审查：\n"
            "1. 你的回答是否有逻辑漏洞？\n"
            "2. 是否有未说明的假设前提？\n"
            "3. 是否有更好的替代解释？\n"
            "4. 如果用户是{user_type}，这个回答是否适合TA的理解水平？\n\n"
            "如有问题，请修正后再输出最终版本。"
        ),
        applicability=["academic", "analysis", "export"],
        strength="medium",
        anti_pattern="不要在简单任务中使用自检。",
    ),
    PromptPattern(
        id="meta-uncertainty-calibration",
        name="Uncertainty Calibration",
        category="meta",
        description="要求模型对每个主张标注确信度。来源：OpenAI Uncertainty Research。",
        source="OpenAI Uncertainty Research / Academic Conventions",
        template=(
            "对于你的每个主要论点，请在括号中标注确信度：\n"
            "- [确信] = 有充分证据支持\n"
            "- [较确信] = 有部分证据，但有讨论空间\n"
            "- [推测] = 可能性较高但缺乏直接证据\n"
            "- [假设] = 仅作为可能性提出\n\n"
            "这有助于读者理解你的分析的可靠性程度。"
        ),
        applicability=["academic", "analysis"],
        strength="medium",
        anti_pattern="不要滥用确信度标注。",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
# Pattern → Mode+Task Mapping
# ═══════════════════════════════════════════════════════════════════════════

PATTERN_MODE_MAPPING = {
    "academic": {
        "system": ["role-expertise-boundary", "constraint-negative", "style-register-switching"],
        "topic": ["struct-chain-of-thought", "meta-uncertainty-calibration"],
        "analysis": ["struct-chain-of-thought", "meta-self-critique", "meta-uncertainty-calibration"],
        "export": ["struct-format-constraint", "struct-chain-of-thought", "meta-self-critique"],
        "hints": ["constraint-token-budget"],
    },
    "government": {
        "system": ["role-expertise-boundary", "constraint-negative", "style-register-switching"],
        "topic": ["struct-chain-of-thought", "constraint-token-budget"],
        "analysis": ["struct-chain-of-thought", "struct-format-constraint"],
        "export": ["struct-format-constraint", "constraint-token-budget"],
        "hints": ["constraint-token-budget"],
    },
    "youth": {
        "system": [
            "role-expertise-boundary", "constraint-negative",
            "style-register-switching", "style-socratic-questioning", "style-marxist-lens",
        ],
        "topic": ["style-socratic-questioning", "struct-chain-of-thought"],
        "analysis": ["struct-chain-of-thought", "style-socratic-questioning"],
        "export": ["struct-format-constraint", "struct-few-shot-calibration"],
        "hints": ["style-socratic-questioning", "constraint-token-budget"],
    },
}


class DistillationCatalog:
    """Query interface for the distilled pattern catalog."""

    def __init__(self, patterns: list[PromptPattern] | None = None):
        self._patterns = patterns or DISTILLED_PATTERNS
        self._by_id: dict[str, PromptPattern] = {p.id: p for p in self._patterns}
        self._by_category: dict[str, list[PromptPattern]] = {}
        for p in self._patterns:
            self._by_category.setdefault(p.category, []).append(p)

    def get(self, pattern_id: str) -> Optional[PromptPattern]:
        return self._by_id.get(pattern_id)

    def by_category(self, category: str) -> list[PromptPattern]:
        return self._by_category.get(category, [])

    def by_mode_task(self, mode: str, task: str) -> list[PromptPattern]:
        ids = PATTERN_MODE_MAPPING.get(mode, {}).get(task, [])
        return [self._by_id[pid] for pid in ids if pid in self._by_id]

    def build_distilled_modifier(self, mode: str, task: str) -> str:
        """Build a prompt modifier from distilled patterns for a mode+task combo."""
        pattern_ids = PATTERN_MODE_MAPPING.get(mode, {}).get(task, [])
        if not pattern_ids:
            return ""

        parts = []
        for pid in pattern_ids:
            p = self._by_id.get(pid)
            if not p:
                continue
            if task == "topic" and p.id == "struct-chain-of-thought":
                parts.append(p.template)
            elif task == "analysis" and p.id == "struct-chain-of-thought":
                parts.append(p.template)
            elif task == "analysis" and p.id == "meta-self-critique":
                parts.append(p.template.format(user_type="学术研究者"))
            elif task == "analysis" and p.id == "meta-uncertainty-calibration":
                parts.append(p.template)
            elif task == "export" and p.id == "struct-format-constraint":
                parts.append(p.template.format(format_spec="{format_spec}"))
            elif task == "hints" and p.id == "constraint-token-budget":
                parts.append(p.template.format(max_words="100", max_paragraphs="1"))
            else:
                parts.append(p.template)
        return "\n\n".join(parts)

    def all_patterns(self) -> list[PromptPattern]:
        return list(self._patterns)

    def to_json(self) -> str:
        return json.dumps(
            [{"id": p.id, "name": p.name, "category": p.category,
              "description": p.description, "source": p.source}
             for p in self._patterns],
            ensure_ascii=False, indent=2,
        )


catalog = DistillationCatalog()


# ═══════════════════════════════════════════════════════════════════════════
# LLM-Assisted Distillation (future use)
# ═══════════════════════════════════════════════════════════════════════════

DISTILLATION_ANALYSIS_PROMPT = """你是一位Prompt Engineering专家。请分析以下system prompt，提取设计模式。

对于每个设计模式，输出：

```json
{
  "patterns": [
    {
      "name": "模式名称（3-6字）",
      "category": "role | structure | constraint | style | meta",
      "description": "这个模式做什么，为什么有效",
      "template": "可复用的模板片段",
      "applicability": ["适用场景"],
      "strength": "high | medium | low"
    }
  ]
}
```

要分析的system prompt:
{prompt_text}"""


async def distill_from_source(
    prompt_text: str,
    source_name: str,
    ai_callable,
) -> list[PromptPattern]:
    """Use an LLM to extract design patterns from an arbitrary system prompt.

    Args:
        prompt_text: The system prompt to analyze
        source_name: Where this prompt came from (for attribution)
        ai_callable: An async function that takes a prompt string and returns text
    """
    analysis_prompt = DISTILLATION_ANALYSIS_PROMPT.format(prompt_text=prompt_text)
    try:
        response = await ai_callable(analysis_prompt)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = json.loads(response)

        patterns = []
        for item in data.get("patterns", []):
            patterns.append(PromptPattern(
                id=f"distilled-{source_name}-{item['name'].lower().replace(' ', '-')}",
                name=item["name"],
                category=item.get("category", "structure"),
                description=item.get("description", ""),
                source=source_name,
                template=item.get("template", ""),
                applicability=item.get("applicability", []),
                strength=item.get("strength", "medium"),
            ))
        logger.info(f"Distilled {len(patterns)} patterns from {source_name}")
        return patterns
    except Exception as e:
        logger.error(f"Distillation failed for {source_name}: {e}")
        return []
