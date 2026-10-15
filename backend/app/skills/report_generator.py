from app.skills.base import BaseSkill, SkillResult
from app.skills.mode_prompts import get_mode_modifier


class ReportGeneratorSkill(BaseSkill):
    name = "report_generator"
    description = "调查报告生成：结构化报告框架、学术写作辅助、图表建议、格式规范"
    version = "0.2.0"

    def system_prompt(self, context: dict | None = None) -> str:
        theme = (context or {}).get("theme", "academic")
        mode_hint = get_mode_modifier(theme, "system")
        export_fmt = get_mode_modifier(theme, "export")

        return (
            "你是一位社会科学报告写作专家，精通学术论文、政务调研报告和学习报告的撰写规范。\n"
            "你的任务是根据用户的项目资料，生成一份符合其使用场景的结构化报告。\n\n"
            f"{mode_hint}\n\n"
            f"输出框架要求：\n{export_fmt}\n\n"
            "使用 Markdown 格式输出。"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "project_data": {"type": "string", "description": "项目所有相关文本数据"},
                "report_type": {
                    "type": "string",
                    "enum": ["academic", "policy", "general", "auto"],
                    "description": "报告类型",
                },
                "target_audience": {"type": "string", "description": "目标读者群体"},
                "word_limit": {"type": "string", "description": "字数要求（可选）"},
                "theme": {"type": "string", "description": "模式: academic/government/youth"},
            },
            "required": ["project_data"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "报告", "report", "撰写", "写作", "写报告", "生成报告",
            "调查报告", "研究报告", "成果报告", "结题", "汇报",
            "论文", "文章", "文稿", "草稿", "初稿",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.2, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        ctx = context or {}
        ctx["theme"] = user_input.get("theme", ctx.get("theme", "academic"))

        project_data = user_input.get("project_data", "")
        report_type = user_input.get("report_type", "auto")
        audience = user_input.get("target_audience", "学术同行")
        word_limit = user_input.get("word_limit", "")
        theme = ctx["theme"]

        prompt = (
            f"报告类型：{report_type}\n"
            f"目标读者：{audience}\n"
            f"字数要求：{word_limit}\n\n"
            f"项目资料：\n{project_data[:6000]}\n\n"
            f"{get_mode_modifier(theme, 'export')}\n\n"
            "请按照上述框架生成完整的调查报告。"
        )
        messages = [
            {"role": "system", "content": self.system_prompt(ctx)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.6, max_tokens=6144)
        return SkillResult(content=response)
