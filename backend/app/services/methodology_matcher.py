"""
P1 — Methodology Matching Engine.

Maps research question characteristics to recommended methodology
combinations: theory → method → sampling → instrument trinity.

The "methodology trinity" is a key competitive differentiator:
no competitor product does this end-to-end for Chinese social science.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MethodologyMatch:
    """Complete methodology recommendation for a research question."""
    research_purpose: str = "explore"         # explore / describe / explain / evaluate
    time_dimension: str = "cross_sectional"   # cross_sectional / longitudinal / retrospective
    analysis_unit: str = "individual"         # individual / group / organization / community / text
    data_type: str = "text"                   # text / numeric / mixed / visual

    primary_methods: list[str] = field(default_factory=list)
    secondary_methods: list[str] = field(default_factory=list)

    sampling_strategy: str = "purposive"
    sample_size_min: int = 15
    sample_size_max: int = 30
    sample_size_rationale: str = ""

    data_collection_tools: list[str] = field(default_factory=list)
    analysis_approach: str = ""
    software_recommendations: list[str] = field(default_factory=list)

    validity_strategies: list[str] = field(default_factory=list)
    ethical_considerations: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "research_purpose": self.research_purpose,
            "time_dimension": self.time_dimension,
            "analysis_unit": self.analysis_unit,
            "data_type": self.data_type,
            "primary_methods": self.primary_methods,
            "secondary_methods": self.secondary_methods,
            "sampling_strategy": self.sampling_strategy,
            "sample_size": {"min": self.sample_size_min, "max": self.sample_size_max},
            "sample_size_rationale": self.sample_size_rationale,
            "data_collection_tools": self.data_collection_tools,
            "analysis_approach": self.analysis_approach,
            "software_recommendations": self.software_recommendations,
            "validity_strategies": self.validity_strategies,
            "ethical_considerations": self.ethical_considerations,
            "caveats": self.caveats,
        }


# ── Methodology matching matrix ──
# Key: (purpose, data_type, theory_need) → recommendation bundle

METHODOLOGY_MATRIX = {
    # ── Qualitative / exploratory ──
    ("explore", "text", "theory_building"): {
        "primary": ["深度访谈", "参与观察", "焦点小组"],
        "secondary": ["文献分析", "扎根理论编码", "叙事分析"],
        "sampling": "目的性抽样 / 理论抽样",
        "sample_size": (15, 30),
        "rationale": "质性研究追求信息饱和而非统计代表性，15-30人通常可达到主题饱和",
        "tools": ["半结构访谈提纲", "NVivo / MAXQDA", "田野笔记模板"],
        "analysis": "扎根理论三级编码 → 主题分析 → 理论建构",
        "software": ["NVivo", "MAXQDA", "Atlas.ti", "Dedoose"],
        "validity": ["三角验证（方法/数据/研究者）", "成员检查", "长期沉浸", "反例分析"],
        "ethics": ["知情同意（录音/笔记）", "匿名化处理", "退出权说明", "关系不对等反思"],
        "caveats": ["初学者容易过早终止编码", "注意田野进入的守门人问题", "警惕'田野亲密'导致的分析盲区"],
    },

    ("explore", "text", "theory_extension"): {
        "primary": ["半结构访谈", "焦点小组", "文本分析"],
        "secondary": ["案例研究", "比较分析", "过程追踪"],
        "sampling": "分层目的性抽样",
        "sample_size": (20, 40),
        "rationale": "理论扩展需要更大的变异范围，分层抽样确保不同视角的覆盖",
        "tools": ["半结构访谈提纲", "文档分析矩阵", "NVivo / MAXQDA"],
        "analysis": "主题分析 + 模式匹配 → 理论扩展命题",
        "software": ["NVivo", "MAXQDA", "Dedoose"],
        "validity": ["三角验证", "同行审视", "反例搜索", "可追溯审计"],
        "ethics": ["知情同意", "匿名化", "二次使用说明"],
        "caveats": ["确保案例间可比性", "避免确认偏误选择支持性案例"],
    },

    # ── Quantitative / explanatory ──
    ("explain", "numeric", "theory_testing"): {
        "primary": ["问卷调查", "实验设计", "二手数据分析"],
        "secondary": ["量表开发", "结构方程模型", "多层次回归"],
        "sampling": "概率抽样 / 分层随机抽样",
        "sample_size": (200, 1000),
        "rationale": "量化研究需足够统计效力，G*Power计算建议≥200（中等效应量）",
        "tools": ["结构化问卷（Likert量表）", "SPSS / R / Stata", "Qualtrics / 问卷星"],
        "analysis": "描述统计 → 信效度检验 → 回归/SEM → 稳健性检验",
        "software": ["SPSS", "R", "Stata", "Mplus", "AMOS"],
        "validity": [
            "内容效度（专家评审）", "构念效度（CFA）",
            "内部一致性（Cronbach α）", "共同方法偏差检验",
        ],
        "ethics": ["匿名化问卷", "数据安全存储", "IRB审批", "被试费说明"],
        "caveats": [
            "共同方法偏差是最常见问题",
            "注意问卷长度（≤15分钟为宜）",
            "预测试至少30份",
        ],
    },

    ("explain", "numeric", "theory_extension"): {
        "primary": ["问卷调查", "纵贯追踪", "准实验设计"],
        "secondary": ["多层线性模型", "面板数据分析", "倾向值匹配"],
        "sampling": "分层随机抽样 / 配额抽样",
        "sample_size": (300, 1500),
        "rationale": "纵贯研究需考虑流失率（预估20-30%），初始样本量需相应放大",
        "tools": ["结构化问卷", "追踪管理工具", "R / Stata"],
        "analysis": "描述统计 → 差异检验 → 层级回归/HLM → 稳健性检验",
        "software": ["R", "Stata", "Mplus", "SPSS"],
        "validity": [
            "多重共线性检验", "Harman单因子检验", "追踪样本代表性检验",
        ],
        "ethics": ["追踪研究中的退出权", "数据链接的隐私风险"],
        "caveats": ["样本流失是最主要威胁", "测量等值性问题（跨时间点比较）"],
    },

    # ── Mixed methods ──
    ("explore", "mixed", "theory_building"): {
        "primary": ["顺序探索设计（质性→量化）", "深度访谈 → 问卷开发"],
        "secondary": ["焦点小组", "预测试", "探索性因子分析"],
        "sampling": "两阶段：目的性抽样（阶段1）+ 概率抽样（阶段2）",
        "sample_size": (15, 30),
        "rationale": "阶段1达到信息饱和（15-30人），阶段2根据EFA需求（100-200+）",
        "tools": ["半结构访谈提纲", "问卷初稿", "认知访谈协议"],
        "analysis": "质性编码 → 主题提取 → 量表开发 → EFA验证",
        "software": ["NVivo + SPSS", "MAXQDA + R"],
        "validity": [
            "顺序设计的整合效度", "量表的内容效度（质性支撑）", "构念效度（EFA/CFA）",
        ],
        "ethics": ["两阶段研究的双重知情同意"],
        "caveats": [
            "阶段衔接是最大困难点",
            "时间成本高（至少增加1个月）",
            "确保质性发现真正驱动量化工具设计",
        ],
    },

    ("describe", "mixed", "theory_extension"): {
        "primary": ["并行三角验证设计", "问卷调查 + 深度访谈"],
        "secondary": ["焦点小组", "档案分析"],
        "sampling": "并行设计：概率抽样（量化）+ 目的性抽样（质性）",
        "sample_size": (200, 600),
        "rationale": "量化部分需统计效力（≥200），质性辅样本20-30人做深度补充",
        "tools": ["结构化问卷", "半结构访谈提纲", "SPSS + NVivo"],
        "analysis": "并行分析 → 联合展示（joint display）→ 三角验证",
        "software": ["SPSS + NVivo", "R + MAXQDA"],
        "validity": ["并行研究的三角验证", "方法间一致性检验", "互补性分析"],
        "ethics": ["不同数据源的隐私处理差异"],
        "caveats": ["两种数据矛盾时需诚实报告", "注意时间同步问题"],
    },

    # ── Case study / deep ──
    ("describe", "text", "theory_building"): {
        "primary": ["案例研究", "深度访谈", "档案分析"],
        "secondary": ["参与观察", "焦点小组", "过程追踪"],
        "sampling": "理论抽样 / 典型案例抽样",
        "sample_size": (1, 6),
        "rationale": "案例研究追求分析性概括而非统计概括，1-6个案例足以进行跨案例比较",
        "tools": ["案例研究协议", "半结构访谈提纲", "档案清单", "NVivo"],
        "analysis": "个案内分析 → 跨案例比较 → 模式匹配 → 理论命题",
        "software": ["NVivo", "MAXQDA"],
        "validity": [
            "建构效度（多重证据源）", "内在效度（模式匹配）",
            "外在效度（分析性概括）",
        ],
        "ethics": ["案例匿名化的特殊挑战", "组织层面的知情同意"],
        "caveats": ["案例选择是关键——避免方便抽样", "注意个案的特异性vs可推广性平衡"],
    },

    # ── Content / discourse analysis ──
    ("describe", "text", "theory_extension"): {
        "primary": ["内容分析", "话语分析", "框架分析"],
        "secondary": ["主题分析", "计算文本分析"],
        "sampling": "分层随机抽样（文本库）/ 建构周抽样（媒体内容）",
        "sample_size": (200, 1000),
        "rationale": "文本分析样本量取决于分析层次：人工编码200-500篇，计算文本分析可达数千篇",
        "tools": ["编码手册", "NVivo / Dedoose", "Python（jieba, gensim）"],
        "analysis": "编码表开发 → 信度检验（Krippendorff α≥0.80）→ 频率分析 → 模式识别",
        "software": ["NVivo", "Dedoose", "Python/R（计算文本分析）"],
        "validity": ["编码者间信度", "编码手册的稳定性检验", "反例搜索"],
        "ethics": ["公开文本的引用规范", "社交媒体数据的隐私边界"],
        "caveats": ["编码手册的完备性决定研究质量", "注意媒介文本的选择性偏差"],
    },
}


class MethodologyMatcher:
    """Match research questions to methodology recommendations.

    Uses keyword-based classification to identify research purpose,
    data type, and theory need, then looks up the methodology matrix.
    """

    PURPOSE_PATTERNS = {
        "explore": [
            "探索", "了解", "发现", "揭示", "理解", "是什么", "如何", "怎样",
            "explore", "understand", "discover", "how", "what",
        ],
        "describe": [
            "描述", "呈现", "描绘", "梳理", "现状", "特征", "特点", "分布",
            "describe", "depict", "characterize", "profile",
        ],
        "explain": [
            "解释", "影响", "因果", "机制", "因素", "决定", "为什么", "原因",
            "explain", "cause", "mechanism", "factor", "determine", "why",
            "效应", "作用", "关系", "相关",
        ],
        "evaluate": [
            "评估", "评价", "效果", "绩效", "影响评估", "政策评估",
            "evaluate", "assess", "effect", "impact", "outcome",
        ],
    }

    DATA_TYPE_PATTERNS = {
        "text": [
            "访谈", "观察", "文本", "话语", "叙事", "民族志", "田野",
            "interview", "observation", "text", "discourse", "narrative",
            "质性", "qualitative", "案例", "case",
        ],
        "numeric": [
            "问卷", "调查", "数据", "统计", "回归", "定量", "量化",
            "survey", "data", "statistics", "regression", "quantitative",
            "量表", "指标", "变量", "假设检验",
        ],
        "mixed": [
            "混合", "综合", "多元", "结合", "整合",
            "mixed method", "triangulation", "multi-method",
        ],
    }

    THEORY_PATTERNS = {
        "theory_building": [
            "建构", "生成", "提出", "发展理论", "构建理论", "理论建构",
            "build", "generate", "develop", "construct",
            "扎根", "探索性", "grounded",
        ],
        "theory_testing": [
            "检验", "验证", "测试", "实证", "假设",
            "test", "verify", "validate", "hypothesis",
            "推论", "演绎", "deductive",
        ],
        "theory_extension": [
            "扩展", "修正", "补充", "完善", "拓展",
            "extend", "modify", "refine", "adapt",
        ],
    }

    UNIT_PATTERNS = {
        "individual": ["个人", "个体", "居民", "村民", "学生", "individual"],
        "group": ["群体", "团体", "团队", "家庭", "group", "team", "household"],
        "organization": ["组织", "机构", "单位", "企业", "学校", "医院", "organization"],
        "community": ["社区", "村庄", "邻里", "街道", "community", "village"],
        "text": ["文本", "话语", "政策文件", "媒体报道", "档案", "document"],
    }

    TIME_PATTERNS = {
        "cross_sectional": ["横截面", "现状", "当前", "cross-sectional"],
        "longitudinal": ["纵贯", "追踪", "变化", "过程", "演变", "longitudinal", "panel"],
        "retrospective": ["回溯", "历史", "回顾", "retrospective", "historical"],
    }

    def match(
        self,
        research_question: str,
        paradigm_preference: str = "qualitative",
        field_conditions: dict | None = None,
    ) -> MethodologyMatch:
        """Match a research question to methodology recommendations."""
        q_lower = research_question.lower()

        purpose = self._classify(q_lower, self.PURPOSE_PATTERNS, "explore")

        if paradigm_preference == "qualitative":
            data_type = self._classify(q_lower, self.DATA_TYPE_PATTERNS, "text")
        elif paradigm_preference == "quantitative":
            data_type = self._classify(q_lower, self.DATA_TYPE_PATTERNS, "numeric")
        else:
            data_type = self._classify(q_lower, self.DATA_TYPE_PATTERNS, "mixed")

        theory_need = self._classify(q_lower, self.THEORY_PATTERNS, "theory_building")
        analysis_unit = self._classify(q_lower, self.UNIT_PATTERNS, "individual")
        time_dim = self._classify(q_lower, self.TIME_PATTERNS, "cross_sectional")

        key = (purpose, data_type, theory_need)
        rec = METHODOLOGY_MATRIX.get(key)

        if rec is None:
            for fallback_theory in ["theory_building", "theory_extension", "theory_testing"]:
                fb_key = (purpose, data_type, fallback_theory)
                if fb_key in METHODOLOGY_MATRIX:
                    rec = METHODOLOGY_MATRIX[fb_key]
                    break

        if rec is None:
            rec = METHODOLOGY_MATRIX[("explore", "text", "theory_building")]

        match = MethodologyMatch(
            research_purpose=purpose,
            time_dimension=time_dim,
            analysis_unit=analysis_unit,
            data_type=data_type,
            primary_methods=rec["primary"],
            secondary_methods=rec["secondary"],
            sampling_strategy=rec["sampling"],
            sample_size_min=rec["sample_size"][0],
            sample_size_max=rec["sample_size"][1],
            sample_size_rationale=rec["rationale"],
            data_collection_tools=rec["tools"],
            analysis_approach=rec["analysis"],
            software_recommendations=rec["software"],
            validity_strategies=rec["validity"],
            ethical_considerations=rec["ethics"],
            caveats=rec["caveats"],
        )

        if paradigm_preference == "mixed" and data_type != "mixed":
            match.primary_methods.append(
                "补充访谈" if data_type == "numeric" else "补充问卷"
            )
            match.secondary_methods.append("方法间三角验证")

        if field_conditions:
            if field_conditions.get("access_difficulty") == "high":
                match.caveats.append("田野进入难度高——建议先找守门人，准备替代方案")
                match.ethical_considerations.append("高风险进入场景：确保安全预案")
            if field_conditions.get("time_constraint") == "tight":
                match.caveats.append("时间紧张——考虑缩小范围或使用二手数据")
            if field_conditions.get("budget_constraint") == "tight":
                match.caveats.append("预算有限——优先开源免费方案")
                match.software_recommendations = [
                    s for s in match.software_recommendations
                    if s in ("R", "Python", "Python/R（计算文本分析）")
                ] or ["R（免费开源）", "jamovi（免费SPSS替代）"]

        logger.info(
            "Methodology match: purpose=%s data=%s theory=%s → %s",
            purpose, data_type, theory_need,
            ", ".join(match.primary_methods[:3]),
        )

        from app.services.confidence_service import for_methodology_match
        match.confidence_marker = for_methodology_match(purpose, data_type)
        return match

    def _classify(
        self, text: str, patterns: dict[str, list[str]], default: str = "",
    ) -> str:
        """Keyword-based classification — highest match count wins."""
        scores = {
            category: sum(1 for kw in keywords if kw.lower() in text)
            for category, keywords in patterns.items()
        }
        if not scores:
            return default
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else default

    def list_available_tags(self) -> list[dict]:
        """Return all methodology tags for UI filter display."""
        label_map = {
            "qualitative_interview": "深度访谈",
            "ethnography": "民族志/田野调查",
            "case_study": "案例研究",
            "survey_quantitative": "问卷调查/量化",
            "grounded_theory": "扎根理论",
            "mixed_methods": "混合方法",
            "content_analysis": "内容/话语分析",
            "experimental": "实验研究",
        }
        return [
            {"tag": k, "label": label_map.get(k, k)}
            for k in [
                "qualitative_interview", "ethnography", "case_study",
                "grounded_theory", "content_analysis", "survey_quantitative",
                "experimental", "mixed_methods",
            ]
        ]


# Singleton
_methodology_matcher: MethodologyMatcher | None = None


def get_methodology_matcher() -> MethodologyMatcher:
    global _methodology_matcher
    if _methodology_matcher is None:
        _methodology_matcher = MethodologyMatcher()
    return _methodology_matcher
