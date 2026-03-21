"""Unit tests for the Chores API endpoints."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

from src.services.chores.service import ChoresService

# =============================================================================
# Helpers
# =============================================================================


async def _insert_chore(
    db: aiosqlite.Connection,
    *,
    project_id: str = "PVT_1",
    name: str = "Bug Bash",
    template_path: str = ".github/ISSUE_TEMPLATE/bug-bash.md",
    template_content: str = "---\nname: Bug Bash\n---\nRun bug bash",
    status: str = "active",
    schedule_type: str | None = None,
    schedule_value: int | None = None,
    chore_id: str | None = None,
) -> str:
    """Insert a chore directly into the DB for test setup. Returns chore_id."""
    cid = chore_id or str(uuid.uuid4())
    await db.execute(
        """
        INSERT INTO chores (
            id, project_id, name, template_path, template_content,
            status, schedule_type, schedule_value,
            last_triggered_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0,
                  strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
                  strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        """,
        (
            cid,
            project_id,
            name,
            template_path,
            template_content,
            status,
            schedule_type,
            schedule_value,
        ),
    )
    await db.commit()
    return cid


# =============================================================================
# GET /chores/{project_id}
# =============================================================================


class TestListChores:
    """Tests for the list chores endpoint."""

    @pytest.mark.anyio
    async def test_empty_list(self, client, mock_db):
        """GET with no chores returns an empty array."""
        resp = await client.get("/api/v1/chores/PVT_1")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.anyio
    async def test_returns_chores_for_project(self, client, mock_db):
        """GET returns only chores belonging to the requested project."""
        await _insert_chore(mock_db, project_id="PVT_1", name="Chore A")
        await _insert_chore(mock_db, project_id="PVT_1", name="Chore B")
        await _insert_chore(mock_db, project_id="PVT_2", name="Other Project Chore")

        resp = await client.get("/api/v1/chores/PVT_1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = {c["name"] for c in data}
        assert names == {"Chore A", "Chore B"}

    @pytest.mark.anyio
    async def test_project_isolation(self, client, mock_db):
        """Chores from other projects are not returned."""
        await _insert_chore(mock_db, project_id="PVT_2", name="Foreign Chore")

        resp = await client.get("/api/v1/chores/PVT_1")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.anyio
    async def test_chore_response_shape(self, client, mock_db):
        """Returned chore has all expected fields."""
        await _insert_chore(
            mock_db,
            project_id="PVT_1",
            name="Full Chore",
            schedule_type="time",
            schedule_value=7,
        )

        resp = await client.get("/api/v1/chores/PVT_1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

        chore = data[0]
        assert chore["name"] == "Full Chore"
        assert chore["schedule_type"] == "time"
        assert chore["schedule_value"] == 7
        assert chore["status"] == "active"
        assert "id" in chore
        assert "created_at" in chore
        assert "updated_at" in chore
        assert chore["last_triggered_count"] == 0
        assert chore["current_issue_number"] is None


# =============================================================================
# GET /chores/{project_id} — Filtered Pagination
# =============================================================================


class TestListChoresFilteredPagination:
    """Tests for server-side filtering, sorting, and pagination of chores."""

    @pytest.mark.anyio
    async def test_pagination_first_page(self, client, mock_db):
        """GET with limit=3 returns first 3 chores with has_more=true when more exist."""
        for i in range(5):
            await _insert_chore(mock_db, project_id="PVT_1", name=f"Chore {i:02d}")

        resp = await client.get("/api/v1/chores/PVT_1?limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["has_more"] is True
        assert data["next_cursor"] is not None
        assert data["total_count"] == 5

    @pytest.mark.anyio
    async def test_pagination_second_page(self, client, mock_db):
        """GET with cursor returns the next page of chores."""
        for i in range(5):
            await _insert_chore(mock_db, project_id="PVT_1", name=f"Chore {i:02d}")

        resp1 = await client.get("/api/v1/chores/PVT_1?limit=3")
        cursor = resp1.json()["next_cursor"]

        resp2 = await client.get(f"/api/v1/chores/PVT_1?limit=3&cursor={cursor}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is False

    @pytest.mark.anyio
    async def test_pagination_fewer_than_limit(self, client, mock_db):
        """GET with limit returns all chores with has_more=false when fewer than limit."""
        for i in range(2):
            await _insert_chore(mock_db, project_id="PVT_1", name=f"Chore {i}")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is False

    @pytest.mark.anyio
    async def test_filter_by_status_active(self, client, mock_db):
        """GET with status=active returns only active chores."""
        await _insert_chore(mock_db, project_id="PVT_1", name="Active One", status="active")
        await _insert_chore(mock_db, project_id="PVT_1", name="Paused One", status="paused")
        await _insert_chore(mock_db, project_id="PVT_1", name="Active Two", status="active")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&status=active")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert all(c["status"] == "active" for c in data["items"])

    @pytest.mark.anyio
    async def test_filter_by_schedule_type_time(self, client, mock_db):
        """GET with schedule_type=time returns only time-scheduled chores."""
        await _insert_chore(mock_db, name="Time Chore", schedule_type="time", schedule_value=7)
        await _insert_chore(mock_db, name="Count Chore", schedule_type="count", schedule_value=5)
        await _insert_chore(mock_db, name="Unscheduled")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&schedule_type=time")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Time Chore"

    @pytest.mark.anyio
    async def test_filter_by_schedule_type_unscheduled(self, client, mock_db):
        """GET with schedule_type=unscheduled returns only chores with null schedule_type."""
        await _insert_chore(mock_db, name="Time Chore", schedule_type="time", schedule_value=7)
        await _insert_chore(mock_db, name="No Schedule")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&schedule_type=unscheduled")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "No Schedule"

    @pytest.mark.anyio
    async def test_filter_by_search(self, client, mock_db):
        """GET with search returns chores matching name or template_path."""
        await _insert_chore(mock_db, name="Deploy Check", template_path=".github/deploy.md")
        await _insert_chore(mock_db, name="Bug Bash", template_path=".github/bug-bash.md")
        await _insert_chore(mock_db, name="Release Notes", template_path=".github/deploy-notes.md")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&search=deploy")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        names = {c["name"] for c in data["items"]}
        assert "Deploy Check" in names
        assert "Release Notes" in names

    @pytest.mark.anyio
    async def test_combined_filters(self, client, mock_db):
        """GET with status+schedule_type+search returns intersection of all filters."""
        await _insert_chore(
            mock_db,
            name="Deploy Active Time",
            status="active",
            schedule_type="time",
            schedule_value=7,
            template_path=".github/deploy.md",
        )
        await _insert_chore(
            mock_db,
            name="Deploy Paused Time",
            status="paused",
            schedule_type="time",
            schedule_value=7,
            template_path=".github/deploy2.md",
        )
        await _insert_chore(
            mock_db,
            name="Deploy Active Count",
            status="active",
            schedule_type="count",
            schedule_value=5,
            template_path=".github/deploy3.md",
        )
        await _insert_chore(
            mock_db,
            name="Bug Bash",
            status="active",
            schedule_type="time",
            schedule_value=7,
        )

        resp = await client.get(
            "/api/v1/chores/PVT_1?limit=25&status=active&schedule_type=time&search=deploy"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Deploy Active Time"

    @pytest.mark.anyio
    async def test_cursor_pagination_with_filters(self, client, mock_db):
        """Cursor pagination respects active filters on subsequent pages."""
        for i in range(5):
            await _insert_chore(
                mock_db,
                name=f"Active {i:02d}",
                status="active",
            )
        for i in range(3):
            await _insert_chore(mock_db, name=f"Paused {i}", status="paused")

        resp1 = await client.get("/api/v1/chores/PVT_1?limit=3&status=active")
        data1 = resp1.json()
        assert len(data1["items"]) == 3
        assert data1["has_more"] is True
        assert data1["total_count"] == 5

        resp2 = await client.get(
            f"/api/v1/chores/PVT_1?limit=3&status=active&cursor={data1['next_cursor']}"
        )
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        assert data2["has_more"] is False
        assert all(c["status"] == "active" for c in data2["items"])

    @pytest.mark.anyio
    async def test_total_count_reflects_filtered_count(self, client, mock_db):
        """total_count in paginated response reflects filtered count, not total chores."""
        for i in range(4):
            await _insert_chore(mock_db, name=f"Active {i}", status="active")
        for i in range(3):
            await _insert_chore(mock_db, name=f"Paused {i}", status="paused")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&status=active")
        data = resp.json()
        assert data["total_count"] == 4

    @pytest.mark.anyio
    async def test_sort_by_name_asc(self, client, mock_db):
        """GET with sort=name&order=asc returns chores sorted by name ascending."""
        await _insert_chore(mock_db, name="Charlie")
        await _insert_chore(mock_db, name="Alpha")
        await _insert_chore(mock_db, name="Bravo")

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&sort=name&order=asc")
        assert resp.status_code == 200
        data = resp.json()
        names = [c["name"] for c in data["items"]]
        assert names == ["Alpha", "Bravo", "Charlie"]

    @pytest.mark.anyio
    async def test_sort_by_updated_at_desc(self, client, mock_db):
        """GET with sort=updated_at&order=desc returns chores sorted by updated_at descending."""
        c1 = await _insert_chore(mock_db, name="Old")
        c2 = await _insert_chore(mock_db, name="New")
        # Make "New" have a later updated_at
        await mock_db.execute(
            "UPDATE chores SET updated_at = '2026-12-01T00:00:00Z' WHERE id = ?", (c2,)
        )
        await mock_db.execute(
            "UPDATE chores SET updated_at = '2026-01-01T00:00:00Z' WHERE id = ?", (c1,)
        )
        await mock_db.commit()

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&sort=updated_at&order=desc")
        assert resp.status_code == 200
        data = resp.json()
        names = [c["name"] for c in data["items"]]
        assert names == ["New", "Old"]

    @pytest.mark.anyio
    async def test_sort_by_attention(self, client, mock_db):
        """GET with sort=attention&order=asc returns chores sorted by attention score."""
        # Score 0: active + no schedule
        await _insert_chore(mock_db, name="Needs Attention", status="active")
        # Score 3: paused
        await _insert_chore(mock_db, name="Paused", status="paused")
        # Score 2: normal (active + has schedule)
        await _insert_chore(
            mock_db,
            name="Normal",
            status="active",
            schedule_type="time",
            schedule_value=7,
        )

        resp = await client.get("/api/v1/chores/PVT_1?limit=25&sort=attention&order=asc")
        assert resp.status_code == 200
        data = resp.json()
        names = [c["name"] for c in data["items"]]
        assert names == ["Needs Attention", "Normal", "Paused"]


class TestChoresServiceCRUD:
    """Direct unit tests for ChoresService CRUD methods."""

    @pytest.mark.anyio
    async def test_create_and_get(self, mock_db):
        """create_chore + get_chore round-trips correctly."""
        from src.models.chores import ChoreCreate

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Test Chore", template_content="# Template\nContent")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/test-chore.md"
        )

        assert chore.name == "Test Chore"
        assert chore.project_id == "PVT_1"
        assert chore.status.value == "active"
        assert chore.template_path == ".github/ISSUE_TEMPLATE/test-chore.md"

        fetched = await service.get_chore(chore.id)
        assert fetched is not None
        assert fetched.id == chore.id

    @pytest.mark.anyio
    async def test_duplicate_name_raises(self, mock_db):
        """Creating a chore with a duplicate name in the same project raises ValueError."""
        from src.models.chores import ChoreCreate

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Dup", template_content="content")
        await service.create_chore("PVT_1", body, template_path=".github/ISSUE_TEMPLATE/dup.md")

        with pytest.raises(ValueError, match="already exists"):
            await service.create_chore(
                "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/dup2.md"
            )

    @pytest.mark.anyio
    async def test_list_chores(self, mock_db):
        """list_chores returns correct project chores."""
        await _insert_chore(mock_db, project_id="PVT_1", name="A")
        await _insert_chore(mock_db, project_id="PVT_1", name="B")
        await _insert_chore(mock_db, project_id="PVT_2", name="C")

        service = ChoresService(mock_db)
        chores = await service.list_chores("PVT_1")
        assert len(chores) == 2

    @pytest.mark.anyio
    async def test_update_chore(self, mock_db):
        """update_chore applies partial update correctly."""
        from src.models.chores import ChoreUpdate

        cid = await _insert_chore(mock_db, project_id="PVT_1", name="Updatable")
        service = ChoresService(mock_db)

        updated = await service.update_chore(
            cid, ChoreUpdate(schedule_type="time", schedule_value=14)
        )
        assert updated is not None
        assert updated.schedule_type.value == "time"
        assert updated.schedule_value == 14

    @pytest.mark.anyio
    async def test_delete_chore(self, mock_db):
        """delete_chore removes chore and returns True."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="Deletable")
        service = ChoresService(mock_db)

        assert await service.delete_chore(cid) is True
        assert await service.get_chore(cid) is None

    @pytest.mark.anyio
    async def test_delete_nonexistent(self, mock_db):
        """delete_chore returns False for nonexistent ID."""
        service = ChoresService(mock_db)
        assert await service.delete_chore("nonexistent-id") is False

    @pytest.mark.anyio
    async def test_get_nonexistent(self, mock_db):
        """get_chore returns None for missing ID."""
        service = ChoresService(mock_db)
        assert await service.get_chore("nonexistent-id") is None


# =============================================================================
# PATCH /chores/{project_id}/{chore_id}
# =============================================================================


class TestUpdateChore:
    """Tests for the update chore endpoint (schedule, status)."""

    @pytest.mark.anyio
    async def test_update_schedule_time(self, client, mock_db):
        """PATCH with valid time schedule saves correctly."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="TimeChore")
        resp = await client.patch(
            f"/api/v1/chores/PVT_1/{cid}",
            json={"schedule_type": "time", "schedule_value": 14},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["schedule_type"] == "time"
        assert data["schedule_value"] == 14

    @pytest.mark.anyio
    async def test_update_schedule_count(self, client, mock_db):
        """PATCH with valid count schedule saves correctly."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="CountChore")
        resp = await client.patch(
            f"/api/v1/chores/PVT_1/{cid}",
            json={"schedule_type": "count", "schedule_value": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["schedule_type"] == "count"
        assert data["schedule_value"] == 5

    @pytest.mark.anyio
    async def test_update_schedule_value_zero_rejected(self, client, mock_db):
        """PATCH with schedule_value <= 0 is rejected by Pydantic validation."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="ZeroVal")
        resp = await client.patch(
            f"/api/v1/chores/PVT_1/{cid}",
            json={"schedule_type": "time", "schedule_value": 0},
        )
        assert resp.status_code == 422  # Pydantic validation (gt=0)

    @pytest.mark.anyio
    async def test_update_type_without_value_rejected(self, client, mock_db):
        """PATCH with schedule_type but no schedule_value is rejected."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="TypeOnly")
        resp = await client.patch(
            f"/api/v1/chores/PVT_1/{cid}",
            json={"schedule_type": "time"},
        )
        assert resp.status_code == 422
        assert "Invalid chore configuration" in resp.json()["error"]

    @pytest.mark.anyio
    async def test_update_nonexistent_chore(self, client, mock_db):
        """PATCH on a nonexistent chore returns 404."""
        resp = await client.patch(
            "/api/v1/chores/PVT_1/nonexistent",
            json={"schedule_type": "time", "schedule_value": 7},
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_update_wrong_project(self, client, mock_db):
        """PATCH on a chore belonging to a different project returns 404."""
        cid = await _insert_chore(mock_db, project_id="PVT_2", name="OtherProject")
        resp = await client.patch(
            f"/api/v1/chores/PVT_1/{cid}",
            json={"schedule_type": "time", "schedule_value": 7},
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_update_status(self, client, mock_db):
        """PATCH can toggle status to paused."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="StatusChore")
        resp = await client.patch(
            f"/api/v1/chores/PVT_1/{cid}",
            json={"status": "paused"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

    @pytest.mark.anyio
    async def test_paused_chores_excluded_from_trigger_evaluation(self, mock_db):
        """Paused chores are not returned by list_active_scheduled_chores."""
        await _insert_chore(
            mock_db,
            project_id="PVT_1",
            name="Active",
            status="active",
            schedule_type="time",
            schedule_value=7,
        )
        await _insert_chore(
            mock_db,
            project_id="PVT_1",
            name="Paused",
            status="paused",
            schedule_type="time",
            schedule_value=7,
        )

        service = ChoresService(mock_db)
        active = await service.list_active_scheduled_chores()
        names = [c.name for c in active]
        assert "Active" in names
        assert "Paused" not in names


class TestInlineUpdateChoreApi:
    """Tests for the inline chore edit endpoint."""

    @pytest.mark.anyio
    async def test_returns_400_when_repository_cannot_be_resolved_for_pr_changes(
        self,
        client,
        mock_db,
    ):
        """Name/content edits should fail clearly when no repository can be resolved."""
        chore_id = await _insert_chore(mock_db, project_id="PVT_1", name="Inline Edit")

        with patch(
            "src.api.chores.resolve_repository", AsyncMock(side_effect=RuntimeError("boom"))
        ):
            resp = await client.put(
                f"/api/v1/chores/PVT_1/{chore_id}/inline-update",
                json={"name": "Renamed chore"},
            )

        assert resp.status_code == 422
        assert "Could not resolve repository" in resp.json()["error"]


# =============================================================================
# POST /chores/evaluate-triggers
# =============================================================================


class TestEvaluateTriggersApi:
    """Tests for the evaluate triggers endpoint."""

    @pytest.mark.anyio
    async def test_forwards_project_and_parent_issue_count(
        self,
        client,
        mock_github_service,
        mock_session,
    ):
        """POST evaluate-triggers forwards the project filter and current count."""
        service = AsyncMock()
        service.evaluate_triggers.return_value = {
            "evaluated": 1,
            "triggered": 1,
            "skipped": 0,
            "results": [
                {
                    "chore_id": "chore-1",
                    "chore_name": "Bug Bash",
                    "triggered": True,
                    "issue_number": 42,
                    "issue_url": "https://github.com/owner/repo/issues/42",
                }
            ],
        }

        with (
            patch("src.api.chores._get_service", return_value=service),
            patch(
                "src.api.chores.resolve_repository",
                AsyncMock(return_value=("owner", "repo")),
            ),
        ):
            resp = await client.post(
                "/api/v1/chores/evaluate-triggers",
                json={"project_id": "PVT_1", "parent_issue_count": 7},
            )

        assert resp.status_code == 200
        assert resp.json()["triggered"] == 1
        service.evaluate_triggers.assert_awaited_once_with(
            github_service=mock_github_service,
            access_token=mock_session.access_token,
            owner="owner",
            repo="repo",
            project_id="PVT_1",
            parent_issue_count=7,
        )


# =============================================================================
# DELETE /chores/{project_id}/{chore_id}
# =============================================================================


class TestDeleteChore:
    """Tests for the delete chore endpoint."""

    @pytest.mark.anyio
    async def test_delete_existing_chore(self, client, mock_db):
        """DELETE removes a chore and returns success."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="Deletable")
        resp = await client.delete(f"/api/v1/chores/PVT_1/{cid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True
        assert data["closed_issue_number"] is None

        # Verify chore is gone
        list_resp = await client.get("/api/v1/chores/PVT_1")
        assert len(list_resp.json()) == 0

    @pytest.mark.anyio
    async def test_delete_nonexistent_chore(self, client, mock_db):
        """DELETE returns 404 for a nonexistent chore."""
        resp = await client.delete("/api/v1/chores/PVT_1/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_wrong_project(self, client, mock_db):
        """DELETE returns 404 when chore belongs to a different project."""
        cid = await _insert_chore(mock_db, project_id="PVT_2", name="WrongProject")
        resp = await client.delete(f"/api/v1/chores/PVT_1/{cid}")
        assert resp.status_code == 404


# =============================================================================
# POST /chores/{project_id}/chat
# =============================================================================


class TestChoreChat:
    """Tests for the chore chat endpoint (sparse-input template refinement)."""

    @pytest.mark.anyio
    async def test_first_message_creates_conversation(self, client):
        """First chat message should return a conversation_id."""
        mock_ai = AsyncMock(name="AIAgentService")
        mock_ai._call_completion.return_value = "What kind of bugs should be covered?"

        with patch("src.services.ai_agent.get_ai_agent_service", return_value=mock_ai):
            resp = await client.post(
                "/api/v1/chores/PVT_1/chat",
                json={"content": "run a bug bash", "conversation_id": None},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] is not None
        assert data["message"] == "What kind of bugs should be covered?"
        assert data["template_ready"] is False
        assert data["template_content"] is None

    @pytest.mark.anyio
    async def test_subsequent_message_continues_conversation(self, client):
        """Continuing a conversation should reuse the same conversation_id."""
        mock_ai = AsyncMock(name="AIAgentService")
        mock_ai._call_completion.side_effect = [
            "Tell me more about scope",
            "Got it, here's more detail needed",
        ]

        with patch("src.services.ai_agent.get_ai_agent_service", return_value=mock_ai):
            # First message
            resp1 = await client.post(
                "/api/v1/chores/PVT_1/chat",
                json={"content": "bug bash", "conversation_id": None},
            )
            conv_id = resp1.json()["conversation_id"]

            # Second message with same conversation_id
            resp2 = await client.post(
                "/api/v1/chores/PVT_1/chat",
                json={"content": "focus on UI bugs", "conversation_id": conv_id},
            )

        assert resp2.status_code == 200
        data = resp2.json()
        assert data["conversation_id"] == conv_id
        assert data["message"] == "Got it, here's more detail needed"

    @pytest.mark.anyio
    async def test_template_finalization_detected(self, client):
        """When AI returns a ```template block, template_ready should be True."""
        template_response = (
            "Here's your template:\n\n"
            "```template\n"
            "---\nname: Bug Bash\n---\n\n## Bug Bash\n\nRun bug bash weekly.\n"
            "```"
        )
        mock_ai = AsyncMock(name="AIAgentService")
        mock_ai._call_completion.return_value = template_response

        with patch("src.services.ai_agent.get_ai_agent_service", return_value=mock_ai):
            resp = await client.post(
                "/api/v1/chores/PVT_1/chat",
                json={"content": "bug bash weekly", "conversation_id": None},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["template_ready"] is True
        assert data["template_content"] is not None
        assert "Bug Bash" in data["template_content"]

    @pytest.mark.anyio
    async def test_ai_failure_returns_500(self, client):
        """When the AI service fails, return 500."""
        mock_ai = AsyncMock(name="AIAgentService")
        mock_ai._call_completion.side_effect = RuntimeError("AI service down")

        with patch("src.services.ai_agent.get_ai_agent_service", return_value=mock_ai):
            resp = await client.post(
                "/api/v1/chores/PVT_1/chat",
                json={"content": "test", "conversation_id": None},
            )

        assert resp.status_code == 500
        assert "Failed to complete chat" in resp.json()["error"]


# =============================================================================
# POST /chores/{project_id}/{chore_id}/trigger
# =============================================================================


class TestManualTrigger:
    """Tests for the manual trigger endpoint."""

    @pytest.mark.anyio
    async def test_trigger_success(self, client, mock_db, mock_github_service):
        """POST trigger creates issue and returns result."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="Bug Bash")

        mock_github_service.create_issue.return_value = {
            "number": 42,
            "node_id": "I_node_42",
            "html_url": "https://github.com/owner/repo/issues/42",
        }
        mock_github_service.add_issue_to_project.return_value = "item-id"

        with (
            patch("src.api.chores.resolve_repository", return_value=("owner", "repo")),
            patch("src.services.workflow_orchestrator.get_workflow_config", return_value=None),
        ):
            resp = await client.post(f"/api/v1/chores/PVT_1/{cid}/trigger")

        assert resp.status_code == 200
        data = resp.json()
        assert data["triggered"] is True
        assert data["chore_name"] == "Bug Bash"
        assert data["issue_number"] == 42

    @pytest.mark.anyio
    async def test_trigger_409_open_instance(self, client, mock_db, mock_github_service):
        """POST trigger returns 409 when an open issue already exists."""
        cid = await _insert_chore(mock_db, project_id="PVT_1", name="Bug Bash")
        # Set current issue number
        await mock_db.execute("UPDATE chores SET current_issue_number = 10 WHERE id = ?", (cid,))
        await mock_db.commit()

        mock_github_service.check_issue_closed.return_value = False

        with patch("src.api.chores.resolve_repository", return_value=("owner", "repo")):
            resp = await client.post(f"/api/v1/chores/PVT_1/{cid}/trigger")

        assert resp.status_code == 409
        assert "Open instance" in resp.json()["error"]

    @pytest.mark.anyio
    async def test_trigger_404_nonexistent(self, client, mock_db):
        """POST trigger returns 404 for nonexistent chore."""
        with patch("src.api.chores.resolve_repository", return_value=("owner", "repo")):
            resp = await client.post("/api/v1/chores/PVT_1/nonexistent/trigger")

        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_trigger_404_wrong_project(self, client, mock_db):
        """POST trigger returns 404 when chore belongs to different project."""
        cid = await _insert_chore(mock_db, project_id="PVT_2", name="Wrong Proj")

        with patch("src.api.chores.resolve_repository", return_value=("owner", "repo")):
            resp = await client.post(f"/api/v1/chores/PVT_1/{cid}/trigger")

        assert resp.status_code == 404
