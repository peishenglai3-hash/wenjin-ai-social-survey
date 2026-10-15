from app.skills.base import BaseSkill, SkillResult
from app.services.confidence_service import from_llm_response


class FieldworkCoachSkill(BaseSkill):
    name = "fieldwork_coach"
    description = "实时访谈教练：追问方向、话术建议、注意事项、矛盾点标记"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        ctx_str = str(context) if context else ""
        return (
            "你是一位资深的田野调查访谈教练，拥有丰富的深度访谈和焦点小组主持经验。\n"
            "你的任务是基于实时访谈转录文本，为访谈者提供即时、可操作的建议。\n\n"
            "输出要求（用中文，简短直接）：\n"
            "1. 追问方向：基于受访者最新回答，指出1-2个值得深挖的方向\n"
            "2. 话术建议：给出1-2句具体的追问措辞\n"
            "3. 注意事项：提醒避免引导性问题、保持中立、注意非语言信息\n"
            "4. 矛盾点标记：如受访者前后表述不一致，指出并建议如何温和追问\n"
            "5. 节奏评估：当前访谈节奏是否合适（过快/过慢/偏离主题）\n\n"
            "每条建议控制在30字以内，输出为JSON数组格式。\n"
            f"额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "最近对话片段"},
                "scenario": {"type": "string", "description": "访谈场景类型"},
                "phase": {"type": "string", "enum": ["opening", "main", "closing"], "description": "访谈阶段"},
                "interviewee_profile": {"type": "string", "description": "受访者基本信息（可选）"},
            },
            "required": ["transcript"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "访谈", "追问", "话术", "采访", "教练", "coach", "interview",
            "深度访谈", "焦点小组", "田野访谈", "质性访谈", "半结构化",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.25, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        transcript = user_input.get("transcript", "")
        scenario = user_input.get("scenario", "community_interview")
        phase = user_input.get("phase", "main")

        prompt = (
            f"访谈场景: {scenario}\n"
            f"访谈阶段: {phase}\n"
            f"最近对话片段:\n{transcript}\n\n"
            "请提供3-5条即时建议，输出为JSON数组格式: [\"建议1\", \"建议2\", ...]"
        )
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.5, max_tokens=1024)
        return SkillResult(content=response, confidence=from_llm_response(response))
