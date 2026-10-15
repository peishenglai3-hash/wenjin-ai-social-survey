"""AI-assisted qualitative coding skill.

This module provides the small adapter expected by the codebook service. It
returns candidate codes only; a researcher must review and accept them before
they become durable project data.
"""

from app.skills.base import BaseSkill, SkillResult


class QualitativeCodingSkill(BaseSkill):
    name = "qualitative_coding"
    description = "质性材料的开放编码、主题编码和编码簿候选建议"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        context_text = str(context) if context else ""
        return (
            "你是一位严谨的质性研究编码助手。你的输出只是供研究者审阅的候选编码，"
            "不能替代研究者判断，也不能把受访者身份或未提供的事实补写出来。\n"
            "请依据文本证据提出少量、可区分、可复用的编码，并保留不确定性。\n"
            "必须输出 JSON 对象：{\"codes\":[{\"name\":\"...\",\"definition\":\"...\","
            "\"evidence\":\"...\",\"confidence\":0.0}]}。"
            "不要输出 markdown 代码围栏。\n"
            f"额外上下文：{context_text}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "待编码的访谈或田野文本"},
                "research_question": {"type": "string", "description": "研究问题（可选）"},
                "coding_paradigm": {
                    "type": "string",
                    "enum": ["auto", "open", "thematic", "grounded_theory", "content_analysis"],
                },
                "existing_codes": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["transcript"],
        }

    def match(self, user_intent: str) -> float:
        keywords = ["质性编码", "定性编码", "编码簿", "开放编码", "主题编码", "coding", "codebook"]
        intent = user_intent.lower()
        hits = sum(1 for keyword in keywords if keyword.lower() in intent)
        return min(hits / 2.0, 1.0)

    async def execute(
        self, ai_service, user_input: dict, context: dict | None = None
    ) -> SkillResult:
        transcript = str(user_input.get("transcript", ""))[:8000]
        research_question = str(user_input.get("research_question", ""))[:1000]
        paradigm = user_input.get("coding_paradigm", "auto")
        existing_codes = user_input.get("existing_codes", [])
        prompt = (
            f"研究问题：{research_question}\n"
            f"编码范式：{paradigm}\n"
            f"已有编码：{existing_codes}\n\n"
            f"待编码文本：\n{transcript}\n\n"
            "请提出可审阅的编码候选，并为每个候选附上简短证据片段和置信度。"
        )
        response = await ai_service.chat(
            [
                {"role": "system", "content": self.system_prompt(context)},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        return SkillResult(content=response)
