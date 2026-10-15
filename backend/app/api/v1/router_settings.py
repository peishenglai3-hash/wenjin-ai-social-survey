"""User Settings endpoints — AI behaviour, UI preferences, project defaults, privacy."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.deps_auth import require_user, get_current_profile
from app.models.user import UserAccount
from app.models.survey import UserProfile

router = APIRouter(prefix="/settings", tags=["settings"])

# ── Spectrum dimension metadata ─────────────────────────────────────

SPECTRUM_DIMENSIONS = [
    {
        "id": "theory_driven",
        "label": "理论导向",
        "left": "理论驱动",
        "right": "经验驱动",
        "desc": "你更倾向于从理论出发推导假设，还是从经验观察中归纳规律？",
    },
    {
        "id": "methodological_rigidity",
        "label": "方法论刚性",
        "left": "严谨规范",
        "right": "灵活探索",
        "desc": "你更偏好严格遵循方法手册，还是根据实际情况灵活调整？",
    },
    {
        "id": "analysis_depth",
        "label": "分析深度",
        "left": "广度优先",
        "right": "深度优先",
        "desc": "你倾向于覆盖多个主题（广度），还是深耕少数核心问题（深度）？",
    },
    {
        "id": "structure_preference",
        "label": "结构性",
        "left": "结构化",
        "right": "开放式",
        "desc": "你更喜欢用固定提纲和结构化工具，还是开放式、非结构化的探索？",
    },
    {
        "id": "participation_level",
        "label": "参与度",
        "left": "旁观观察",
        "right": "深度参与",
        "desc": "你在调查中倾向于保持距离观察，还是深度融入参与？",
    },
    {
        "id": "tech_dependency",
        "label": "技术依赖",
        "left": "低技术",
        "right": "高技术",
        "desc": "你偏好传统纸笔/面对面方式，还是积极使用数字工具和AI辅助？",
    },
    {
        "id": "writing_style",
        "label": "写作风格",
        "left": "学术正式",
        "right": "通俗亲和",
        "desc": "你的写作风格更接近学术论文，还是通俗报告/故事叙述？",
    },
    {
        "id": "learning_preference",
        "label": "学习偏好",
        "left": "示范引导",
        "right": "自主探索",
        "desc": "你更喜欢系统给你明确示范和步骤，还是提供方向后自己探索？",
    },
]

# ── Setting option metadata ──────────────────────────────────────────

SETTINGS_DEFAULTS = {
    "ai_temperature": 0.5,
    "ai_model_pref": "auto",
    "ai_hint_frequency": "standard",
    "ui_font_size": "medium",
    "ui_high_contrast": False,
    "default_export_format": "report",
    "auto_save_interval": "60s",
}

SETTINGS_OPTIONS = {
    "ai_model_pref": [
        {"id": "auto", "label": "智能切换（推荐）", "desc": "根据任务复杂度自动选择模型"},
        {"id": "flash", "label": "经济模式", "desc": "响应更快，成本更低，适合简单任务"},
        {"id": "pro", "label": "深度模式", "desc": "更深入的分析，适合复杂学术任务"},
    ],
    "ai_hint_frequency": [
        {"id": "off", "label": "关闭", "desc": "不主动推送提示"},
        {"id": "low", "label": "少量（1-2条）", "desc": "仅在关键节点提示"},
        {"id": "standard", "label": "标准（3-5条）", "desc": "平衡的提示频率"},
        {"id": "high", "label": "密集（5+条）", "desc": "适合新手，提供充分引导"},
    ],
    "ui_font_size": [
        {"id": "small", "label": "小（14px）"},
        {"id": "medium", "label": "中（16px）"},
        {"id": "large", "label": "大（18px）"},
    ],
    "default_export_format": [
        {"id": "report", "label": "调查报告", "theme": "academic"},
        {"id": "paper_outline", "label": "论文大纲", "theme": "academic"},
        {"id": "proposal", "label": "项目申报书", "theme": "academic"},
        {"id": "official_document", "label": "公文写作", "theme": "government"},
        {"id": "policy_brief", "label": "政策建议专报", "theme": "government"},
        {"id": "gov_report", "label": "政务调研报告", "theme": "government"},
        {"id": "knowledge_summary", "label": "知识总结", "theme": "youth"},
        {"id": "learning_report", "label": "学习探索报告", "theme": "youth"},
        {"id": "reflection", "label": "实践反思", "theme": "youth"},
    ],
    "auto_save_interval": [
        {"id": "30s", "label": "30秒"},
        {"id": "60s", "label": "1分钟"},
        {"id": "300s", "label": "5分钟"},
        {"id": "off", "label": "关闭自动保存"},
    ],
}

# Fields that can be updated via PATCH /settings
UPDATABLE_FIELDS = (
    list(SETTINGS_DEFAULTS.keys())
    + [d["id"] for d in SPECTRUM_DIMENSIONS]
)

# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/defaults")
async def get_settings_defaults():
    """Return all settings metadata: spectrum dimensions, option lists, defaults."""
    return {
        "spectrum_dimensions": SPECTRUM_DIMENSIONS,
        "defaults": SETTINGS_DEFAULTS,
        "options": SETTINGS_OPTIONS,
    }


@router.get("/{profile_id}")
async def get_settings(
    profile_id: int,
    user: UserAccount = Depends(require_user),
    profile: UserProfile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Get current settings and spectrum values for a user profile."""
    # Verify ownership - prevent horizontal privilege escalation
    if profile.id != profile_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(UserProfile).where(UserProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"error": "Profile not found"}

    # Build spectrum dict
    spectrum = {}
    for dim in SPECTRUM_DIMENSIONS:
        spectrum[dim["id"]] = getattr(profile, dim["id"], 3)

    # Build settings dict
    settings = {}
    for key in SETTINGS_DEFAULTS:
        val = getattr(profile, key, SETTINGS_DEFAULTS[key])
        settings[key] = val

    return {
        "profile_id": profile.id,
        "theme": profile.theme_preference,
        "spectrum": spectrum,
        "settings": settings,
    }


@router.patch("/{profile_id}")
async def update_settings(
    profile_id: int,
    payload: dict,
    user: UserAccount = Depends(require_user),
    profile: UserProfile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Update one or more settings/spectrum fields for a user profile."""
    # Verify ownership - prevent horizontal privilege escalation
    if profile.id != profile_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(UserProfile).where(UserProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"error": "Profile not found"}

    updated = []
    for field, value in payload.items():
        if field in UPDATABLE_FIELDS and hasattr(profile, field):
            setattr(profile, field, value)
            updated.append(field)

    await db.commit()
    await db.refresh(profile)

    # Return updated spectrum + settings
    spectrum = {}
    for dim in SPECTRUM_DIMENSIONS:
        spectrum[dim["id"]] = getattr(profile, dim["id"], 3)

    settings_data = {}
    for key in SETTINGS_DEFAULTS:
        settings_data[key] = getattr(profile, key, SETTINGS_DEFAULTS[key])

    return {
        "profile_id": profile.id,
        "updated_fields": updated,
        "spectrum": spectrum,
        "settings": settings_data,
    }


@router.post("/{profile_id}/reset")
async def reset_settings(
    profile_id: int,
    user: UserAccount = Depends(require_user),
    profile: UserProfile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Reset all settings and spectrum values to defaults."""
    # Verify ownership - prevent horizontal privilege escalation
    if profile.id != profile_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(UserProfile).where(UserProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"error": "Profile not found"}

    # Reset spectrum to 3 (midpoint)
    for dim in SPECTRUM_DIMENSIONS:
        setattr(profile, dim["id"], 3)

    # Reset settings to defaults
    for key, default_val in SETTINGS_DEFAULTS.items():
        setattr(profile, key, default_val)

    await db.commit()
    await db.refresh(profile)

    return {"profile_id": profile.id, "message": "All settings reset to defaults"}
