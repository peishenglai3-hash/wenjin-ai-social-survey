"""Mode-specific prompt fragments for the three themes.

学术 (Academic): rigorous scholarship, theory dialogue, paper-ready output
政务 (Government): policy language, actionable recommendations, formal reports
青春 (Youth): guided learning, plain language, Marxist historical materialism
"""

# ── System prompt modifiers (appended to base system prompts) ──────

ACADEMIC_SYSTEM = (
    "你正在为学术研究者提供服务。请严格遵循社会科学学术规范：\n"
    "1. 强调理论对话——将发现与既有社会学理论建立联系\n"
    "2. 注重概念化——使用规范的学术概念，避免口语化表达\n"
    "3. 方法论自觉——明确分析所基于的方法论预设（定量/定性/混合）\n"
    "4. 可引证性——输出的观点应具备可转化为学术论文的潜力\n"
    "5. 严谨边界——对不确定的结论使用适当的学术限定词"
)

GOVERNMENT_SYSTEM = (
    "你正在为基层治理和政务调研工作者提供服务。请遵循政务文书规范：\n"
    "1. 使用规范的公文用语——语体庄重、准确、简洁\n"
    "2. 突出问题导向——聚焦现实治理难题，分析原因，提出可操作的对策建议\n"
    "3. 注重政策衔接——将调研发现与国家政策方针相衔接\n"
    "4. 结构规范——基本情况→主要做法与成效→存在问题→对策建议\n"
    "5. 数据与案例并重——用具体案例和数据支撑论点，增强说服力"
)

YOUTH_SYSTEM = (
    "你正在为青年学生提供学习引导服务。请做到：\n"
    "1. 通俗易懂——使用生活化的语言解释专业概念，每个关键术语附简要解释\n"
    "2. 引导思考——引导使用者自己发现问题、提出问题，而非直接给答案\n"
    "3. 马克思主义社会历史观——在分析社会现象时自然地融入以下视角：\n"
    "   · 社会存在决定社会意识——思想观念受物质生活条件制约\n"
    "   · 阶级分析方法——关注社会结构中的权力关系和利益格局\n"
    "   · 历史唯物主义——将社会现象放在具体历史发展阶段中理解\n"
    "   · 实践是检验真理的唯一标准——强调实地调查和经验研究的重要性\n"
    "4. 鼓励反思——设置反思性问题，帮助形成独立的社会观察能力\n"
    "5. 自然融入——不使用政治口号式语言，展现社会科学的分析魅力"
)

# ── Mode-aware export templates ────────────────────────────────────

EXPORT_MODIFIERS = {
    "academic": (
        "请按照学术论文规范格式组织输出：\n"
        "1. **摘要**（200-300字，概括研究问题、方法、发现、结论）\n"
        "2. **引言**（研究背景与问题提出）\n"
        "3. **文献回顾与理论框架**\n"
        "4. **研究方法**（数据来源、样本、分析方法）\n"
        "5. **研究发现**（分主题报告实证结果）\n"
        "6. **讨论**（与既有研究对话，指出理论贡献）\n"
        "7. **结论**（局限性、政策含义、未来研究方向）\n"
        "8. **参考文献**（建议APA第7版格式）\n"
        "行文风格：严谨、客观、第三人称。使用学术术语但不过度。"
    ),
    "government": (
        "请按照政务调研报告规范格式组织输出：\n"
        "1. **标题**（简洁明了，点明调研对象和主题）\n"
        "2. **基本情况**（调研时间、地点、对象、方法）\n"
        "3. **主要做法与成效**（梳理已有工作基础和取得的成效）\n"
        "4. **存在问题与原因分析**（实事求是地指出问题，深入分析原因）\n"
        "5. **对策建议**（具体、可操作、有针对性的建议）\n"
        "6. **结语**（简要总结，表达对工作推进的期望）\n"
        "行文风格：规范、准确、简洁。使用公文用语，避免空话套话。"
    ),
    "youth": (
        "请按照学习报告的风格组织输出：\n"
        "1. **我为什么要关注这个问题？**（个人动机和社会意义）\n"
        "2. **我看到了什么？**（观察到的社会现象，用具体事例描述）\n"
        "3. **为什么会这样？**（尝试用社会学概念和理论解释）\n"
        "   · 每个理论概念后附【概念解释】小贴士\n"
        "4. **这让我想到了什么？**（与课堂知识、个人经验建立联系）\n"
        "5. **我还有什么困惑？**（提出未解决的问题，引导进一步探索）\n"
        "6. **如果我想深入了解更多……**（推荐阅读材料和下一步行动建议）\n"
        "行文风格：亲切、引导式。用'我们'而非'笔者'。鼓励批判性思考。"
    ),
}

# ── Topic framing by mode ──────────────────────────────────────────

TOPIC_MODIFIERS = {
    "academic": (
        "请从学术研究的角度框定研究选题：\n"
        "- 与既有文献中的哪些理论对话？\n"
        "- 研究填补了什么知识空白？\n"
        "- 可以操作化为哪些可检验的研究假设？"
    ),
    "government": (
        "请从基层治理和政策实践的角度框定研究选题：\n"
        "- 该选题对应哪项政策议题或治理难题？\n"
        "- 研究结论能为决策者提供什么参考？\n"
        "- 调研如何体现实事求是的工作方法？"
    ),
    "youth": (
        "请从青年学生学习的角度框定研究选题：\n"
        "- 这个问题为什么值得年轻人关注？\n"
        "- 研究过程中可以学到什么社会学方法？\n"
        "- 如何用生活中的例子来理解这个研究问题？"
    ),
}

# ── Interview scenario presets by mode ──────────────────────────────

INTERVIEW_SCENARIOS = {
    "academic": [
        {
            "id": "academic_depth",
            "label": "学术深度访谈",
            "description": "面向研究对象的半结构化深度访谈，适合质性研究数据收集",
            "phases": ["建立rapport", "开放式提问", "理论探针追问", "总结确认"],
        },
        {
            "id": "expert_consultation",
            "label": "专家咨询访谈",
            "description": "面向领域专家的结构化咨询，获取专业见解",
            "phases": ["背景介绍", "核心问题咨询", "方法论讨论", "未来展望"],
        },
    ],
    "government": [
        {
            "id": "community_survey",
            "label": "基层调研访谈",
            "description": "面向社区居民/村干部的实地调研，了解政策落实情况",
            "phases": ["寒暄破冰", "基本情况了解", "政策感知询问", "诉求收集", "总结致谢"],
        },
        {
            "id": "cadre_interview",
            "label": "干部座谈访谈",
            "description": "面向基层干部的座谈调研，了解工作中的实际困难",
            "phases": ["情况介绍", "工作成效汇报", "困难与瓶颈", "政策建议", "归纳总结"],
        },
    ],
    "youth": [
        {
            "id": "peer_interview",
            "label": "朋辈访谈",
            "description": "面向同学/朋友的轻松访谈，适合初学者练习访谈技巧",
            "phases": ["破冰聊天", "主题引入", "展开讨论", "深度追问练习", "总结反馈"],
        },
        {
            "id": "observation_practice",
            "label": "参与观察练习",
            "description": "在公共场所进行非参与式观察，练习田野笔记记录",
            "phases": ["选择观察点", "系统观察", "田野笔记", "初步分析", "反思讨论"],
        },
    ],
}


def get_mode_modifier(theme: str, modifier_type: str = "system") -> str:
    """Return the appropriate mode-specific prompt modifier.

    Args:
        theme: 'academic' | 'government' | 'youth'
        modifier_type: 'system' | 'export' | 'topic'
    """
    theme = theme if theme in ("academic", "government", "youth") else "academic"

    if modifier_type == "system":
        return {"academic": ACADEMIC_SYSTEM, "government": GOVERNMENT_SYSTEM, "youth": YOUTH_SYSTEM}[theme]
    elif modifier_type == "export":
        return EXPORT_MODIFIERS[theme]
    elif modifier_type == "topic":
        return TOPIC_MODIFIERS[theme]
    return ""


def get_interview_scenarios(theme: str) -> list[dict]:
    """Return preset interview scenarios for a given mode."""
    return INTERVIEW_SCENARIOS.get(theme, INTERVIEW_SCENARIOS["academic"])


# ═══════════════════════════════════════════════════════════════════════
# Deep Heterogeneity — 深度异质化：每种模式独有工作流、工具链、分析框架
# ═══════════════════════════════════════════════════════════════════════

MODE_WORKFLOWS = {
    "academic": {
        "name": "学术研究流程",
        "stages": [
            {"id": "literature", "label": "文献回顾与理论建构", "icon": "📚",
             "desc": "系统检索文献，识别理论空白，构建概念框架"},
            {"id": "design", "label": "研究设计", "icon": "📐",
             "desc": "操作化概念，选择研究方法，制定抽样策略"},
            {"id": "fieldwork", "label": "田野数据收集", "icon": "🎙",
             "desc": "深度访谈/参与观察/档案研究，系统记录"},
            {"id": "coding", "label": "数据编码与分析", "icon": "🔍",
             "desc": "主题编码/扎根理论/内容分析，理论饱和度检验"},
            {"id": "writing", "label": "学术写作与发表", "icon": "✍️",
             "desc": "遵循学术论文结构，回应审稿人关切"},
        ],
        "recommended_tools": ["文献管理(Zotero)", "质性分析(MAXQDA/NVivo)", "问卷(SurveyCTO)"],
    },
    "government": {
        "name": "政务调研流程",
        "stages": [
            {"id": "briefing", "label": "调研方案制定", "icon": "📋",
             "desc": "明确调研目的、对象、方式、时间安排"},
            {"id": "stakeholder", "label": "利益相关方走访", "icon": "👥",
             "desc": "座谈/走访/问卷调查，覆盖各类利益群体"},
            {"id": "data_collect", "label": "数据与资料收集", "icon": "📊",
             "desc": "统计报表、台账资料、政策文件收集"},
            {"id": "analysis", "label": "问题诊断与对策研提", "icon": "🔎",
             "desc": "归纳问题、分析原因、提出可操作建议"},
            {"id": "report", "label": "调研报告撰写与汇报", "icon": "📄",
             "desc": "按政务文书规范撰写，附数据支撑和案例"},
        ],
        "recommended_tools": ["问卷(问卷星)", "统计(Excel/SPSS)", "可视(DataV)"],
    },
    "youth": {
        "name": "学习探索流程",
        "stages": [
            {"id": "curiosity", "label": "发现感兴趣的问题", "icon": "🔎",
             "desc": "从日常生活/新闻/课堂中发现值得探究的社会现象"},
            {"id": "learn", "label": "知识准备", "icon": "📖",
             "desc": "阅读相关通俗读物和入门文献，建立基本认识"},
            {"id": "observe", "label": "实地观察与记录", "icon": "👀",
             "desc": "带着问题进入现场，系统观察并记录"},
            {"id": "reflect", "label": "反思与讨论", "icon": "💭",
             "desc": "与同伴讨论观察发现，反思自己的预设和偏见"},
            {"id": "present", "label": "成果展示与分享", "icon": "🎤",
             "desc": "用通俗易懂的方式分享发现，撰写学习报告"},
        ],
        "recommended_tools": ["笔记(Notion/语雀)", "思维导图(XMind)", "可视化(Canva)"],
    },
}

MODE_ANALYSIS_FRAMEWORKS = {
    "academic": [
        {"name": "主题编码 (Thematic Coding)", "desc": "从文本中提取、归纳、抽象出主题",
         "steps": ["开放编码", "主轴编码", "选择性编码", "理论饱和度检验"]},
        {"name": "叙事分析 (Narrative Analysis)", "desc": "关注受访者如何讲述自己的故事",
         "steps": ["识别叙事结构", "分析叙事策略", "解读叙事意义", "关联社会语境"]},
        {"name": "话语分析 (Discourse Analysis)", "desc": "分析语言使用背后的权力关系",
         "steps": ["文本选择", "话语实践分析", "社会实践分析", "意识形态批判"]},
    ],
    "government": [
        {"name": "SWOT分析", "desc": "评估政策/项目的优势、劣势、机会、威胁",
         "steps": ["优势识别", "劣势诊断", "机会评估", "威胁分析", "战略匹配"]},
        {"name": "问题树分析 (Problem Tree)", "desc": "从核心问题出发追溯原因和后果",
         "steps": ["确定核心问题", "追溯根本原因", "分析直接后果", "构建对策树"]},
        {"name": "利益相关方矩阵", "desc": "按影响力×关注度分类利益群体",
         "steps": ["识别利益方", "影响力评估", "关注度评估", "制定沟通策略"]},
    ],
    "youth": [
        {"name": "5W1H分析", "desc": "Who/What/When/Where/Why/How 框架",
         "steps": ["六要素逐一回答", "信息关联分析", "发现信息缺口", "补充调研"]},
        {"name": "比较分析", "desc": "通过对比不同案例发现规律",
         "steps": ["选择比较对象", "确定比较维度", "寻找相似与差异", "解释原因"]},
        {"name": "反思日志", "desc": "通过写作促进批判性反思",
         "steps": ["描述所见", "记录感受", "分析原因", "联系理论", "提出新问题"]},
    ],
}

MODE_TASK_CONFIG = {
    "academic": {
        "hints": {"temperature": 0.4, "max_tokens": 1024},
        "summarize": {"temperature": 0.4, "max_tokens": 4096},
        "analysis": {"temperature": 0.5, "max_tokens": 8192},
        "export": {"temperature": 0.4, "max_tokens": 8192},
        "topic": {"temperature": 0.5, "max_tokens": 8192},
    },
    "government": {
        "hints": {"temperature": 0.4, "max_tokens": 1024},
        "summarize": {"temperature": 0.3, "max_tokens": 4096},
        "analysis": {"temperature": 0.4, "max_tokens": 8192},
        "export": {"temperature": 0.3, "max_tokens": 8192},
        "topic": {"temperature": 0.4, "max_tokens": 8192},
    },
    "youth": {
        "hints": {"temperature": 0.7, "max_tokens": 1024},
        "summarize": {"temperature": 0.6, "max_tokens": 4096},
        "analysis": {"temperature": 0.6, "max_tokens": 8192},
        "export": {"temperature": 0.5, "max_tokens": 8192},
        "topic": {"temperature": 0.7, "max_tokens": 8192},
    },
}


def get_mode_workflow(theme: str) -> dict:
    """Return the full workflow configuration for a mode."""
    return MODE_WORKFLOWS.get(theme, MODE_WORKFLOWS["academic"])


def get_mode_analysis_frameworks(theme: str) -> list[dict]:
    """Return the recommended analysis frameworks for a mode."""
    return MODE_ANALYSIS_FRAMEWORKS.get(theme, MODE_ANALYSIS_FRAMEWORKS["academic"])


def get_mode_task_config(theme: str, task: str) -> dict:
    """Return the AI parameters (temperature, max_tokens) for a mode+task combo."""
    defaults = {"temperature": 0.5, "max_tokens": 4096}
    mode_configs = MODE_TASK_CONFIG.get(theme, MODE_TASK_CONFIG["academic"])
    return mode_configs.get(task, defaults)


# ── Spectrum dimension labels for prompt injection ───────────────────

SPECTRUM_LABELS = {
    "theory_driven": ("理论驱动", "经验驱动"),
    "methodological_rigidity": ("严谨规范", "灵活探索"),
    "analysis_depth": ("广度优先", "深度优先"),
    "structure_preference": ("结构化", "开放式"),
    "participation_level": ("旁观观察", "深度参与"),
    "tech_dependency": ("低技术", "高技术"),
    "writing_style": ("学术正式", "通俗亲和"),
    "learning_preference": ("示范引导", "自主探索"),
}

# Per-dimension prompt modifiers — injected at different intensity levels
SPECTRUM_PROMPT_MODIFIERS = {
    "theory_driven": {
        1: "请从理论出发构建分析框架，强调与既有学术文献的对话。",
        2: "请在分析中适当关注理论视角，同时重视经验材料。",
        3: "请平衡理论视角与经验观察。",
        4: "请从经验材料中归纳模式，辅以理论概念加以解释。",
        5: "请以经验观察为出发点，通过归纳提炼实践智慧，减少抽象理论讨论。",
    },
    "methodological_rigidity": {
        1: "请严格遵循规范的研究方法流程，在每个步骤中说明方法论依据。",
        2: "请在有方法论依据的前提下保持一定的灵活性。",
        3: "请在规范与灵活之间保持平衡。",
        4: "请根据研究实际情况灵活调整方法，不必拘泥于标准流程。",
        5: "请以实用为导向，根据田野情况自由调整，强调方法的创造性运用。",
    },
    "analysis_depth": {
        1: "请广泛覆盖多个相关主题和视角，追求分析的全面性。",
        2: "请在覆盖面的基础上，选择1-2个重点方向适当深入。",
        3: "请在广度和深度之间保持平衡。",
        4: "请聚焦少数核心主题进行深入分析，不必面面俱到。",
        5: "请深耕1-2个核心问题，追求分析的深度和透彻程度。",
    },
    "structure_preference": {
        1: "请使用严格的分析框架和标准化模板组织内容。",
        2: "请以结构化方式为主，允许局部灵活调整。",
        3: "请在结构与开放之间保持平衡。",
        4: "请采用半结构化的方式，保留探索空间。",
        5: "请以开放式探索为主，不拘泥于预设框架。",
    },
    "participation_level": {
        1: "请保持客观中立的分析立场，强调研究者与对象的距离。",
        2: "请以观察为主，适度融入参与式理解。",
        3: "请在观察与参与之间保持平衡。",
        4: "请采取参与式的研究视角，关注主体体验和互动过程。",
        5: "请以深度参与者的视角进行分析，强调共情理解和主体间性。",
    },
    "tech_dependency": {
        1: "请优先推荐传统、低门槛的研究工具和方法。",
        2: "请以传统方法为主，适度引入简单数字工具。",
        3: "请平衡传统方法与数字工具的推荐。",
        4: "请积极推荐数字工具和AI辅助方法。",
        5: "请以前沿数字技术和AI工具为主要推荐方向。",
    },
    "writing_style": {
        1: "请使用严谨的学术写作风格，符合核心期刊发表标准。",
        2: "请以学术风格为主，适度降低术语密度以提升可读性。",
        3: "请在学术严谨与通俗易懂之间保持平衡。",
        4: "请使用通俗亲和的语言，但保留分析深度。",
        5: "请使用生活化的语言和叙述性表达，降低阅读门槛。",
    },
    "learning_preference": {
        1: "请提供明确的步骤示范和可复用的模板，引导用户逐步完成。",
        2: "请以示范为主，在每个阶段提供参考示例。",
        3: "请在示范引导与自主探索之间保持平衡。",
        4: "请提供方向性建议和资源，鼓励用户自主探索。",
        5: "请以启发式提问为主，引导用户独立思考和探索。",
    },
}


def build_spectrum_prompt(spectrum_values: dict) -> str:
    """Build a spectral user-profile prompt from 1–5 dimension scores.

    Each dimension contributes a modifier line at its intensity level.
    Only dimensions that deviate from the midpoint (3) are included to
    keep the prompt concise.
    """
    lines = ["\n## 用户方法论光谱\n"]
    has_deviation = False

    for dim_id, (left, right) in SPECTRUM_LABELS.items():
        score = spectrum_values.get(dim_id, 3)
        if not isinstance(score, int) or score < 1 or score > 5:
            score = 3
        if score == 3:
            continue
        has_deviation = True

        bar_left = "█" * max(0, 3 - score)
        bar_right = "█" * max(0, score - 3)
        midpoint = "░"
        bar = f"{bar_left or ' '}{midpoint}{bar_right or ' '}"

        modifier = SPECTRUM_PROMPT_MODIFIERS.get(dim_id, {}).get(score, "")
        lines.append(f"- {left} {bar} {right} ({score}/5)")
        if modifier:
            lines.append(f"  → {modifier}")

    if not has_deviation:
        return ""

    return "\n".join(lines)


def build_deep_heterogeneity_prompt(theme: str, stage: str = "", task: str = "") -> str:
    """Build a comprehensive mode-specific prompt with deep heterogeneity.

    Integrates reference membrane, workflow context, analysis frameworks,
    and mode-appropriate AI parameter settings.
    """
    workflow = get_mode_workflow(theme)
    frameworks = get_mode_analysis_frameworks(theme)

    parts = [f"## {workflow['name']}\n"]

    if stage:
        stage_info = next((s for s in workflow["stages"] if s["id"] == stage), None)
        if stage_info:
            parts.append(f"当前阶段：{stage_info['icon']} {stage_info['label']}")
            parts.append(f"阶段说明：{stage_info['desc']}\n")
    else:
        parts.append("可用阶段：")
        for s in workflow["stages"]:
            parts.append(f"  {s['icon']} {s['label']} — {s['desc']}")
        parts.append("")

    parts.append(f"推荐工具：{' · '.join(workflow['recommended_tools'])}\n")
    parts.append("## 可用分析框架")
    for fw in frameworks:
        parts.append(f"\n### {fw['name']}")
        parts.append(f"{fw['desc']}")
        parts.append("步骤：" + " → ".join(fw["steps"]))

    if task == "hints":
        hints_map = {
            "academic": "提示应聚焦：理论对话方向、方法论注意事项、概念化建议",
            "government": "提示应聚焦：政策衔接点、可操作性评估、基层实际考量",
            "youth": "提示应聚焦：学习引导、概念解释、反思问题",
        }
        parts.append(f"\n{hints_map.get(theme, hints_map['academic'])}")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════
# Prompt Distillation Integration (构想一成果转化)
# ═══════════════════════════════════════════════════════════════════════

def get_distilled_modifier(theme: str, task: str = "system") -> str:
    """Return prompt modifier built from distilled design patterns.

    Layers distilled patterns (from open-source prompt engineering research)
    on top of the base mode-specific prompts. This is the production
    integration point for 构想一 (Prompt Distillation).

    Args:
        theme: 'academic' | 'government' | 'youth'
        task: 'system' | 'topic' | 'analysis' | 'export' | 'hints'
    """
    try:
        from app.services.prompt_distiller import catalog
        return catalog.build_distilled_modifier(theme, task)
    except ImportError:
        return ""


def build_enhanced_system_prompt(theme: str, spectrum_values: dict | None = None) -> str:
    """Build a complete, distillation-enhanced system prompt for a mode.

    Layers:
    1. Base mode modifier (mode_prompts.py)
    2. Distilled design patterns (prompt_distiller.py)
    3. Spectrum personalization (if spectrum_values provided)
    """
    parts = []

    # Layer 1: Base mode system modifier
    base = get_mode_modifier(theme, "system")
    parts.append(base)

    # Layer 2: Distilled patterns
    distilled = get_distilled_modifier(theme, "system")
    if distilled:
        parts.append("\n## 交互设计原则\n" + distilled)

    # Layer 3: Spectrum personalization
    if spectrum_values:
        spectrum = build_spectrum_prompt(spectrum_values)
        if spectrum:
            parts.append(spectrum)

    return "\n\n".join(parts)


def get_distilled_task_prompt(theme: str, task: str, base_prompt: str = "") -> str:
    """Enhance a task-specific prompt with distilled design patterns.

    Args:
        theme: 'academic' | 'government' | 'youth'
        task: 'topic' | 'analysis' | 'export' | 'hints'
        base_prompt: The existing task prompt to enhance
    """
    distilled = get_distilled_modifier(theme, task)
    if not distilled:
        return base_prompt

    return base_prompt + "\n\n## 输出要求\n" + distilled


def list_distilled_patterns() -> list[dict]:
    """Return all distilled patterns for inspection/auditing."""
    try:
        from app.services.prompt_distiller import catalog
        return [
            {"id": p.id, "name": p.name, "category": p.category,
             "source": p.source, "strength": p.strength}
            for p in catalog.all_patterns()
        ]
    except ImportError:
        return []
