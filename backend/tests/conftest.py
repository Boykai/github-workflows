"""
Pytest configuration for backend tests.
"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"
