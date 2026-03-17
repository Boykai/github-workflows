"""Unit tests for Protocol types.

Covers:
- ModelProvider protocol exists and is runtime_checkable
- CacheInvalidationPolicy protocol exists and is runtime_checkable
- Concrete implementations satisfy the protocols (structural subtyping)
"""

from typing import Any

from src.protocols import CacheInvalidationPolicy, ModelProvider

# =============================================================================
# ModelProvider
# =============================================================================


class TestModelProviderProtocol:
    """Tests for the ModelProvider protocol."""

    def test_protocol_is_importable(self):
        assert ModelProvider is not None

    def test_protocol_is_runtime_checkable(self):
        """A class with matching methods should be recognized as implementing the protocol."""

        class DummyProvider:
            async def fetch_models(self, token: str | None) -> list[Any]:
                return []

        assert isinstance(DummyProvider(), ModelProvider)

    def test_non_conforming_class_rejected(self):
        """A class without the required methods should NOT satisfy the protocol."""

        class Empty:
            pass

        assert not isinstance(Empty(), ModelProvider)


# =============================================================================
# CacheInvalidationPolicy
# =============================================================================


class TestCacheInvalidationPolicyProtocol:
    """Tests for the CacheInvalidationPolicy protocol."""

    def test_protocol_is_importable(self):
        assert CacheInvalidationPolicy is not None

    def test_protocol_is_runtime_checkable(self):
        """A conforming class should pass isinstance check."""

        class DummyPolicy:
            def should_invalidate(self, key: str, age_seconds: float) -> bool:
                return False

            def on_write(self, key: str) -> None:
                pass

        assert isinstance(DummyPolicy(), CacheInvalidationPolicy)

    def test_partial_implementation_rejected(self):
        """A class with only one of the two required methods should fail."""

        class PartialPolicy:
            def should_invalidate(self, key: str, age_seconds: float) -> bool:
                return True

        assert not isinstance(PartialPolicy(), CacheInvalidationPolicy)
