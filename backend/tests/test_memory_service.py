"""Unit tests for MemoryService — extract, save, retrieve, inject, delete."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.memory_service import MemoryService
from app.models.survey import UserMemory


class TestMemoryExtraction:
    """Test the extract_from_dialogue() method."""

    @pytest.mark.asyncio
    async def test_extract_parses_valid_json_response(self):
        ai = AsyncMock()
        ai.chat.return_value = json.dumps({
            "memories": [
                {
                    "category": "preference",
                    "key": "favoured_paradigm",
                    "value": "用户偏好质性研究方法",
                    "confidence": 0.9,
                    "importance": 5,
                },
            ],
        })

        memories = await MemoryService.extract_from_dialogue(
            ai,
            user_message="我喜欢用深度访谈做研究",
            assistant_reply="明白，你是质性研究方向的学者",
        )

        assert len(memories) == 1
        assert memories[0]["category"] == "preference"
        assert memories[0]["key"] == "favoured_paradigm"

    @pytest.mark.asyncio
    async def test_extract_handles_empty_dialogue(self):
        ai = AsyncMock()
        result = await MemoryService.extract_from_dialogue(ai, "", "")
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_sets_defaults_for_missing_fields(self):
        ai = AsyncMock()
        ai.chat.return_value = json.dumps({
            "memories": [
                {"category": "note", "key": "test_key", "value": "some value"},
            ],
        })

        memories = await MemoryService.extract_from_dialogue(ai, "hello", "world")

        m = memories[0]
        assert m["confidence"] == 0.5  # default
        assert m["importance"] == 3     # default

    @pytest.mark.asyncio
    async def test_extract_handles_malformed_json(self):
        ai = AsyncMock()
        ai.chat.return_value = "not valid json at all"

        result = await MemoryService.extract_from_dialogue(ai, "hello", "world")
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_filters_incomplete_memories(self):
        ai = AsyncMock()
        ai.chat.return_value = json.dumps({
            "memories": [
                {"category": "preference"},  # missing key and value — filtered out
                {"category": "preference", "key": "good", "value": "complete"},
            ],
        })

        memories = await MemoryService.extract_from_dialogue(ai, "hello", "world")
        assert len(memories) == 1  # only the complete one
        assert memories[0]["key"] == "good"

    @pytest.mark.asyncio
    async def test_extract_includes_profile_summary(self):
        ai = AsyncMock()
        ai.chat.return_value = json.dumps({"memories": []})

        profile = {
            "role": "undergraduate", "experience_level": "beginner",
            "paradigm_preference": "qualitative",
        }

        await MemoryService.extract_from_dialogue(
            ai, "hello", "world", profile_data=profile,
        )

        # Verify the profile summary was passed to the AI
        call_msg = ai.chat.call_args[0][0]
        user_content = call_msg[1]["content"]
        assert "本科生" in user_content
        assert "新手" in user_content
        assert "质性" in user_content


class TestMemoryPersistence:
    """Test save_memories() upsert logic with real in-memory SQLite."""

    @pytest.mark.asyncio
    async def test_save_inserts_new_memory(self, db_session):
        memories = [
            {"category": "preference", "key": "likes_qual",
             "value": "用户偏好质性方法", "confidence": 0.8, "importance": 4},
        ]
        count = await MemoryService.save_memories(db_session, profile_id=1, memories=memories)
        assert count == 1

        from sqlalchemy import select
        row = await db_session.execute(
            select(UserMemory).where(UserMemory.profile_id == 1)
        )
        mems = list(row.scalars().all())
        assert len(mems) == 1
        assert mems[0].key == "likes_qual"

    @pytest.mark.asyncio
    async def test_save_upserts_existing_memory(self, db_session):
        # Insert first time
        memories = [
            {"category": "preference", "key": "likes_qual",
             "value": "旧值", "confidence": 0.5, "importance": 3},
        ]
        await MemoryService.save_memories(db_session, profile_id=1, memories=memories)

        # Upsert — same category+key → update existing row
        memories2 = [
            {"category": "preference", "key": "likes_qual",
             "value": "新值", "confidence": 0.8, "importance": 5},
        ]
        await MemoryService.save_memories(db_session, profile_id=1, memories=memories2)

        from sqlalchemy import select
        row = await db_session.execute(
            select(UserMemory).where(UserMemory.profile_id == 1)
        )
        mems = list(row.scalars().all())
        assert len(mems) == 1  # still one row
        assert mems[0].value == "新值"
        # Confidence boosted by +0.1 on upsert
        assert mems[0].confidence == 0.9


class TestMemoryRetrieval:
    """Test get_relevant_memories() returns sorted by weighted score."""

    @pytest.mark.asyncio
    async def test_retrieve_sorts_by_weighted_score(self, db_session):
        db_session.add(UserMemory(
            profile_id=1, category="preference", key="high",
            value="high score", confidence=1.0, importance=5,
        ))
        db_session.add(UserMemory(
            profile_id=1, category="note", key="low",
            value="low score", confidence=0.5, importance=1,
        ))
        await db_session.commit()

        memories = await MemoryService.get_relevant_memories(db_session, profile_id=1)
        assert len(memories) == 2
        # High score should come first
        assert memories[0].key == "high"


class TestMemoryFormatting:
    """Test build_memory_context() for system-prompt injection."""

    def test_build_context_formats_memories_correctly(self):
        m = UserMemory(
            profile_id=1, category="preference", key="test",
            value="用户偏好深度访谈", confidence=0.9, importance=4,
        )
        result = MemoryService.build_memory_context([m])

        assert "用户偏好深度访谈" in result
        assert "★★★★" in result  # importance=4 → 4 stars

    def test_build_context_returns_empty_for_no_memories(self):
        assert MemoryService.build_memory_context([]) == ""


class TestMemoryCRUD:
    """Test delete, confirm, edit, suppress operations."""

    @pytest.mark.asyncio
    async def test_delete_existing_memory(self, db_session):
        m = UserMemory(profile_id=1, category="note", key="temp", value="x")
        db_session.add(m)
        await db_session.commit()

        ok = await MemoryService.delete_memory(db_session, memory_id=m.id, profile_id=1)
        assert ok is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, db_session):
        ok = await MemoryService.delete_memory(db_session, memory_id=99999, profile_id=1)
        assert ok is False

    @pytest.mark.asyncio
    async def test_confirm_boosts_confidence(self, db_session):
        m = UserMemory(profile_id=1, category="note", key="x", value="y", confidence=0.5)
        db_session.add(m)
        await db_session.commit()

        ok = await MemoryService.confirm_memory(db_session, memory_id=m.id, profile_id=1)
        assert ok is True
        assert m.confidence == 0.8  # boosted by +0.3, capped at 1.0

    @pytest.mark.asyncio
    async def test_suppress_sets_confidence_to_0_1(self, db_session):
        m = UserMemory(profile_id=1, category="note", key="x", value="y", confidence=0.8)
        db_session.add(m)
        await db_session.commit()

        ok = await MemoryService.suppress_memory(db_session, memory_id=m.id, profile_id=1)
        assert ok is True
        assert m.confidence == 0.1

    @pytest.mark.asyncio
    async def test_edit_memory_updates_fields(self, db_session):
        m = UserMemory(profile_id=1, category="old_cat", key="old_key", value="old_val")
        db_session.add(m)
        await db_session.commit()

        ok = await MemoryService.edit_memory(
            db_session, memory_id=m.id, profile_id=1,
            value="new_val", key="new_key",
        )
        assert ok is True
        assert m.value == "new_val"
        assert m.key == "new_key"
        assert m.category == "old_cat"  # unchanged
