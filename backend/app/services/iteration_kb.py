"""Iteration Knowledge Base — query, seed, and analyze development retrospectives.

Usage:
  from app.services.iteration_kb import seed_dashscope_debugging, search_similar_failures
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iteration import CasePoint, FailurePoint, Implication, IterationRecord, MicroInnovation

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Seed Data: DashScope Transcription Debugging (2026-06-03 ~ 06-04)
# ═══════════════════════════════════════════════════════════════════════════

DASHSCOPE_DEBUG_SEED = {
    "iteration": {
        "title": "DashScope 文件转录 Bug 修复（FileTrans + WebSocket 双路径调试）",
        "phase": "debugging",
        "version": "v0.2.1",
        "summary": (
            "修复田野调查模块的文件转录功能。尝试了 FileTrans REST API（需HTTPS URL）和 "
            "Paraformer WebSocket Realtime API（需 gummy-realtime-v1 权限）两条路径。"
            "最终因 API Key 权限不足和 ICP 备案期间的 HTTPS 不可用，转录功能暂时阻塞。"
        ),
        "context_before": (
            "田野调查模块的文件上传→转录功能报 400 Bad Request。"
            "DashScope FileTrans API 要求音频文件 URL 必须是 HTTPS，但服务器仅有 HTTP（ICP备案中）。"
        ),
        "context_after": (
            "已确认两条技术路径均可行但需要外部条件："
            "1) FileTrans: 需要 ICP 备案通过后的 HTTPS 域名或 Cloudflare Tunnel；"
            "2) WebSocket Realtime: 需要申请 gummy-realtime-v1 模型权限。"
            "Docker 镜像已安装 dashscope SDK 1.25.20，待外部条件满足后即可使用。"
        ),
        "lessons_learned": (
            "1) API 权限边界是纯代码无法解决的硬边界——需要在调试初期主动验证 API Key 权限；"
            "2) Docker 中 .env 覆盖 config.py 默认值，docker compose restart 不重读 env_file；"
            "3) 混合协议栈（HTTP/HTTPS/WS）下，对第三方 API 的要求必须在架构设计阶段考虑；"
            "4) websockets 库版本漂移（14.x 的 extra_headers→additional_headers）是沉默的杀手。"
        ),
        "tags": "dashscope,asr,transcription,websocket,docker,icp,api-permission",
    },
    "failure_points": [
        {
            "symptom": "FileTrans API 返回 400 Bad Request",
            "root_cause": (
                "DashScope FileTrans 的 file_urls 参数要求 HTTPS 公网可访问 URL。"
                "当前服务器使用 HTTP + 自签名 HTTPS 证书，DashScope 拒绝下载文件。"
                "ICP 备案期间域名 configured-domain.invalid DNS 被暂停，无法使用 Let's Encrypt 等 CA 证书。"
            ),
            "fix": (
                "短期方案（任选一）："
                "A) Cloudflare Tunnel / ngrok / frp 创建 HTTPS 隧道 → FileTrans；"
                "B) DashScope SDK Recognition 类（WebSocket 直传，不依赖 URL）；"
                "C) 等待 ICP 通过后 Let's Encrypt HTTPS。"
                "长期：ICP 后 public_base_url 改为 https://configured-domain.invalid"
            ),
            "prevention": (
                "架构设计阶段检查所有第三方 API 对协议（HTTP/HTTPS）的要求。"
                "为 FileTrans 增加本地文件上传模式（Base64 编码内联提交）。"
            ),
            "severity": "critical",
        },
        {
            "symptom": "websockets.connect() 报错: unexpected keyword argument 'extra_headers'",
            "root_cause": (
                "websockets Python 库 13.x → 14.x 升级：connect() 的 extra_headers 参数"
                "重命名为 additional_headers。Docker 容器重建时安装了最新版（14.1），与源码不兼容。"
            ),
            "fix": (
                "将 asr_qwen.py 中 relay() 和 transcribe_file() 两处"
                "websockets.connect() 的 extra_headers 改为 additional_headers。"
            ),
            "prevention": (
                "requirements.txt 中固定关键依赖版本（如 websockets==13.0）。"
                "Dockerfile 中增加依赖版本锁定步骤。"
            ),
            "severity": "high",
        },
        {
            "symptom": "WebSocket 连接成功但发送任意消息后返回 1007 'Model not found'",
            "root_cause": (
                "DashScope Realtime API (/api-ws/v1/realtime) 使用 OpenAI Realtime API 协议。"
                "URL 参数 ?model=paraformer-realtime-v2 自动创建 session（session.created 事件）。"
                "但 session 中的 input_audio_transcription.model 是 gummy-realtime-v1，"
                "这是一个独立的转录模型，需要额外 API 权限。我们的 Key 没有该权限。"
            ),
            "fix": (
                "安装 dashscope SDK 1.25.20，其 Recognition 类可能使用不同内部端点。"
                "如 SDK 也不支持，需联系阿里云申请 gummy-realtime-v1 权限。"
            ),
            "prevention": (
                "集成第三方 API 前，先在隔离环境测试完整协议流程。"
                "优先使用官方 SDK 而非裸 WebSocket。"
                "记录 API Key 权限清单作为项目知识资产。"
            ),
            "severity": "critical",
        },
        {
            "symptom": "docker compose restart 后 .env 修改不生效",
            "root_cause": (
                "docker compose restart 仅重启容器进程，不重新读取 env_file。"
                "需要 docker compose up -d 才能重新创建容器并读取最新 .env。"
                ".env 中 QWEN_ASR_MODEL=qwen3-asr-flash-realtime 覆盖了 config.py 默认值。"
            ),
            "fix": (
                "1) 修改 .env 中 QWEN_ASR_MODEL=paraformer-realtime-v2"
                "2) docker compose up -d（非 restart）"
                "3) 验证：docker compose exec backend env | grep QWEN"
            ),
            "prevention": (
                "部署文档标注：修改 .env 后必须 up -d 而非 restart。"
                "config.py 启动时打印所有关键配置值。"
            ),
            "severity": "medium",
        },
        {
            "symptom": "Docker 镜像构建失败: apt-get install ffmpeg 超时/404",
            "root_cause": (
                "Dockerfile 使用 deb.debian.org 官方源。阿里云 ECS（中国境内）连接 Debian 官方源"
                "速度极慢或超时。需要替换为阿里云镜像源。"
            ),
            "fix": (
                "Dockerfile 中 apt-get update 之前增加："
                "sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources"
            ),
            "prevention": (
                "为中国 ECS 部署创建专用 Dockerfile 或 build args。"
                "维护已验证可用的镜像源列表。"
            ),
            "severity": "medium",
        },
    ],
    "case_points": [
        {
            "category": "docker",
            "pattern": "Docker .env 配置更新 → 必须用 up -d 而非 restart",
            "example": (
                "# 错误（修改 .env 后）：\n"
                "docker compose restart\n\n"
                "# 正确：\n"
                "vim .env\n"
                "docker compose up -d\n"
                "docker compose exec backend env | grep KEY"
            ),
        },
        {
            "category": "api",
            "pattern": "websockets 14.x 的 connect() 使用 additional_headers 而非 extra_headers",
            "example": (
                "# websockets >= 14.0:\n"
                "async with websockets.connect(\n"
                "    url,\n"
                "    additional_headers={\"Authorization\": f\"Bearer {key}\"},\n"
                ") as ws:"
            ),
        },
        {
            "category": "config",
            "pattern": "Pydantic Settings .env 覆盖优先级高于源码默认值",
            "example": (
                "# config.py: qwen_asr_model: str = \"paraformer-realtime-v2\"\n"
                "# .env:      QWEN_ASR_MODEL=qwen3-asr-flash-realtime\n"
                "# 运行时实际值: qwen3-asr-flash-realtime ← 易忽略的陷阱！\n"
                "# 建议：启动时打印所有配置值。"
            ),
        },
        {
            "category": "protocol",
            "pattern": "DashScope Realtime API 使用 OpenAI Realtime 协议，非旧版二进制 PCM",
            "example": (
                "# DashScope /api-ws/v1/realtime：\n"
                "# URL ?model=paraformer-realtime-v2 → 自动创建 session\n"
                "# 音频通过 JSON 消息发送（base64）：\n"
                '{"type": "input_audio_buffer.append", "audio": "<base64>"}\n'
                '{"type": "input_audio_buffer.commit"}\n'
                '{"type": "response.create"}\n'
                "# 输出转录模型 gummy-realtime-v1 需独立权限"
            ),
        },
        {
            "category": "docker",
            "pattern": "中国 ECS Docker 构建 → 替换 Debian 源为阿里云镜像",
            "example": (
                "RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' "
                "/etc/apt/sources.list.d/debian.sources && \\\n"
                "    apt-get update && apt-get install -y ffmpeg"
            ),
        },
    ],
    "micro_innovations": [
        {
            "name": "WebSocket 协议自动发现",
            "description": (
                "通过等待 session.created 事件并解析 session 配置，"
                "自动发现 API 使用的实际协议版本和模型，而非硬编码协议假设。"
                "asr_qwen.py 的 transcribe_file() 已实现此模式。"
            ),
            "impact_score": 4.0,
            "status": "adopted",
        },
        {
            "name": "双路径文件转录（FileTrans + WebSocket fallback）",
            "description": (
                "router_fieldwork.py 中实现：先尝试 FileTrans REST API（需要 HTTPS URL），"
                "失败时自动回退到 WebSocket 流式转录。fallback 架构正确——"
                "当任一条件满足时即可工作。"
            ),
            "impact_score": 3.5,
            "status": "adopted",
        },
    ],
    "implications": [
        {
            "source_type": "iteration",
            "implication": (
                "API 权限验证应作为第三方服务集成的第一步（而非协议调试），"
                "可节省大量无效调试时间。建议建立 API Key 权限清单文档。"
            ),
            "actionable": (
                "创建 docs/API_PERMISSIONS.md，记录所有第三方 API Key 的权限范围、"
                "已测试的能力、已知限制。每次新增 API 或更换 Key 时更新。"
            ),
            "priority": "high",
        },
        {
            "source_type": "iteration",
            "implication": (
                "Docker 配置管理存在多个静默覆盖点（.env > config.py 默认值，"
                "up -d > restart），需要建立配置变更的检查清单。"
            ),
            "actionable": (
                "创建 docs/DEPLOYMENT_CHECKLIST.md，包含：修改 .env 后的验证步骤、"
                "Docker 重建后的环境变量检查、关键 API 端点的 smoke test。"
            ),
            "priority": "high",
        },
    ],
}


async def seed_dashscope_debugging(db: AsyncSession) -> int:
    """Seed the iteration knowledge base with the DashScope debugging session.

    Returns the iteration_id of the created record.
    Idempotent: skips if an iteration with the same title already exists.
    """
    title = DASHSCOPE_DEBUG_SEED["iteration"]["title"]

    existing = await db.execute(
        select(IterationRecord).where(IterationRecord.title == title)
    )
    if existing.scalar_one_or_none():
        logger.info("DashScope debugging seed already exists, skipping")
        return 0

    it = DASHSCOPE_DEBUG_SEED["iteration"]
    record = IterationRecord(
        title=it["title"],
        phase=it["phase"],
        version=it["version"],
        summary=it["summary"],
        context_before=it["context_before"],
        context_after=it["context_after"],
        lessons_learned=it["lessons_learned"],
        tags=it["tags"],
    )
    db.add(record)
    await db.flush()

    for fp in DASHSCOPE_DEBUG_SEED["failure_points"]:
        db.add(FailurePoint(
            iteration_id=record.id,
            symptom=fp["symptom"],
            root_cause=fp["root_cause"],
            fix=fp["fix"],
            prevention=fp["prevention"],
            severity=fp["severity"],
        ))

    for cp in DASHSCOPE_DEBUG_SEED["case_points"]:
        db.add(CasePoint(
            iteration_id=record.id,
            category=cp["category"],
            pattern=cp["pattern"],
            example=cp["example"],
        ))

    for mi in DASHSCOPE_DEBUG_SEED["micro_innovations"]:
        db.add(MicroInnovation(
            iteration_id=record.id,
            name=mi["name"],
            description=mi["description"],
            impact_score=mi["impact_score"],
            status=mi["status"],
        ))

    for impl in DASHSCOPE_DEBUG_SEED["implications"]:
        db.add(Implication(
            source_type=impl["source_type"],
            source_id=record.id,
            implication=impl["implication"],
            actionable=impl["actionable"],
            priority=impl["priority"],
        ))

    await db.commit()
    logger.info(
        f"Seeded DashScope debugging iteration (id={record.id}): "
        f"{len(DASHSCOPE_DEBUG_SEED['failure_points'])} failures, "
        f"{len(DASHSCOPE_DEBUG_SEED['case_points'])} case points, "
        f"{len(DASHSCOPE_DEBUG_SEED['micro_innovations'])} innovations, "
        f"{len(DASHSCOPE_DEBUG_SEED['implications'])} implications"
    )
    return record.id


async def search_similar_failures(db: AsyncSession, query: str, limit: int = 5) -> list[dict]:
    """Simple keyword search across failure points. Returns top matches."""
    words = query.split()
    results = []
    for word in words[:5]:
        pattern = f"%{word}%"
        rows = await db.execute(
            select(FailurePoint).where(
                (FailurePoint.symptom.ilike(pattern)) |
                (FailurePoint.root_cause.ilike(pattern)) |
                (FailurePoint.fix.ilike(pattern))
            ).limit(limit)
        )
        for fp in rows.scalars().all():
            results.append({
                "id": fp.id,
                "symptom": fp.symptom[:200],
                "root_cause": fp.root_cause[:200],
                "fix": fp.fix[:200],
                "severity": fp.severity,
            })
    return results[:limit]


async def get_recent_case_points(db: AsyncSession, category: str = "", limit: int = 10) -> list[dict]:
    """Retrieve reusable case points, optionally filtered by category."""
    q = select(CasePoint).order_by(CasePoint.reuse_count.desc())
    if category:
        q = q.where(CasePoint.category == category)
    rows = await db.execute(q.limit(limit))
    return [
        {"id": cp.id, "category": cp.category, "pattern": cp.pattern,
         "example": cp.example, "reuse_count": cp.reuse_count}
        for cp in rows.scalars().all()
    ]


async def get_pending_implications(db: AsyncSession) -> list[dict]:
    """Get high-priority implications that haven't been actioned."""
    rows = await db.execute(
        select(Implication)
        .where(Implication.priority.in_(["high", "critical"]))
        .order_by(Implication.priority.desc())
    )
    return [
        {"id": i.id, "implication": i.implication,
         "actionable": i.actionable, "priority": i.priority}
        for i in rows.scalars().all()
    ]
