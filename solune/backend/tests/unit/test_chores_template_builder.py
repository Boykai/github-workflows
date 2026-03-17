"""Tests for chore template builder (src/services/chores/template_builder.py).

Covers:
- build_template: front matter generation and preservation
- derive_template_path: slugification and path construction
- is_sparse_input: heuristic classification
- _slugify: special character handling
- commit_template_to_repo: success and failure paths
- merge_chore_pr: success and failure paths
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.services.chores.template_builder import (
    _slugify,
    build_template,
    commit_template_to_repo,
    derive_template_path,
    is_sparse_input,
    merge_chore_pr,
)

# ── build_template ────────────────────────────────────────────────────────


class TestBuildTemplate:
    """Tests for YAML front matter generation."""

    def test_content_with_existing_front_matter_preserved(self):
        """Content already containing front matter is used as-is."""
        content = "---\nname: Custom\nabout: My chore\n---\n\nDo the thing"
        result = build_template("Custom", content)
        assert result.startswith("---")
        assert "name: Custom" in result
        assert result.count("---") == 2

    def test_content_without_front_matter_gets_default(self):
        """Plain content gets default YAML front matter prepended."""
        result = build_template("DB Cleanup", "Vacuum the database")
        assert result.startswith("---")
        assert "name: DB Cleanup" in result
        assert "about: Recurring chore — DB Cleanup" in result
        assert "title: '[CHORE] DB Cleanup'" in result
        assert "labels: chore" in result
        assert "Vacuum the database" in result


# ── derive_template_path ──────────────────────────────────────────────────


class TestDeriveTemplatePath:
    """Tests for template path derivation from chore name."""

    def test_basic_slugification(self):
        """Simple name is slugified into path."""
        path = derive_template_path("Bug Bash")
        assert path == ".github/ISSUE_TEMPLATE/chore-bug-bash.md"

    def test_special_characters_handled(self):
        """Special characters are replaced with hyphens."""
        path = derive_template_path("DB Cleanup (Weekly)")
        assert path == ".github/ISSUE_TEMPLATE/chore-db-cleanup-weekly.md"

    def test_numbers_preserved(self):
        """Numbers in the name are preserved."""
        path = derive_template_path("Phase 2 Rollout")
        assert path == ".github/ISSUE_TEMPLATE/chore-phase-2-rollout.md"


# ── is_sparse_input ───────────────────────────────────────────────────────


class TestIsSparseInput:
    """Tests for sparse vs. rich content classification."""

    def test_empty_is_sparse(self):
        """Empty string is classified as sparse."""
        assert is_sparse_input("") is True

    def test_whitespace_only_is_sparse(self):
        """Whitespace-only string is classified as sparse."""
        assert is_sparse_input("   ") is True

    def test_short_text_is_sparse(self):
        """Short phrase (≤15 words) is classified as sparse."""
        assert is_sparse_input("Clean up old branches") is True

    def test_text_with_headings_is_rich(self):
        """Text containing markdown headings is classified as rich."""
        text = "## Steps\n1. First\n2. Second\n3. Third"
        assert is_sparse_input(text) is False

    def test_text_with_lists_is_rich(self):
        """Text containing markdown list markers is classified as rich."""
        text = "Tasks to do:\n- Clean cache\n- Rotate secrets\n- Update deps"
        assert is_sparse_input(text) is False

    def test_long_multiline_text_is_rich(self):
        """Long multi-line text (≥3 newlines) is classified as rich."""
        text = "Line one\nLine two\nLine three\nLine four"
        assert is_sparse_input(text) is False

    def test_moderate_single_line_is_sparse(self):
        """Single line with ≤40 words is still sparse."""
        text = "Run a database vacuum and clean up old sessions from the system"
        assert is_sparse_input(text) is True


# ── _slugify ──────────────────────────────────────────────────────────────


class TestSlugify:
    """Tests for slug generation from chore names."""

    def test_lowercase_conversion(self):
        """Name is lowercased."""
        assert _slugify("DB Cleanup") == "db-cleanup"

    def test_special_chars_replaced(self):
        """Non-alphanumeric characters become hyphens."""
        assert _slugify("Cleanup (Weekly)") == "cleanup-weekly"

    def test_leading_trailing_hyphens_stripped(self):
        """Leading and trailing hyphens are stripped."""
        assert _slugify("--test--") == "test"

    def test_empty_name_returns_chore(self):
        """Empty name falls back to 'chore'."""
        assert _slugify("") == "chore"

    def test_numbers_preserved(self):
        """Numbers are preserved in slugs."""
        assert _slugify("Phase 2") == "phase-2"


# ── commit_template_to_repo ───────────────────────────────────────────────


class TestCommitTemplateToRepo:
    """Tests for the commit-template-to-repo workflow."""

    async def test_success_path(self):
        """Full commit workflow returns template path, PR, and tracking issue."""
        gh = AsyncMock(name="GitHubProjectsService")
        gh.get_repository_info.return_value = {
            "repository_id": "R_abc",
            "default_branch": "main",
            "head_oid": "abc123",
        }
        gh.create_branch.return_value = "ref-id-1"
        gh.commit_files.return_value = "commit-oid-1"
        gh.create_pull_request.return_value = {
            "number": 42,
            "url": "https://github.com/owner/repo/pull/42",
        }
        gh.create_issue.return_value = {
            "number": 10,
            "node_id": "I_xyz",
        }
        gh.add_issue_to_project.return_value = "PVTI_1"

        result = await commit_template_to_repo(
            github_service=gh,
            access_token="tok",
            owner="owner",
            repo="repo",
            project_id="PVT_1",
            name="DB Cleanup",
            template_content="---\nname: DB Cleanup\n---\nBody",
        )

        assert result["template_path"] == ".github/ISSUE_TEMPLATE/chore-db-cleanup.md"
        assert result["pr_number"] == 42
        assert result["tracking_issue_number"] == 10
        gh.create_branch.assert_awaited_once()
        gh.commit_files.assert_awaited_once()

    async def test_branch_creation_fails_raises_runtime_error(self):
        """RuntimeError is raised when branch creation returns None."""
        gh = AsyncMock(name="GitHubProjectsService")
        gh.get_repository_info.return_value = {
            "repository_id": "R_abc",
            "default_branch": "main",
            "head_oid": "abc123",
        }
        gh.create_branch.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create branch"):
            await commit_template_to_repo(
                github_service=gh,
                access_token="tok",
                owner="owner",
                repo="repo",
                project_id="PVT_1",
                name="Fail",
                template_content="body",
            )


# ── merge_chore_pr ────────────────────────────────────────────────────────


class TestMergeChorePr:
    """Tests for the merge-chore-PR workflow."""

    async def test_merge_success(self):
        """Successful merge returns (True, None)."""
        gh = AsyncMock(name="GitHubProjectsService")
        gh.get_pull_request.return_value = {"id": "PR_abc"}
        gh.merge_pull_request.return_value = {"merged": True}

        success, error = await merge_chore_pr(gh, "tok", "owner", "repo", 42)
        assert success is True
        assert error is None

    async def test_pr_not_found_returns_false(self):
        """Returns (False, error) when PR is not found."""
        gh = AsyncMock(name="GitHubProjectsService")
        gh.get_pull_request.return_value = None

        success, error = await merge_chore_pr(gh, "tok", "owner", "repo", 999)
        assert success is False
        assert "not found" in error
