from app.skills.base import BaseSkill, SkillResult


class LiteratureReviewSkill(BaseSkill):
    name = "literature_review"
    description = "文献检索与综述辅助：关键词建议、文献脉络梳理、理论框架构建、研究空白识别"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        ctx_str = str(context) if context else ""
        return (
            "你是一位社会科学文献综述专家，擅长系统性地梳理研究脉络和构建理论框架。\n"
            "你的任务是根据用户的研究主题，提供文献检索和综述写作的指导。\n\n"
            "输出要求（用 Markdown 格式）：\n\n"
            "## 一、检索关键词建议\n"
            "- 中英文核心关键词各5-8个\n"
            "- 关键词组合策略（布尔运算符建议）\n"
            "- 推荐检索数据库（CNKI/万方/Web of Science/Scopus/Google Scholar等）\n\n"
            "## 二、文献脉络梳理\n"
            "- 该领域的经典文献（3-5篇奠基性研究）\n"
            "- 近5年的重要进展（3-5篇高引/高影响力文献）\n"
            "- 中文文献与英文文献的研究侧重差异\n\n"
            "## 三、理论框架构建\n"
            "- 推荐2-3个可用的理论视角\n"
            "- 各理论的适用性分析\n"
            "- 理论整合的可能性\n\n"
            "## 四、研究空白识别\n"
            "- 已有研究的共识和争议\n"
            "- 方法论层面的空白\n"
            "- 实证层面的空白\n"
            "- 情境/人群/地域的空白\n\n"
            "## 五、文献综述结构建议\n"
            "- 建议的章节结构\n"
            "- 各节应涵盖的内容要点\n"
            "- 避免的常见写作误区\n\n"
            f"额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "research_topic": {"type": "string", "description": "研究主题"},
                "discipline": {"type": "string", "description": "学科领域（社会学/心理学/公共管理/传播学等）"},
                "scope": {"type": "string", "enum": ["narrow", "moderate", "broad"], "description": "综述范围"},
                "language_preference": {"type": "string", "enum": ["chinese", "english", "both"], "description": "语言偏好"},
            },
            "required": ["research_topic"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "文献", "综述", "文献综述", "literature", "review", "论文",
            "检索", "参考文献", "引用", "前人研究", "研究现状", "学术史",
            "理论框架", "概念框架", "theoretical", "bibliography",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.22, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        topic = user_input.get("research_topic", "")
        discipline = user_input.get("discipline", "社会学")
        scope = user_input.get("scope", "moderate")
        lang = user_input.get("language_preference", "both")

        prompt = (
            f"研究主题：{topic}\n"
            f"学科领域：{discipline}\n"
            f"综述范围：{scope}\n"
            f"语言偏好：{lang}\n\n"
            "请按照系统提示的框架，输出完整的文献综述指导方案。"
        )
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.6, max_tokens=4096)
        return SkillResult(content=response)
