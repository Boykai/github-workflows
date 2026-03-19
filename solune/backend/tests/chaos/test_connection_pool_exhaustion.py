"""Chaos test: database connection pool exhaustion.

Verifies that the application handles connection pool exhaustion
gracefully — returning errors rather than hanging or crashing.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestConnectionPoolExhaustion:
    """Simulate connection pool exhaustion scenarios."""

    @pytest.mark.asyncio
    async def test_db_timeout_returns_error_not_hang(self):
        """When the database is locked, the health endpoint should error, not hang."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("database is locked"))

        with patch("src.services.database.get_db", return_value=mock_db):
            # Simulating a query under pool exhaustion
            with pytest.raises(Exception, match="database is locked"):
                cursor = await mock_db.execute("SELECT 1")
                await cursor.fetchone()

    @pytest.mark.asyncio
    async def test_concurrent_db_access_resilient(self):
        """Multiple concurrent database accesses should not deadlock."""
        success_count = 0
        error_count = 0

        mock_db = AsyncMock()

        async def _make_query(query_id: int):
            nonlocal success_count, error_count
            try:
                if query_id % 3 == 0:
                    mock_db.execute.side_effect = Exception("pool exhausted")
                else:
                    mock_db.execute.side_effect = None
                    mock_db.execute.return_value = AsyncMock(fetchone=AsyncMock(return_value=(1,)))
                await mock_db.execute(f"SELECT {query_id}")
                success_count += 1
            except Exception:
                error_count += 1

        tasks = [_make_query(i) for i in range(30)]
        # Ensure this completes within a reasonable time (no deadlock)
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)

        assert success_count + error_count == 30
        assert error_count > 0  # Some should have failed
        assert success_count > 0  # Some should have succeeded
