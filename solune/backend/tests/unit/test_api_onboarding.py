"""Tests for the onboarding tour state API endpoints (FR-038).

Covers:
- GET /api/v1/onboarding/state — returns defaults for new users, stored state for existing
- PUT /api/v1/onboarding/state — create, update, complete, dismiss flows
- UPSERT logic — COALESCE preserves existing timestamps
- Validation — current_step bounds (0-13), required fields
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.helpers.assertions import assert_api_success

# ---------------------------------------------------------------------------
# GET /api/v1/onboarding/state
# ---------------------------------------------------------------------------


class TestGetOnboardingState:
    async def test_returns_defaults_for_new_user(self, client: AsyncClient):
        """New user with no stored state gets defaults."""
        resp = await client.get("/api/v1/onboarding/state")
        data = assert_api_success(resp)

        assert data["user_id"] == "12345"
        assert data["current_step"] == 0
        assert data["completed"] is False
        assert data["dismissed_at"] is None
        assert data["completed_at"] is None

    async def test_returns_stored_state(self, client: AsyncClient, mock_db):
        """Returns previously stored onboarding state."""
        await mock_db.execute(
            """
            INSERT INTO onboarding_tour_state
                (user_id, current_step, completed, completed_at, dismissed_at)
            VALUES ('12345', 3, 0, NULL, NULL)
            """,
        )
        await mock_db.commit()

        resp = await client.get("/api/v1/onboarding/state")
        data = assert_api_success(resp)

        assert data["user_id"] == "12345"
        assert data["current_step"] == 3
        assert data["completed"] is False


# ---------------------------------------------------------------------------
# PUT /api/v1/onboarding/state — basic UPSERT
# ---------------------------------------------------------------------------


class TestUpdateOnboardingState:
    async def test_creates_initial_state(self, client: AsyncClient):
        """PUT creates a new row when none exists for the user."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 1, "completed": False, "dismissed": False},
        )
        data = assert_api_success(resp)

        assert data["user_id"] == "12345"
        assert data["current_step"] == 1
        assert data["completed"] is False

    async def test_updates_existing_state(self, client: AsyncClient):
        """PUT updates the step for a user who already has state."""
        # Create initial state
        await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 0, "completed": False, "dismissed": False},
        )
        # Update to step 5
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 5, "completed": False, "dismissed": False},
        )
        data = assert_api_success(resp)
        assert data["current_step"] == 5

        # Verify via GET
        resp = await client.get("/api/v1/onboarding/state")
        data = assert_api_success(resp)
        assert data["current_step"] == 5


# ---------------------------------------------------------------------------
# PUT — completion flow
# ---------------------------------------------------------------------------


class TestOnboardingCompletion:
    async def test_completing_sets_completed_at(self, client: AsyncClient):
        """Setting completed=True populates completed_at timestamp."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 9, "completed": True, "dismissed": False},
        )
        data = assert_api_success(resp)

        assert data["completed"] is True
        assert data["completed_at"] is not None

    async def test_completed_at_not_reset_on_subsequent_update(self, client: AsyncClient, mock_db):
        """COALESCE logic preserves completed_at once set."""
        # Complete the tour
        await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 9, "completed": True, "dismissed": False},
        )

        # Read the stored completed_at
        cursor = await mock_db.execute(
            "SELECT completed_at FROM onboarding_tour_state WHERE user_id = '12345'"
        )
        row = await cursor.fetchone()
        original_completed_at = row["completed_at"]
        assert original_completed_at is not None

        # Update step without re-completing
        await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 3, "completed": False, "dismissed": False},
        )

        # completed_at should be preserved by COALESCE
        cursor = await mock_db.execute(
            "SELECT completed_at FROM onboarding_tour_state WHERE user_id = '12345'"
        )
        row = await cursor.fetchone()
        assert row["completed_at"] == original_completed_at


# ---------------------------------------------------------------------------
# PUT — dismissal flow
# ---------------------------------------------------------------------------


class TestOnboardingDismissal:
    async def test_dismissing_sets_dismissed_at(self, client: AsyncClient):
        """Setting dismissed=True populates dismissed_at timestamp."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 2, "completed": False, "dismissed": True},
        )
        data = assert_api_success(resp)
        assert data["dismissed_at"] is not None

    async def test_dismissed_at_preserved_on_subsequent_update(self, client: AsyncClient, mock_db):
        """COALESCE logic preserves dismissed_at once set."""
        # Dismiss the tour
        await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 2, "completed": False, "dismissed": True},
        )

        cursor = await mock_db.execute(
            "SELECT dismissed_at FROM onboarding_tour_state WHERE user_id = '12345'"
        )
        row = await cursor.fetchone()
        original_dismissed_at = row["dismissed_at"]
        assert original_dismissed_at is not None

        # Update step without re-dismissing
        await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": 5, "completed": False, "dismissed": False},
        )

        cursor = await mock_db.execute(
            "SELECT dismissed_at FROM onboarding_tour_state WHERE user_id = '12345'"
        )
        row = await cursor.fetchone()
        assert row["dismissed_at"] == original_dismissed_at


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestOnboardingValidation:
    @pytest.mark.parametrize("step", [-1, 14, 100])
    async def test_invalid_step_rejected(self, client: AsyncClient, step: int):
        """Steps outside 0-13 range are rejected with 422."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": step, "completed": False, "dismissed": False},
        )
        assert resp.status_code == 422

    async def test_missing_current_step_rejected(self, client: AsyncClient):
        """current_step is required."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"completed": False, "dismissed": False},
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("step", [0, 5, 13])
    async def test_valid_step_accepted(self, client: AsyncClient, step: int):
        """Boundary values 0 and 13 are accepted."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": step, "completed": False, "dismissed": False},
        )
        assert resp.status_code == 200

    @pytest.mark.parametrize("step", [11, 12, 13])
    async def test_step_boundary_11_to_13(self, client: AsyncClient, step: int):
        """Steps 11-13 are accepted after expanding the validator from le=10 to le=13."""
        resp = await client.put(
            "/api/v1/onboarding/state",
            json={"current_step": step, "completed": False, "dismissed": False},
        )
        data = assert_api_success(resp)
        assert data["current_step"] == step
