"""Topic argumentation skill — deep research direction analysis and refinement."""

from app.skills.base import BaseSkill, SkillResult


class TopicArgumentationSkill(BaseSkill):
    name = "topic_argumentation"
    description = "深度论证研究方向：选题聚焦、理论框架、方法匹配、抽样策略、局限应对"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        ctx_str = str(context) if context else ""
        return (
            "你是一位资深的社会科学研究方法论导师，拥有20年指导学生开题和论文写作的经验。\n"
            "你的任务是对用户提出的研究方向进行深度学术论证，帮助ta将模糊的想法转化为可操作的研究方案。\n\n"
            "输出要求（用 Markdown 格式，至少2500字）：\n\n"
            "## 一、选题聚焦\n"
            "- 将研究主题从模糊转向精确：明确研究问题、研究对象、研究范围\n"
            "- 指出选题的理论意义和现实意义\n"
            "- 提供3-5个具体可操作的研究问题（research questions）\n"
            "- 评估选题的可行性（时间、资源、数据获取难度）\n\n"
            "## 二、理论框架\n"
            "- 推荐2-3个适合的理论视角（说明为什么这些理论适合该选题）\n"
            "- 简要说明每个理论的核心概念及其在研究中的应用方式\n"
            "- 建议如何在文献综述中组织这些理论\n\n"
            "## 三、方法匹配\n"
            "- 判断研究问题最适合质性、量化还是混合方法\n"
            "- 给出方法论选择的论证（为什么是X而不是Y）\n"
            "- 推荐具体的研究设计（案例研究/问卷调查/民族志/实验/内容分析等）\n"
            "- 说明数据收集方式（访谈/问卷/观察/档案/混合）\n\n"
            "## 四、抽样策略\n"
            "- 明确目标总体和可及总体\n"
            "- 推荐抽样方式（概率/非概率，并说明理由）\n"
            "- 估算样本量并给出依据\n"
            "- 讨论抽样偏差的可能来源及控制方法\n\n"
            "## 五、局限与应对\n"
            "- 预判该研究可能面临的方法论局限\n"
            "- 预判田野实践中的困难（进入现场/拒访/社会称许性等）\n"
            "- 给出每种局限的应对策略\n\n"
            "## 六、后续步骤建议\n"
            "- 建议用户下一步该做什么（文献综述/预访谈/问卷预测试等）\n"
            "- 推荐3-5篇必读文献或参考书目\n\n"
            "注意事项：\n"
            "- 论证要有学术深度，不要泛泛而谈\n"
            "- 所有建议必须有方法论依据\n"
            "- 鼓励用户，但也明确指出潜在的困难和风险\n"
            "- 语言风格：专业但不晦涩，像是在办公室里和学生聊天\n\n"
            f"额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "research_direction": {
                    "type": "string",
                    "description": "用户的研究方向描述（可以比较模糊）",
                },
                "paradigm_preference": {
                    "type": "string",
                    "enum": ["qualitative", "quantitative", "mixed", "unsure"],
                    "description": "研究范式偏好",
                },
                "user_level": {
                    "type": "string",
                    "enum": ["undergraduate", "graduate", "researcher", "grassroots"],
                    "description": "用户身份/学术阶段",
                },
                "context_info": {
                    "type": "string",
                    "description": "补充信息（田野地点、资源限制、已有数据等）",
                },
            },
            "required": ["research_direction"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "选题", "论证", "研究方向", "开题", "研究问题", "研究设计",
            "理论框架", "论文选题", "方法选择", "范式", "研究方案",
            "topic", "research direction", "proposal", "research question",
            "research design", "theoretical framework", "开题报告",
            "研究题目", "课题", "论文方向",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.2, 1), 1.0)

    async def execute(
        self, ai_service, user_input: dict, context: dict | None = None
    ) -> SkillResult:
        direction = user_input.get("research_direction", "")
        paradigm = user_input.get("paradigm_preference", "unsure")
        level = user_input.get("user_level", "undergraduate")
        extra = user_input.get("context_info", "")

        paradigm_map = {
            "qualitative": "质性研究",
            "quantitative": "量化研究",
            "mixed": "混合方法",
            "unsure": "尚未确定",
        }
        level_map = {
            "undergraduate": "本科生",
            "graduate": "研究生",
            "researcher": "研究人员",
            "grassroots": "基层工作者",
        }

        prompt = (
            f"研究方向：{direction}\n"
            f"范式偏好：{paradigm_map.get(paradigm, paradigm)}\n"
            f"用户背景：{level_map.get(level, level)}\n"
        )
        if extra:
            prompt += f"补充信息：{extra}\n"
        prompt += "\n请按照系统提示的六个维度，输出完整的选题论证方案。"

        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.7, max_tokens=4096)
        return SkillResult(content=response)
