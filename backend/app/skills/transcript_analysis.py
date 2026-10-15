from app.skills.base import BaseSkill, SkillResult


class TranscriptAnalysisSkill(BaseSkill):
    name = "transcript_analysis"
    description = "访谈转录分析与编码：主题提取、情感分析、编码框架、方法论反思"
    version = "0.1.0"

    def system_prompt(self, context: dict | None = None) -> str:
        ctx_str = str(context) if context else ""
        return (
            "你是一位质性研究分析专家，精通扎根理论、主题分析和内容分析等编码方法。\n"
            "你的任务是对田野访谈转录文本进行系统化的结构化分析。\n\n"
            "输出要求（用 Markdown 格式）：\n\n"
            "## 一、核心发现（3-5个关键发现）\n"
            "- 每个发现用一句话概括，附一段转录原文作为证据\n\n"
            "## 二、主题编码\n"
            "- 识别2-5个主要主题（一级编码）\n"
            "- 每个主题下列出2-3个子主题（二级编码）\n"
            "- 标注每个主题在文本中的出现频率（高频/中频/低频）\n\n"
            "## 三、概念关系图\n"
            "- 描述主题之间的关联（因果关系、并列关系、层级关系）\n"
            "- 尝试提取一个核心范畴（选择性编码）\n\n"
            "## 四、情感与态度分析\n"
            "- 受访者的整体情绪基调（积极/消极/中性/混合）\n"
            "- 对特定话题的情感变化（如由平静转为激动）\n\n"
            "## 五、未充分展开的话题\n"
            "- 列出受访者提到但未深入的关键词/话题\n"
            "- 建议后续访谈中应追问的方向\n\n"
            "## 六、方法论反思\n"
            "- 访谈者的问题是否有效（开放/封闭、引导/中立）\n"
            "- 改进建议\n\n"
            f"额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "完整访谈转录文本"},
                "research_topic": {"type": "string", "description": "研究主题（可选，用于定向分析）"},
                "coding_framework": {
                    "type": "string",
                    "enum": ["grounded_theory", "thematic_analysis", "content_analysis", "auto"],
                    "description": "编码方法偏好",
                },
            },
            "required": ["transcript"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "编码", "主题分析", "转录", "transcript", "扎根理论", "内容分析",
            "质性分析", "定性分析", "编码框架", "主题提取", "coding", "theme",
            "文本分析", "访谈分析", "语料分析",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.22, 1), 1.0)

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        transcript = user_input.get("transcript", "")
        research_topic = user_input.get("research_topic", "")
        coding = user_input.get("coding_framework", "auto")

        prompt = f"研究主题：{research_topic}\n编码方法偏好：{coding}\n\n转录文本：\n{transcript[:6000]}\n\n请按照系统提示的框架进行完整的编码分析。"
        messages = [
            {"role": "system", "content": self.system_prompt(context)},
            {"role": "user", "content": prompt},
        ]
        response = await ai_service.chat(messages, temperature=0.5, max_tokens=4096)
        return SkillResult(content=response)
