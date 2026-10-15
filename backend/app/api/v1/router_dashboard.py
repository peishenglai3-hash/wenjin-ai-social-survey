"""Dashboard aggregation endpoint — unified home page data."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.deps_auth import get_current_profile
from app.middleware.token_logger import get_usage_summary
from app.models.survey import UserProfile, SurveyProject, SurveySession, AnalysisResult
from app.skills.mode_prompts import (
    build_spectrum_prompt,
    SPECTRUM_LABELS,
    SPECTRUM_PROMPT_MODIFIERS,
    get_mode_workflow,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ── Spectrum-based quick tips ──────────────────────────────────────

SPECTRUM_TIPS = {
    "theory_driven": {
        1: "你的理论导向很强——记得在理论框架中留出空间，让田野中的意外发现也能被看见。",
        2: "理论是你的锚点，但也别忘了倾听经验材料自身的逻辑。",
        4: "你倾向于从经验出发——试试在分析时偶尔跳出来，用一个理论视角重新审视你的材料。",
        5: "经验是宝库——但偶尔的抽象思考能帮你看到更大的图景。不妨尝试用一个中层理论来组织你的发现。",
    },
    "methodological_rigidity": {
        1: "你对方法的严谨令人敬佩——但也请记住，田野中最精彩的发现往往来自「不规范」的瞬间。",
        2: "方法规范是你的好习惯——在严格遵守的同时，保持对意外发现的敏感。",
        4: "你的灵活应变是田野中的优势——不过也别忘了在关键节点做好记录，以便回溯和论证。",
        5: "灵活性是你的超能力——但偶尔的方法论反思能让你的发现更具说服力。",
    },
    "analysis_depth": {
        1: "你善于广泛覆盖——下次分析时，试试锁定一个最让你困惑的发现，深入挖掘。",
        2: "广覆盖是你的优势——同时也选1-2个核心主题做更深入的剖析。",
        4: "深度分析是你的强项——不过也要记得勾勒整体图景，让读者不迷失在细节中。",
        5: "你擅长深挖——尝试用一句话概括你的核心发现，帮助读者把握整体方向。",
    },
    "structure_preference": {
        1: "结构化让你安心——但偶尔的开放式追问可能带来意想不到的收获。",
        2: "你有清晰的结构感——在访谈末尾留5分钟自由交谈，可能会有惊喜。",
        4: "你偏爱开放式探索——在某些关键问答上准备追问策略，能提升材料的可比性。",
        5: "开放带来了丰富性——分析阶段的编码框架能帮你从丰富材料中理出主线。",
    },
    "participation_level": {
        1: "保持距离有助于客观观察——但也可能错过只有参与其中才能理解的内在逻辑。",
        2: "你的观察立场清晰——偶尔尝试换位思考，从被研究者的视角看问题。",
        4: "你善于参与和共情——记得定期退后一步，用分析性的眼光审视你的观察。",
        5: "深度参与让你接近真相——但也容易产生「本土化盲区」。找个外部视角定期反馈。",
    },
    "tech_dependency": {
        1: "低技术方法让你更贴近研究对象——但也可能错过一些效率提升的机会。试试用一款简单的录音转写工具？",
        2: "你对技术保持审慎——关键环节使用技术辅助能帮你节省大量机械劳动。",
        4: "你善于利用技术——但也别忘了有些洞察只能在面对面、无屏幕干扰的时刻产生。",
        5: "技术是你的加速器——但也要为那些不能数字化的「沉默知识」留出空间。",
    },
    "writing_style": {
        1: "学术写作的严谨值得称道——如果目标读者是大众，试试用故事开头代替定义开头。",
        2: "你写得很规范——偶尔用一个生动的案例或引语来点亮你的分析。",
        4: "你的文字很亲和——在关键论点上增加学术引用能增强说服力。",
        5: "通俗表达让更多人理解你的研究——保留一个「学术版摘要」给专业读者。",
    },
    "learning_preference": {
        1: "你喜欢清晰的示范——试试在某一个环节脱离模板，按自己的想法尝试，看看会发生什么。",
        2: "示范是你的安全网——在有信心的环节尝试独立探索。",
        4: "你享受自主探索——但也别拒绝向有经验的研究者请教，他们能帮你少走弯路。",
        5: "独立探索是你的风格——偶尔的同行交流和示范参考也能带来新的启发。",
    },
}


def _generate_spectrum_tips(spectrum_values: dict, limit: int = 3) -> list[dict]:
    """Generate personalized methodology tips based on spectrum deviations."""
    tips = []
    for dim_id, (left, right) in SPECTRUM_LABELS.items():
        score = spectrum_values.get(dim_id, 3)
        if not isinstance(score, int) or score < 1 or score > 5:
            score = 3
        if score == 3:
            continue
        tip = SPECTRUM_TIPS.get(dim_id, {}).get(score, "")
        if tip:
            tips.append({
                "dimension": dim_id,
                "score": score,
                "left_label": left,
                "right_label": right,
                "tip": tip,
            })
    tips.sort(key=lambda t: abs(t["score"] - 3), reverse=True)
    return tips[:limit]


def _get_next_step(project: dict | None, phase: str) -> dict:
    """Recommend next action based on project phase."""
    steps = {
        "pre_survey": {"action": "设计问卷", "to": "/questionnaire", "icon": "📝",
                       "desc": "你的项目还在准备阶段，接下来可以开始设计调查问卷"},
        "during_survey": {"action": "开始田野", "to": "/fieldwork", "icon": "🎙",
                          "desc": "项目正在进行中，打开田野工具开始记录访谈"},
        "post_survey": {"action": "分析数据", "to": "/analysis", "icon": "📊",
                        "desc": "数据收集完成，开始系统分析你的发现"},
        "completed": {"action": "导出成果", "to": "/export", "icon": "📄",
                      "desc": "项目已完成，将分析结果导出为报告或论文"},
    }
    if project:
        return steps.get(phase, steps["pre_survey"])
    return {"action": "新建项目", "to": "/topic", "icon": "🔍",
            "desc": "还没有项目？从选题设计开始你的第一个调查"}


# ── Endpoint ────────────────────────────────────────────────────────

@router.get("")
async def get_dashboard(
    profile: UserProfile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate dashboard data: profile, project overview, sessions, tips, tokens."""
    profile_id = profile.id

    spectrum = {dim: getattr(profile, dim, 3) for dim in SPECTRUM_LABELS}

    # Latest project
    proj_result = await db.execute(
        select(SurveyProject)
        .where(SurveyProject.profile_id == profile_id)
        .order_by(SurveyProject.updated_at.desc())
        .limit(1)
    )
    latest_project = proj_result.scalar_one_or_none()

    project_data = None
    if latest_project:
        sess_count = await db.execute(
            select(func.count(SurveySession.id))
            .where(SurveySession.project_id == latest_project.id)
        )
        analysis_count = await db.execute(
            select(func.count(AnalysisResult.id))
            .where(AnalysisResult.project_id == latest_project.id)
        )
        project_data = {
            "id": latest_project.id,
            "title": latest_project.title,
            "research_direction": latest_project.research_direction,
            "paradigm": latest_project.paradigm,
            "phase": latest_project.phase,
            "status": latest_project.status,
            "session_count": sess_count.scalar() or 0,
            "analysis_count": analysis_count.scalar() or 0,
        }

    # All projects count
    all_proj_result = await db.execute(
        select(func.count(SurveyProject.id))
        .where(SurveyProject.profile_id == profile_id)
    )
    total_projects = all_proj_result.scalar() or 0

    # Spectrum tips
    tips = _generate_spectrum_tips(spectrum)

    # Token usage (7 days)
    token_summary = get_usage_summary(hours=168)

    # Mode workflow
    theme = profile.theme_preference or "academic"
    workflow_data = get_mode_workflow(theme)

    # Next step
    next_step = _get_next_step(project_data, latest_project.phase if latest_project else "pre_survey")

    return {
        "needs_setup": False,
        "profile": {
            "id": profile.id,
            "role": profile.role,
            "experience_level": profile.experience_level,
            "paradigm_preference": profile.paradigm_preference,
            "theme_preference": theme,
            "spectrum": spectrum,
            "spectrum_summary": build_spectrum_prompt(spectrum),
        },
        "project": project_data,
        "total_projects": total_projects,
        "tips": tips,
        "token_usage": {
            "calls_7d": token_summary["total_calls"],
            "tokens_7d": token_summary["total_tokens"],
            "cost_7d": token_summary["estimated_cost_cny"],
        },
        "workflow": {
            "name": workflow_data["name"],
            "stages": workflow_data["stages"],
            "recommended_tools": workflow_data["recommended_tools"],
        },
        "next_step": next_step,
    }
