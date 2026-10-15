from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.models.base import Base
from app.models import iteration  # noqa: F401 — ensure iteration KB tables created
from app.models import knowledge_card  # noqa: F401 — M.4 knowledge cards + skills clusters
from app.models import survey  # noqa: F401 — ensure all survey models loaded (incl. ScenarioDesign)
from app.models import user  # noqa: F401 — ensure UserAccount table created
from app.models import analytics  # noqa: F401 — analytics events table

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — create tables
    from app.core.database import async_session_factory, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add columns that may not exist in existing databases (lightweight migration)
        migrations = [
            "ALTER TABLE user_profiles ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'academic'",
            "ALTER TABLE user_profiles ADD COLUMN user_id INTEGER REFERENCES user_accounts(id)",
            # ── Researcher Community (v0.5.0) ──
            "ALTER TABLE user_skills ADD COLUMN published_at TIMESTAMP",
            "ALTER TABLE user_skills ADD COLUMN published_version VARCHAR(20) DEFAULT '1.0.0'",
            "ALTER TABLE user_skills ADD COLUMN fork_count INTEGER DEFAULT 0",
            "ALTER TABLE user_skills ADD COLUMN rating_avg REAL DEFAULT 0.0",
            "ALTER TABLE user_skills ADD COLUMN rating_count INTEGER DEFAULT 0",
            "ALTER TABLE user_skills ADD COLUMN download_count INTEGER DEFAULT 0",
            "ALTER TABLE user_skills ADD COLUMN readme TEXT",
            "ALTER TABLE user_skills ADD COLUMN example_input TEXT",
            "ALTER TABLE user_skills ADD COLUMN example_output TEXT",
            "ALTER TABLE user_skills ADD COLUMN compatible_models VARCHAR(200) DEFAULT '[]'",
            "ALTER TABLE user_skills ADD COLUMN min_app_version VARCHAR(20) DEFAULT '0.2.0'",
            "ALTER TABLE user_skills ADD COLUMN forked_from_id INTEGER",
            "ALTER TABLE user_skills ADD COLUMN fork_lineage VARCHAR(500) DEFAULT '[]'",
        ]
        for stmt in migrations:
            try:
                await conn.execute(text(stmt))
            except Exception:
                logger.debug("Migration skipped (column likely exists): %s", stmt[:80])

    # Seed iteration knowledge base (idempotent)
    try:
        from app.services.iteration_kb import seed_dashscope_debugging
        async with async_session_factory() as db:
            await seed_dashscope_debugging(db)
    except Exception:
        logger.warning(
            "Failed to seed iteration KB (this is non-fatal)", exc_info=True
        )

    # Seed knowledge cards + skills clusters on startup (idempotent)
    try:
        from app.services.knowledge_ingestion import ingest_all as seed_knowledge
        async with async_session_factory() as db:
            result = await seed_knowledge(db)
            logger.info("Knowledge cards seeded: %s", result)
    except Exception:
        logger.warning(
            "Failed to seed knowledge cards (non-fatal)", exc_info=True
        )

    yield
    # Shutdown
    await engine.dispose()
