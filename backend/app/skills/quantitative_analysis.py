from app.skills.base import BaseSkill, SkillResult


class QuantitativeAnalysisSkill(BaseSkill):
    name = "quantitative_analysis"
    description = "定量数据分析：描述统计、假设检验、回归分析、可视化建议、结果解读"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        ctx_str = str(context) if context else ""
        return (
            "你是一位社会科学定量分析专家，精通调查数据的统计分析方法。\n"
            "你的任务是根据用户提供的调查数据（文本描述或结构化数据），进行系统的定量分析。\n\n"
            "输出要求（用 Markdown 格式）：\n\n"
            "## 一、数据概览\n"
            "- 样本量、变量数量、变量类型识别\n"
            "- 数据质量初步评估（缺失值、异常值提示）\n\n"
            "## 二、描述性统计\n"
            "- 关键变量的均值、标准差、中位数、频数分布\n"
            "- 建议使用的可视化类型（柱状图/箱线图/直方图/饼图）\n\n"
            "## 三、推断性统计\n"
            "- 适合的假设检验方法（t检验/卡方检验/ANOVA/相关分析）\n"
            "- 检验结果解读（效应量、置信区间、p值含义的通俗解释）\n\n"
            "## 四、回归分析（如适用）\n"
            "- 推荐回归模型类型（OLS/Logistic/Ordered Logit）\n"
            "- 模型设定建议（自变量、因变量、控制变量）\n"
            "- 结果解读框架（系数含义、模型拟合度）\n\n"
            "## 五、量表分析（如适用）\n"
            "- Cronbach's alpha 信度评估\n"
            "- 探索性因子分析建议\n"
            "- 维度得分计算方式\n\n"
            "## 六、结果报告建议\n"
            "- 表格格式建议（三线表、APA格式）\n"
            "- 关键结果的中文表述建议\n"
            "- 分析局限的诚实说明\n\n"
            f"额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "data_description": {"type": "string", "description": "数据描述或结构化数据文本"},
                "variables": {"type": "string", "description": "变量列表及类型说明"},
                "research_questions": {"type": "string", "description": "研究问题或假设"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["descriptive", "inferential", "regression", "scale", "auto"],
                    "description": "分析类型偏好",
                },
            },
            "required": ["data_description"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "定量", "量化", "统计", "回归", "相关分析", "假设检验", "t检验",
            "方差分析", "ANOVA", "因子分析", "信度", "效度", "描述统计",
            "频数", "均值", "标准差", "p值", "显著性", "数据", "数值",
            "quantitative", "statistics", "regression", "correlation",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.15, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        data_desc = user_input.get("data_description", "")
        variables = user_input.get("variables", "")
        research_q = user_input.get("research_questions", "")
        analysis_type = user_input.get("analysis_type", "auto")

        prompt = (
            f"数据描述：{data_desc[:4000]}\n"
            f"变量信息：{variables}\n"
            f"研究问题：{research_q}\n"
            f"分析类型偏好：{analysis_type}\n\n"
            "请按照系统提示的框架输出完整的定量分析方案。"
        )
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.4, max_tokens=4096)
        return SkillResult(content=response)
