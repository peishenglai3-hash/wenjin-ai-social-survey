"""
Volcano Engine / ARK — Doubao LLM emotion & semantic analysis service.

Uses Doubao Seed 2.0 via ARK API (OpenAI-compatible) for:
  - Deep semantic emotion analysis (6-class: angry/happy/neutral/sad/anxious/avoidant)
  - Interview quality assessment
  - Real-time coaching hints for interviewer HUD

ARK API is OpenAI-compatible: POST /chat/completions
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field

from httpx import AsyncClient

from app.config import settings

logger = logging.getLogger(__name__)

# ── Emotion label normalization (Doubao returns Chinese labels) ──────

EMOTION_LABEL_MAP = {
    "angry": "angry", "anger": "angry", "愤怒": "angry", "生气": "angry", "激动": "angry",
    "happy": "happy", "开心": "happy", "高兴": "happy", "兴奋": "happy", "愉悦": "happy",
    "neutral": "neutral", "中立": "neutral", "平静": "neutral", "平淡": "neutral",
    "sad": "sad", "悲伤": "sad", "难过": "sad", "伤心": "sad", "沮丧": "sad", "低落": "sad",
    "anxious": "anxious", "焦虑": "anxious", "紧张": "anxious", "不安": "anxious", "担忧": "anxious",
    "avoidant": "avoidant", "回避": "avoidant", "防御": "avoidant", "抗拒": "avoidant", "抵触": "avoidant",
    "恐惧": "anxious", "害怕": "anxious", "恐惧/焦虑": "anxious",
    "失望": "sad", "遗憾": "sad", "欣慰": "happy", "释然": "happy", "感激": "happy", "感动": "happy",
    "困惑": "anxious", "矛盾": "avoidant", "犹豫": "avoidant",
    "惊讶": "neutral", "好奇": "happy", "厌恶": "angry", "反感": "angry",
    "无奈": "sad", "无助": "sad",
}


def _normalize_emotion(label: str) -> str:
    """Normalize Chinese or English emotion labels to internal labels."""
    if not label:
        return "neutral"
    cleaned = label.strip().lower()
    if cleaned in EMOTION_LABEL_MAP:
        return EMOTION_LABEL_MAP[cleaned]
    for key, val in EMOTION_LABEL_MAP.items():
        if key in cleaned or cleaned in key:
            return val
    return "neutral"


@dataclass
class EmotionAnalysis:
    """Detailed emotion analysis result from Doubao."""
    primary_emotion: str = "neutral"       # angry|happy|neutral|sad|anxious|avoidant
    secondary_emotion: str = ""
    confidence: float = 0.0
    intensity: float = 0.5                 # 0.0–1.0
    valence: float = 0.0                   # -1.0 (negative) to +1.0 (positive)
    arousal: float = 0.5                   # 0.0 (calm) to 1.0 (excited)
    cues: list[str] = field(default_factory=list)  # linguistic cues detected
    suggested_response: str = ""           # coaching hint for interviewer
    raw_response: str = ""


class VolcanoEmotion:
    """Emotion analysis via Volcano Engine Doubao LLM.

    Specialized for fieldwork interview scenarios — detects nuanced emotions
    beyond simple positive/negative, and generates coaching suggestions.
    """

    def __init__(self, model: str | None = None):
        self.api_key = settings.volcano_api_key
        self.base_url = settings.volcano_base_url.rstrip("/")
        self.model = model or settings.volcano_emotion_model
        self._client: AsyncClient | None = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def _get_client(self) -> AsyncClient:
        if self._client is None:
            self._client = AsyncClient(timeout=60)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def analyze_emotion(
        self,
        text: str,
        speaker_role: str = "respondent",
        context: str = "",
    ) -> EmotionAnalysis:
        """Analyze the emotional content of an interview utterance.

        Args:
            text: The utterance to analyze (respondent or interviewer speech)
            speaker_role: "respondent" or "interviewer"
            context: Optional preceding dialogue for context
        """
        if not self.available:
            return EmotionAnalysis()

        t0 = time.time()

        system_prompt = (
            "你是一个田野访谈情感分析专家。分析受访者发言的情感状态，"
            "识别微妙情绪线索（如回避、恐惧、兴奋、犹豫等），"
            "并为访谈者提供简短的应对建议。"
            "情感标签使用中文（愤怒/开心/中立/悲伤/焦虑/回避）。"
            "只输出JSON，不要markdown代码块，不要额外文字。"
        )

        context_block = f"\n对话上下文:\n{context}\n" if context else ""
        user_prompt = (
            f"角色: {speaker_role}\n"
            f"{context_block}"
            f"发言内容: \"{text[:800]}\"\n\n"
            '输出JSON（情感标签用中文）:\n'
            '{\n'
            '  "primary_emotion": "愤怒|开心|中立|悲伤|焦虑|回避",\n'
            '  "secondary_emotion": "同上或空",\n'
            '  "confidence": 0.85,\n'
            '  "intensity": 0.7,\n'
            '  "valence": -0.5,\n'
            '  "arousal": 0.6,\n'
            '  "cues": ["语言线索1"],\n'
            '  "suggested_response": "简短应对建议"\n'
            '}'
        )

        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 512,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            result = self._parse(content)
            result.raw_response = content
            logger.info(
                f"VolcanoEmotion: {result.primary_emotion} "
                f"(conf={result.confidence:.2f}, {time.time()-t0:.1f}s)"
            )
            return result
        except Exception as e:
            logger.warning(f"VolcanoEmotion failed: {e}")
            return EmotionAnalysis()

    async def analyze_batch(
        self,
        utterances: list[dict],
        speaker_role: str = "respondent",
    ) -> list[EmotionAnalysis]:
        """Analyze a batch of utterances. Returns one result per utterance."""
        results: list[EmotionAnalysis] = []
        # Build context from previous utterances
        context_parts: list[str] = []
        for i, u in enumerate(utterances):
            text = u.get("text", "")
            ctx = "\n".join(context_parts[-5:])  # last 5 as context
            result = await self.analyze_emotion(text, speaker_role, ctx)
            results.append(result)
            context_parts.append(f"[{speaker_role}]: {text}")
        return results

    async def generate_hint(
        self,
        transcript_snippet: str,
        current_emotion: str = "neutral",
    ) -> str:
        """Generate a real-time coaching hint for the interviewer."""
        if not self.available:
            return ""

        prompt = (
            f"当前访谈片段:\n{transcript_snippet[:600]}\n"
            f"受访者当前情绪: {current_emotion}\n\n"
            "作为访谈教练，给访谈者一个简短的实时建议（20字内），"
            "帮助改善访谈质量。例如：追问细节、变换角度、给予共情、放慢节奏等。"
            "只输出建议文本，不加引号。"
        )

        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个田野访谈教练。只输出简短建议。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.6,
                    "max_tokens": 128,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Volcano hint generation failed: {e}")
            return ""

    async def health(self) -> bool:
        """Quick health check."""
        if not self.available:
            return False
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return resp.status_code == 200
        except Exception:
            logger.warning("Volcano health check failed", exc_info=True)
            return False

    @staticmethod
    def _parse(content: str) -> EmotionAnalysis:
        try:
            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            data = json.loads(text)
            raw_primary = str(data.get("primary_emotion", "neutral"))
            raw_secondary = str(data.get("secondary_emotion", ""))
            return EmotionAnalysis(
                primary_emotion=_normalize_emotion(raw_primary),
                secondary_emotion=_normalize_emotion(raw_secondary) if raw_secondary else "",
                confidence=float(data.get("confidence", 0)),
                intensity=float(data.get("intensity", 0.5)),
                valence=float(data.get("valence", 0)),
                arousal=float(data.get("arousal", 0.5)),
                cues=data.get("cues", []),
                suggested_response=str(data.get("suggested_response", "")),
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # Last-resort: try to find emotion keywords in raw text
            logger.warning(f"VolcanoEmotion JSON parse failed: {e}")
            for label in ["angry", "sad", "happy", "anxious", "avoidant", "愤怒", "悲伤", "开心", "焦虑", "回避"]:
                if label in content:
                    return EmotionAnalysis(primary_emotion=_normalize_emotion(label), confidence=0.3)
            return EmotionAnalysis()


volcano_emotion = VolcanoEmotion()
