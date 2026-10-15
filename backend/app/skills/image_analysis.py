import base64
import io
import logging

from app.skills.base import BaseSkill, SkillResult
from app.services.ai import VisionNotSupportedError

logger = logging.getLogger(__name__)

# ── Image compression ──────────────────────────────────────────────

def _compress_image_base64(image_b64: str, max_dim: int = 1568, quality: int = 65) -> str:
    """Resize and compress a base64 JPEG/PNG for vision API limits.

    Qwen-VL input limit is ~129K tokens; a 2.6MB base64 image exceeds this.
    Resize to max_dim on longest edge and recompress as JPEG ~100-250KB.
    Falls back to original if PIL is unavailable or image is already small.
    """
    raw = base64.b64decode(image_b64)
    # Already small enough — skip processing
    if len(raw) < 180 * 1024:  # <180KB raw ≈ ~240KB base64
        return image_b64

    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed — cannot compress images for vision API")
        return image_b64

    try:
        img = Image.open(io.BytesIO(raw))
        # Convert RGBA → RGB for JPEG
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        # Resize if either dimension exceeds max_dim
        w, h = img.size
        scale = max_dim / max(w, h)
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        compressed = base64.b64encode(buf.getvalue()).decode()
        logger.info(
            f"Image compressed: {len(image_b64)//1024}KB → {len(compressed)//1024}KB "
            f"({img.size[0]}x{img.size[1]})"
        )
        return compressed
    except Exception as e:
        logger.warning(f"Image compression failed, sending original: {e}")
        return image_b64


class ImageAnalysisSkill(BaseSkill):
    name = "image_analysis"
    description = "田野图像分析：场景识别、文本提取(OCR)、物体检测、环境评估、视觉笔记"
    version = "0.3.0"

    # Short system prompt for vision API (must stay well under token limits)
    VISION_SYSTEM = (
        "你是一位田野调查视觉分析专家，擅长从现场照片中提取社会科学研究信息。"
        "请仔细观察图片，按照用户要求的框架输出系统的视觉分析。使用中文。"
    )

    # Full output framework — placed in user message, not system
    OUTPUT_FRAMEWORK = (
        "\n\n输出要求（用 Markdown 格式）：\n\n"
        "## 一、场景识别\n"
        "- 场景类型判断（室内/室外/自然/建成环境/公共空间/私人空间）\n"
        "- 场景功能推断\n"
        "- 场景中的人际互动线索\n\n"
        "## 二、关键元素提取\n"
        "- 人物：数量、性别/年龄估计、活动类型、互动模式\n"
        "- 物体：物品清单、功能分类、排列模式\n"
        "- 文字/符号：标识、标语、告示的内容和意义\n"
        "- 空间：布局特征、空间使用模式、边界与通道\n\n"
        "## 三、社会文化解读\n"
        "- 场景中反映的社会关系\n"
        "- 权力/地位的视觉符号\n"
        "- 文化规范与价值观的视觉表现\n"
        "- 与用户研究主题的关联分析\n\n"
        "## 四、研究价值评估\n"
        "- 该场景对研究问题的佐证价值\n"
        "- 建议的后续观察重点\n"
        "- 可能的三角验证方向（结合访谈/问卷）\n\n"
        "## 五、隐私与伦理提醒\n"
        "- 是否涉及可识别个人身份的信息\n"
        "- 公开发布前需要模糊化处理的内容\n"
        "- 知情同意的注意事项"
    )

    def system_prompt(self, context: dict | None = None, vision_available: bool = True) -> str:
        ctx_str = str(context) if context else ""
        vision_note = (
            ""
            if vision_available
            else "\n⚠️ 当前AI服务商不支持直接图像识别。用户已上传图片但我们将通过元数据和描述进行分析。请基于用户提供的描述信息尽力给出专业分析，并在各节中标注「基于描述推断」。\n"
        )
        return (
            "你是一位田野调查视觉分析专家，擅长从现场照片中提取有价值的社会科学研究信息。\n"
            "你的任务是根据用户提供的照片描述和分析需求，提供系统的视觉分析。\n\n"
            + vision_note
            + self.OUTPUT_FRAMEWORK
            + f"\n\n额外上下文：{ctx_str}"
        )

    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "image_description": {"type": "string", "description": "对照片内容的文字描述"},
                "research_topic": {"type": "string", "description": "研究主题（用于定向分析）"},
                "field_location": {"type": "string", "description": "田野地点"},
                "analysis_focus": {
                    "type": "string",
                    "enum": ["general", "social_interaction", "built_environment", "text_ocr", "objects", "auto"],
                    "description": "分析侧重点",
                },
            },
            "required": ["image_description"],
        }

    def match(self, user_intent: str) -> float:
        keywords = [
            "图片", "照片", "图像", "拍照", "视觉", "场景", "现场",
            "image", "photo", "picture", "visual", "scene", "camera",
            "观察", "实拍", "街景", "环境", "空间", "建筑", "设施",
            "OCR", "文字识别", "物体识别",
        ]
        intent_lower = user_intent.lower()
        hits = sum(1 for kw in keywords if kw in intent_lower)
        return min(hits / max(len(keywords) * 0.18, 1), 1.0)

    @staticmethod
    def _extract_image_metadata(image_base64: str) -> dict:
        """Extract basic metadata from a base64-encoded image without vision API."""
        try:
            img_bytes = base64.b64decode(image_base64)
            size_kb = len(img_bytes) / 1024
            # Detect basic image format from magic bytes
            magic = img_bytes[:4]
            fmt = "unknown"
            if magic[:3] == b"\xff\xd8\xff":
                fmt = "JPEG"
            elif magic[:4] == b"\x89PNG":
                fmt = "PNG"
            elif magic[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
                fmt = "WEBP"
            return {
                "format": fmt,
                "size_kb": round(size_kb, 1),
                "has_image": True,
            }
        except Exception:
            return {"format": "unknown", "size_kb": 0, "has_image": False}

    async def execute(self, ai_service, user_input: dict, context: dict | None = None) -> SkillResult:
        image_desc = user_input.get("image_description", "")
        research_topic = user_input.get("research_topic", "")
        location = user_input.get("field_location", "")
        focus = user_input.get("analysis_focus", "auto")

        image_b64 = (context or {}).get("image_base64", "")
        # Text-only fallback AI (DeepSeek) — has large context, avoids qwen-max 30K limit
        text_ai = (context or {}).get("text_ai", ai_service)
        vision_available = True
        vision_error = None

        # Try vision API if image is provided
        if image_b64:
            # Compress large images to stay within Qwen-VL 129K token limit
            image_b64 = _compress_image_base64(image_b64)

            # Check if we have a QwenVisionService (DashScope native API)
            from app.services.vision_qwen import QwenVisionService
            if isinstance(ai_service, QwenVisionService) and ai_service.is_available:
                try:
                    # Use short system prompt for vision — keeps total input small
                    user_prompt = (
                        f"研究主题：{research_topic}\n"
                        f"田野地点：{location}\n"
                        f"分析侧重点：{focus}\n"
                        f"照片描述：{image_desc or '(无)'}\n"
                        "请按照以下框架输出完整的视觉分析："
                        + self.OUTPUT_FRAMEWORK
                    )
                    response = await ai_service.analyze_image(
                        user_prompt, image_b64, temperature=0.6, max_tokens=4096
                    )
                    return SkillResult(
                        content=response,
                        metadata={"vision_used": True, "provider": "qwen-vl-native"},
                    )
                except Exception as e:
                    vision_available = False
                    vision_error = str(e)
                    logger.warning(f"Qwen Vision failed, falling back to text-only: {e}")
            else:
                # Legacy path: try OpenAI-compatible chat_with_image
                try:
                    user_prompt = (
                        f"研究主题：{research_topic}\n"
                        f"田野地点：{location}\n"
                        f"分析侧重点：{focus}\n"
                        f"照片描述：{image_desc or '(无)'}\n"
                        "请按照以下框架输出完整的视觉分析："
                        + self.OUTPUT_FRAMEWORK
                    )
                    response = await ai_service.chat_with_image(
                        user_prompt, image_b64, temperature=0.6, max_tokens=4096
                    )
                    return SkillResult(
                        content=response,
                        metadata={"vision_used": True, "provider": ai_service.base_url},
                    )
                except VisionNotSupportedError as e:
                    vision_available = False
                    vision_error = str(e)
                    logger.warning(f"Vision not supported, falling back to text-only: {e}")

        # Text-only path (or fallback from failed vision)
        # Use text_ai (DeepSeek) for fallback — it has a much larger context window
        # than qwen-max's 30K token limit
        meta = self._extract_image_metadata(image_b64) if image_b64 else {}
        meta_note = ""
        if image_b64 and not vision_available:
            meta_note = (
                f"\n\n[系统备注] 用户上传了一张 {meta.get('format', '未知格式')} 图片 "
                f"({meta.get('size_kb', 0)}KB)，但AI视觉分析未成功。"
                "请基于用户提供的文字描述进行分析，并在各节标注「基于描述推断」。"
            )

        prompt = (
            f"研究主题：{research_topic}\n"
            f"田野地点：{location}\n"
            f"分析侧重点：{focus}\n"
            f"照片描述：\n{image_desc or '(未提供文字描述)'}\n"
            + meta_note +
            "\n请按照系统提示的框架，输出完整的视觉分析。"
        )

        messages = [
            {"role": "system", "content": self.system_prompt(context, vision_available=vision_available)},
            {"role": "user", "content": prompt},
        ]
        response = await text_ai.chat(messages, temperature=0.6, max_tokens=4096)

        return SkillResult(
            content=response,
            metadata={
                "vision_used": False,
                "fallback_reason": vision_error,
                "image_meta": meta,
            },
        )
