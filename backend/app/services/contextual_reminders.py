
"""
B.4 ContextualReminders Service.
Keyword-based triggering + template rendering for in-interview guidance.
Looks up ReferenceCard matches against trigger keywords, ranks by relevance,
returns top-3 reminders with rendered prompt templates.
"""
import logging
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge_card import ReferenceCard, SkillsCluster, TriggerKeyword

logger = logging.getLogger(__name__)


async def get_reminders(
    db: AsyncSession,
    context_text: str,
    mode: str = "deep_one_on_one",
    top_n: int = 3,
) -> list[dict]:
    """Main API: given interview context text, return ranked reminders."""
    if not context_text or len(context_text) < 5:
        return []

    # 1. Find matching trigger keywords
    triggers = await _match_triggers(db, context_text)
    if not triggers:
        return []

    # 2. Find knowledge cards matching the triggered clusters
    cluster_ids = list(set(t["cluster_id"] for t in triggers))
    cards = await _get_cards_for_clusters(db, cluster_ids)
    if not cards:
        return []

    # 3. Score and rank cards by keyword overlap with context
    scored = _score_cards(cards, context_text, triggers)

    # 4. Render prompt templates for top-N
    reminders = []
    for card, score in scored[:top_n]:
        cluster = await _get_cluster(db, triggers[0]["cluster_id"])
        template = cluster.prompt_template if cluster else "{core_concepts}"
        reminder_text = _render_template(template, card, context_text)
        reminders.append({
            "card_id": card.id,
            "source_slug": card.source_slug,
            "confidence": card.confidence,
            "relevance_score": round(score, 2),
            "cluster_id": triggers[0]["cluster_id"],
            "cluster_name": cluster.name if cluster else "",
            "reminder_text": reminder_text,
            "keywords_matched": _matched_keywords(card, context_text),
            "core_concepts": card.core_concepts[:3] if isinstance(card.core_concepts, list) else [],
        })

    return reminders


async def _match_triggers(db: AsyncSession, context: str) -> list[dict]:
    """Find which trigger keywords appear in the context text."""
    result = await db.execute(select(TriggerKeyword))
    all_triggers = result.scalars().all()

    matched = []
    ctx_lower = context.lower()
    for t in all_triggers:
        if t.keyword.lower() in ctx_lower:
            matched.append({
                "keyword": t.keyword,
                "cluster_id": t.cluster_id,
                "sub_module_id": t.sub_module_id,
                "weight": t.weight,
            })
    return sorted(matched, key=lambda x: x["weight"], reverse=True)


async def _get_cards_for_clusters(db: AsyncSession, cluster_ids: list[str]):
    """Get all knowledge cards assigned to these clusters."""
    cards = []
    result = await db.execute(
        select(ReferenceCard).where(ReferenceCard.confidence >= 3)
    )
    for card in result.scalars().all():
        card_clusters = set(card.clusters.split(",")) if card.clusters else set()
        if card_clusters & set(cluster_ids):
            cards.append(card)
    return cards


def _score_cards(cards, context: str, triggers: list[dict]) -> list[tuple]:
    """Score cards by keyword overlap with context. Returns sorted (card, score) pairs."""
    ctx_lower = context.lower()
    scored = []
    for card in cards:
        score = 0.0
        if card.search_text:
            for word in card.search_text.split():
                if len(word) >= 2 and word.lower() in ctx_lower:
                    score += 1.0
        # Boost by confidence
        score *= (card.confidence / 3.0)
        # Boost by cluster trigger weight
        for t in triggers:
            card_clusters = set(card.clusters.split(",")) if card.clusters else set()
            if t["cluster_id"] in card_clusters:
                score += t["weight"]
        if score > 0:
            scored.append((card, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)


def _matched_keywords(card, context: str) -> list[str]:
    """Return which keywords from the card match the context."""
    ctx_lower = context.lower()
    matched = []
    kws = card.keywords if isinstance(card.keywords, list) else []
    for kw in kws:
        if isinstance(kw, str) and len(kw) >= 2 and kw.lower() in ctx_lower:
            matched.append(kw)
    return matched[:10]


async def _get_cluster(db: AsyncSession, cluster_id: str):
    result = await db.execute(
        select(SkillsCluster).where(SkillsCluster.cluster_id == cluster_id)
    )
    return result.scalar_one_or_none()


def _render_template(template: str, card, context: str) -> str:
    """Render a prompt template with card data."""
    concepts = card.core_concepts if isinstance(card.core_concepts, list) else []
    guidelines = card.practical_guidelines if isinstance(card.practical_guidelines, list) else []
    ethics = card.ethical_notes if isinstance(card.ethical_notes, list) else []
    cultural = card.cultural_knowledge if isinstance(card.cultural_knowledge, list) else []
    cases = card.case_studies if isinstance(card.case_studies, list) else []

    # Truncate to avoid prompt bloat
    concepts_str = "; ".join(c[:80] if isinstance(c, str) else str(c)[:80] for c in concepts[:2])
    guidelines_str = "; ".join(g[:100] if isinstance(g, str) else str(g)[:100] for g in guidelines[:2])
    ethics_str = "; ".join(e[:80] if isinstance(e, str) else str(e)[:80] for e in ethics[:1])
    cultural_str = "; ".join(cu[:80] if isinstance(cu, str) else str(cu)[:80] for cu in cultural[:1])
    cases_str = "; ".join(cs[:60] if isinstance(cs, str) else str(cs)[:60] for cs in cases[:1])

    return (
        template
        .replace("{trigger_topic}", context[:100])
        .replace("{region_context}", cultural_str or "无特定地域信息")
        .replace("{cultural_note}", cultural_str or "注意文化敏感性")
        .replace("{core_concepts}", concepts_str or "相关概念")
        .replace("{source_slug}", card.source_slug)
        .replace("{practical_guidelines}", guidelines_str or "参考方法论最佳实践")
        .replace("{ethical_notes}", ethics_str or "遵循研究伦理准则")
        .replace("{interview_mode}", "深度访谈")
        .replace("{concept_keywords}", ", ".join(card.keywords[:5] if isinstance(card.keywords, list) else []))
        .replace("{coding_dimension}", concepts_str[:60])
        .replace("{case_studies}", cases_str or "参考经典案例")
    )
