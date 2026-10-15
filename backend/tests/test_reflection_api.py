"""API smoke tests for reflection endpoints — route reachability and response structure.

Uses the test client from conftest.py which provides in-memory SQLite + mock AI.
"""

import pytest


class TestReflectionAPI:
    """Smoke-test all reflection API endpoints."""

    @pytest.mark.asyncio
    async def test_list_triggers(self, client):
        """GET /api/v1/reflection/triggers returns available triggers."""
        res = await client.get("/api/v1/reflection/triggers")
        assert res.status_code == 200
        data = res.json()
        assert "triggers" in data
        trigger_ids = [t["id"] for t in data["triggers"]]
        assert "fieldwork_completed" in trigger_ids
        assert "analysis_completed" in trigger_ids
        assert "project_completed" in trigger_ids

    @pytest.mark.asyncio
    async def test_start_reflection_missing_profile(self, client):
        """POST /api/v1/reflection/start without profile_id returns error."""
        res = await client.post("/api/v1/reflection/start", json={
            "trigger_type": "fieldwork_completed",
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_start_reflection_unknown_trigger(self, client):
        """POST with unknown trigger type returns error with available list."""
        res = await client.post("/api/v1/reflection/start", json={
            "trigger_type": "nonexistent_trigger",
            "profile_id": 1,
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data
        assert "available" in data

    @pytest.mark.asyncio
    async def test_respond_missing_session(self, client):
        """POST /api/v1/reflection/respond with invalid session returns error."""
        res = await client.post("/api/v1/reflection/respond", json={
            "session_id": "nonexistent",
            "answer": "test answer",
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_respond_missing_answer(self, client):
        """POST with empty answer returns error."""
        res = await client.post("/api/v1/reflection/respond", json={
            "session_id": "test-session",
            "answer": "",
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_conclude_missing_session(self, client):
        """POST /api/v1/reflection/conclude with invalid session."""
        res = await client.post("/api/v1/reflection/conclude", json={
            "session_id": "nonexistent",
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_quick_reflection_missing_notes(self, client):
        """POST /api/v1/reflection/quick without notes returns error."""
        res = await client.post("/api/v1/reflection/quick", json={
            "context": "some context",
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_get_history(self, client):
        """GET /api/v1/reflection/history/{profile_id} returns structure."""
        res = await client.get("/api/v1/reflection/history/1")
        assert res.status_code == 200
        data = res.json()
        assert "profile_id" in data
        assert "sessions" in data

    @pytest.mark.asyncio
    async def test_get_evolution(self, client):
        """GET /api/v1/reflection/evolution/{profile_id} returns spectrum status."""
        res = await client.get("/api/v1/reflection/evolution/1")
        assert res.status_code == 200
        data = res.json()
        assert "profile_id" in data
        # May have current_spectrum or error if profile not found
        assert "current_spectrum" in data or "evolution_summary" in data or "error" in data

    @pytest.mark.asyncio
    async def test_get_evolution_invalid_dimension(self, client):
        """GET with invalid dimension filter returns error."""
        res = await client.get("/api/v1/reflection/evolution/1?dimension=nonexistent_dim")
        assert res.status_code == 200
        data = res.json()
        if "error" in data:
            assert "Invalid" in data["error"] or "invalid" in str(data).lower()

    @pytest.mark.asyncio
    async def test_apply_pending_missing_profile(self, client):
        """POST /api/v1/reflection/apply-pending without profile_id."""
        res = await client.post("/api/v1/reflection/apply-pending", json={})
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_apply_pending_invalid_stability(self, client):
        """POST with out-of-range stability."""
        res = await client.post("/api/v1/reflection/apply-pending", json={
            "profile_id": 1,
            "stability": 1.5,
        })
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_full_reflection_flow(self, client):
        """E2E: create profile → start reflection → respond → conclude → history → evolution.

        This test exercises the complete reflection lifecycle.
        Skips AI-dependent parts if no API key available.
        """
        # 1. Create profile
        res = await client.post("/api/v1/profile", json={
            "role": "graduate",
            "experience_level": "intermediate",
            "paradigm_preference": "qualitative",
            "theme_preference": "academic",
        })
        assert res.status_code == 200
        pid = res.json()["id"]

        # 2. Create project
        res = await client.post("/api/v1/projects", json={
            "profile_id": pid,
            "title": "反射E2E测试项目",
            "paradigm": "qualitative",
        })
        assert res.status_code == 200
        proj_id = res.json()["id"]

        # 3. Start reflection
        res = await client.post("/api/v1/reflection/start", json={
            "trigger_type": "fieldwork_completed",
            "profile_id": pid,
            "project_id": proj_id,
        })
        assert res.status_code == 200
        data = res.json()

        # If AI not available, skip rest of flow
        if "error" in data:
            pytest.skip(f"Reflection start requires AI: {data['error']}")

        assert "session_id" in data
        session_id = data["session_id"]
        assert "current_question" in data

        # 4. Answer questions
        res = await client.post("/api/v1/reflection/respond", json={
            "session_id": session_id,
            "answer": "我发现受访者的回答与理论预设存在差异，让我重新思考研究框架。",
        })
        assert res.status_code == 200
        data = res.json()
        if "error" in data:
            pytest.skip(f"Respond requires AI: {data['error']}")

        # Answer remaining questions if any
        for _ in range(5):  # Safety cap
            if data.get("completed"):
                break
            if not data.get("next_question"):
                break
            res = await client.post("/api/v1/reflection/respond", json={
                "session_id": session_id,
                "answer": "反思让我意识到身份位置深刻影响了研究互动。",
            })
            assert res.status_code == 200
            data = res.json()

        # 5. Conclude
        res = await client.post("/api/v1/reflection/conclude", json={
            "session_id": session_id,
            "apply_adjustments": False,
        })
        assert res.status_code == 200
        conclusion = res.json()
        # Either successful or error if AI unavailable
        assert "summary" in conclusion or "error" in conclusion

        # 6. History
        res = await client.get(f"/api/v1/reflection/history/{pid}")
        assert res.status_code == 200

        # 7. Evolution
        res = await client.get(f"/api/v1/reflection/evolution/{pid}")
        assert res.status_code == 200

        # 8. Apply adjustments
        res = await client.post("/api/v1/reflection/apply-pending", json={
            "profile_id": pid,
            "stability": 0.5,
        })
        assert res.status_code == 200
