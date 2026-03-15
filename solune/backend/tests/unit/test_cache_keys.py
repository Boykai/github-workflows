"""Verification tests for project-scoped cache keys."""

from __future__ import annotations

from src.constants import cache_key_agent_output, cache_key_issue_pr, cache_key_review_requested


class TestCacheKeyScoping:
    """Cache keys are scoped by project_id to prevent cross-project collision."""

    def test_same_issue_different_project_different_key(self) -> None:
        key_a = cache_key_issue_pr(42, 101, project_id="PVT_a")
        key_b = cache_key_issue_pr(42, 101, project_id="PVT_b")
        assert key_a != key_b

    def test_same_project_same_issue_same_key(self) -> None:
        key_a = cache_key_issue_pr(42, 101, project_id="PVT_a")
        key_b = cache_key_issue_pr(42, 101, project_id="PVT_a")
        assert key_a == key_b

    def test_agent_output_scoped(self) -> None:
        key_a = cache_key_agent_output(42, "copilot", 101, project_id="PVT_a")
        key_b = cache_key_agent_output(42, "copilot", 101, project_id="PVT_b")
        assert key_a != key_b

    def test_review_requested_scoped(self) -> None:
        key_a = cache_key_review_requested(42, project_id="PVT_a")
        key_b = cache_key_review_requested(42, project_id="PVT_b")
        assert key_a != key_b

    def test_backward_compatible_without_project_id(self) -> None:
        """When project_id is omitted, keys match the old format but emit a deprecation warning."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            key = cache_key_issue_pr(42, 101)
            assert key == "42:101"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "project_id" in str(w[0].message)
