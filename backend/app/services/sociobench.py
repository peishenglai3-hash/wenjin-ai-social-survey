"""SocioBench / ISSP Knowledge Base Service.

Provides domain knowledge from the ISSP (International Social Survey Programme)
for: topic-to-scale mapping, benchmark references, and analysis enrichment.

Data source: SocioBench (EMNLP 2025) — JiaWANG-TJ/SocioBench
"""

import logging

logger = logging.getLogger(__name__)

# ── ISSP Domain Definitions ─────────────────────────────────────────────

ISSP_DOMAINS = {
    "citizenship": {
        "name_zh": "公民权利与政治参与",
        "year": 2014,
        "key_topics": [
            "政治参与", "选举行为", "公民权利意识", "政治效能感",
            "社会运动参与", "政治信任", "民主价值观",
        ],
        "sample_countries": 34,
        "core_scales": [
            {"name": "政治效能感量表", "items": 6, "alpha": 0.82, "source": "ISSP Citizenship 2014"},
            {"name": "政治信任量表", "items": 5, "alpha": 0.85, "source": "ISSP Role of Government"},
        ],
    },
    "environment": {
        "name_zh": "环境态度与行为",
        "year": 2020,
        "key_topics": [
            "环境关心", "气候变化认知", "亲环境行为", "环境风险感知",
            "可持续发展态度", "绿色消费", "能源政策态度",
        ],
        "sample_countries": 32,
        "core_scales": [
            {"name": "新生态范式量表 (NEP)", "items": 15, "alpha": 0.84, "source": "Dunlap 2000; ISSP 2020"},
            {"name": "环境行为意向", "items": 10, "alpha": 0.82, "source": "ISSP Environment 2020"},
        ],
    },
    "family": {
        "name_zh": "家庭与性别角色",
        "year": 2012,
        "key_topics": [
            "性别角色态度", "婚姻观念", "工作-家庭平衡", "育儿观念",
            "代际关系", "家务分工", "离婚态度",
        ],
        "sample_countries": 38,
        "core_scales": [
            {"name": "性别角色态度量表", "items": 10, "alpha": 0.85, "source": "ISSP Family 2012"},
            {"name": "工作家庭冲突量表", "items": 8, "alpha": 0.88, "source": "Carlson 2000"},
        ],
    },
    "health": {
        "name_zh": "健康与医疗",
        "year": 2011,
        "key_topics": [
            "自评健康", "心理健康", "医疗利用", "健康不平等",
            "生活方式", "社会支持", "医疗服务满意度",
        ],
        "sample_countries": 32,
        "core_scales": [
            {"name": "主观幸福感量表 (SWLS)", "items": 5, "alpha": 0.84, "source": "Diener 1985"},
            {"name": "心理困扰量表 (K6)", "items": 6, "alpha": 0.87, "source": "Kessler 2002"},
        ],
    },
    "nationalidentity": {
        "name_zh": "国家认同",
        "year": 2013,
        "key_topics": [
            "国家认同", "民族自豪感", "移民态度", "全球化认知",
            "文化认同", "公民身份", "爱国主义",
        ],
        "sample_countries": 33,
        "core_scales": [
            {"name": "国家认同量表", "items": 8, "alpha": 0.83, "source": "ISSP National Identity 2013"},
        ],
    },
    "religion": {
        "name_zh": "宗教与价值观",
        "year": 2018,
        "key_topics": [
            "宗教虔诚度", "宗教信仰", "世俗化", "宗教多样性",
            "道德价值观", "灵性追求",
        ],
        "sample_countries": 35,
        "core_scales": [
            {"name": "宗教虔诚度量表", "items": 6, "alpha": 0.88, "source": "ISSP Religion 2018"},
        ],
    },
    "roleofgovernment": {
        "name_zh": "政府角色与福利态度",
        "year": 2016,
        "key_topics": [
            "政府责任", "福利国家态度", "税收态度", "公共支出偏好",
            "再分配政策", "政府干预", "公共服务",
        ],
        "sample_countries": 34,
        "core_scales": [
            {"name": "政府责任认知量表", "items": 8, "alpha": 0.81, "source": "ISSP Role of Government 2016"},
        ],
    },
    "socialinequality": {
        "name_zh": "社会不平等",
        "year": 2019,
        "key_topics": [
            "收入不平等", "社会分层", "机会公平", "阶层认同",
            "分配正义", "社会流动", "贫富差距",
        ],
        "sample_countries": 35,
        "core_scales": [
            {"name": "公平世界信念量表", "items": 7, "alpha": 0.83, "source": "Dalbert 1999; ISSP 2019"},
            {"name": "阶层认同量表", "items": 4, "alpha": 0.75, "source": "ISSP Inequality; CGSS"},
            {"name": "分配公平感量表", "items": 8, "alpha": 0.82, "source": "ISSP Inequality IV"},
        ],
    },
    "socialnetworks": {
        "name_zh": "社交网络与社会资本",
        "year": 2017,
        "key_topics": [
            "社会资本", "社交网络", "社会信任", "社会参与",
            "孤独感", "网络规模", "社会支持",
        ],
        "sample_countries": 30,
        "core_scales": [
            {"name": "社会资本量表", "items": 10, "alpha": 0.80, "source": "ISSP Social Networks 2017"},
            {"name": "社会信任量表", "items": 4, "alpha": 0.75, "source": "ISSP; WVS"},
        ],
    },
    "workorientations": {
        "name_zh": "工作导向",
        "year": 2015,
        "key_topics": [
            "工作价值观", "工作满意度", "工作意义", "职业倦怠",
            "工作-生活平衡", "就业安全感", "职业期望",
        ],
        "sample_countries": 33,
        "core_scales": [
            {"name": "工作价值观量表", "items": 12, "alpha": 0.82, "source": "ISSP Work Orientation 2015"},
            {"name": "工作满意度量表", "items": 5, "alpha": 0.83, "source": "ISSP; CGSS"},
        ],
    },
}

# ── Topic-to-Domain Keyword Mapping ────────────────────────────────────

DOMAIN_KEYWORDS = {
    "socialinequality": [
        "不平等", "贫富", "收入差距", "阶层", "公平", "分配",
        "社会流动", "基尼", "两极分化", "贫困", "阶级",
        "inequality", "stratification", "class", "mobility",
    ],
    "health": [
        "健康", "医疗", "心理", "抑郁", "焦虑", "幸福感", "生活满意度",
        "疾病", "就医", "医保", "自评健康", "压力",
        "health", "wellbeing", "depression", "anxiety",
    ],
    "environment": [
        "环境", "气候", "生态", "绿色", "可持续", "污染", "碳",
        "环保", "自然", "资源", "能耗",
        "environment", "climate", "green", "sustainability",
    ],
    "family": [
        "家庭", "婚姻", "性别", "女性", "男性", "育儿", "代际",
        "家务", "离婚", "生育", "性别角色",
        "family", "marriage", "gender", "childcare",
    ],
    "workorientations": [
        "工作", "职业", "就业", "失业", "加班", "收入", "职场",
        "倦怠", "满意度", "劳动", "薪资",
        "work", "job", "career", "employment", "burnout",
    ],
    "citizenship": [
        "政治", "选举", "投票", "民主", "公民", "参与", "权利",
        "政府信任", "政治效能", "社会运动",
        "political", "democracy", "civic", "voting",
    ],
    "nationalidentity": [
        "国家", "民族", "爱国", "移民", "全球化", "文化认同",
        "国民", "自豪感", "外国人",
        "national", "identity", "immigration", "patriotism",
    ],
    "religion": [
        "宗教", "信仰", "教会", "寺庙", "虔诚", "无神论",
        "religion", "religious", "church", "faith",
    ],
    "roleofgovernment": [
        "政府", "国家干预", "福利", "税收", "公共服务", "再分配",
        "国有企业", "监管", "政策",
        "government", "welfare", "tax", "public service",
    ],
    "socialnetworks": [
        "社交", "网络", "朋友", "信任", "社会资本", "孤独",
        "人际关系", "邻里", "社区",
        "social network", "trust", "loneliness", "social capital",
    ],
}


class SocioBenchKB:
    """SocioBench knowledge base — maps research topics to ISSP domains,
    retrieves validated scales, and provides benchmarking references."""

    def __init__(self):
        self.domains = ISSP_DOMAINS
        self.keywords = DOMAIN_KEYWORDS

    def match_domains(self, research_topic: str, top_k: int = 3) -> list[dict]:
        """Map a research topic to the most relevant ISSP domains."""
        topic_lower = research_topic.lower()
        scores = {}

        for domain_key, keywords in self.keywords.items():
            score = 0
            for kw in keywords:
                if kw.lower() in topic_lower:
                    score += len(kw) * (2 if len(kw) >= 3 else 1)
            if score > 0:
                scores[domain_key] = score

        if scores:
            max_score = max(scores.values())
            scores = {k: round(v / max_score, 2) for k, v in scores.items()}

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        return [
            {
                "domain_key": key,
                "name_zh": self.domains[key]["name_zh"],
                "match_score": score,
                "core_scales": self.domains[key]["core_scales"],
                "key_topics": self.domains[key]["key_topics"][:5],
                "sample_countries": self.domains[key]["sample_countries"],
            }
            for key, score in ranked
        ]

    def get_domain_scales(self, domain_key: str) -> list[dict]:
        """Get validated scales for a specific ISSP domain."""
        domain = self.domains.get(domain_key)
        if not domain:
            return []
        return domain["core_scales"]

    def get_all_domains_summary(self) -> list[dict]:
        """Get a summary of all available ISSP domains."""
        return [
            {
                "key": key,
                "name_zh": info["name_zh"],
                "year": info["year"],
                "countries": info["sample_countries"],
                "n_topics": len(info["key_topics"]),
                "n_scales": len(info["core_scales"]),
            }
            for key, info in self.domains.items()
        ]

    def build_analysis_context(self, research_topic: str) -> str:
        """Build a rich context string for AI analysis prompts."""
        domains = self.match_domains(research_topic, top_k=3)

        if not domains:
            return ""

        lines = ["\n## SocioBench / ISSP 领域匹配\n"]
        lines.append("以下ISSP国际调查领域与当前研究主题相关：\n")

        for i, d in enumerate(domains):
            lines.append(f"### {i+1}. {d['name_zh']}")
            lines.append(f"- 匹配度: {d['match_score']:.0%} · 覆盖{d['sample_countries']}国")
            lines.append(f"- 相关主题: {' · '.join(d['key_topics'])}")
            lines.append("- 推荐量表:")
            for s in d["core_scales"]:
                lines.append(f"  * {s['name']} ({s['items']}题, α={s['alpha']})")
            lines.append("")

        lines.append("请在分析中引用相关ISSP领域作为理论参照。")
        return "\n".join(lines)


sociobench_kb = SocioBenchKB()
