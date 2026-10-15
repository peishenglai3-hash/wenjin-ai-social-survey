from app.skills.base import BaseSkill, SkillResult


class SamplingDesignSkill(BaseSkill):
    name = "sampling_design"
    description = "抽样方案设计：抽样框确定、抽样方法选择、样本量估算、偏差控制、实施建议"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        ctx_str = str(context) if context else ""
        return (
            "你是一位社会调查研究方法专家，精通抽样理论和实践。\n"
            "你的任务是根据用户的研究需求，设计一套科学、可行的抽样方案。\n\n"
            "输出要求（用 Markdown 格式）：\n\n"
            "## 一、目标总体与抽样框\n"
            "- 明确界定目标总体（谁是被研究的对象）\n"
            "- 可及总体的范围\n"
            "- 抽样框的构建方式（如：花名册/地图/随机拨号/网络面板等）\n"
            "- 抽样框可能存在的覆盖误差\n\n"
            "## 二、抽样方法选择\n"
            "- 推荐1-2种抽样方法并论证理由\n"
            "- 概率抽样：简单随机/系统/分层/整群/多阶段\n"
            "- 非概率抽样：配额/立意/滚雪球/便利/最大差异\n"
            "- 混合抽样策略的可行性\n\n"
            "## 三、样本量估算\n"
            "- 基于统计功效的样本量计算（如适用）\n"
            "- 考虑设计效应（deff）的调整\n"
            "- 考虑无应答率的余量\n"
            "- 各子群体的最低样本量要求\n\n"
            "## 四、分层与配额方案（如适用）\n"
            "- 分层变量选择（性别/年龄/地域/教育等）\n"
            "- 各层的比例（比例分配/最优分配）\n"
            "- 配额表设计\n\n"
            "## 五、偏差控制策略\n"
            "- 抽样偏差的可能来源\n"
            "- 无应答偏差的应对\n"
            "- 志愿者偏差的控制\n"
            "- 加权调整方案\n\n"
            "## 六、实施操作指南\n"
            "- 抽样步骤的分步说明\n"
            "- 替换规则（何时及如何替换样本）\n"
            "- 实地操作的注意事项\n"
            "- 质量控制的检查点\n\n"
            f"额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "research_topic": {"type": "string", "description": "研究主题"},
                "target_population": {"type": "string", "description": "目标人群描述"},
                "population_size": {"type": "string", "description": "总体规模估计"},
                "research_paradigm": {"type": "string", "enum": ["quantitative", "qualitative", "mixed"], "description": "研究范式"},
                "resources": {"type": "string", "description": "可用资源（预算/人力/时间）"},
                "access_constraints": {"type": "string", "description": "进入田野的约束条件"},
            },
            "required": ["research_topic", "target_population"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "抽样", "样本", "sample", "sampling", "样本量", "抽样框",
            "概率抽样", "非概率抽样", "分层抽样", "整群抽样", "配额",
            "滚雪球", "随机抽样", "样本设计", "抽样方案", "抽样方法",
            "总体", "population", "设计效应", "误差",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.18, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        topic = user_input.get("research_topic", "")
        population = user_input.get("target_population", "")
        pop_size = user_input.get("population_size", "")
        paradigm = user_input.get("research_paradigm", "mixed")
        resources = user_input.get("resources", "")
        constraints = user_input.get("access_constraints", "")

        prompt = (
            f"研究主题：{topic}\n"
            f"目标人群：{population}\n"
            f"总体规模：{pop_size}\n"
            f"研究范式：{paradigm}\n"
            f"可用资源：{resources}\n"
            f"约束条件：{constraints}\n\n"
            "请按照系统提示的框架，输出完整的抽样方案设计。"
        )
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.5, max_tokens=4096)
        return SkillResult(content=response)
