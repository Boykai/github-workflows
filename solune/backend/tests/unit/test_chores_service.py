"""Unit tests for ChoresService and template builder."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from src.services.chores.template_builder import (
    build_template,
    derive_template_path,
    is_sparse_input,
)

# =============================================================================
# build_template
# =============================================================================


class TestBuildTemplate:
    """Tests for YAML front matter generation."""

    def test_adds_front_matter_to_plain_content(self):
        """Plain content gets default YAML front matter prepended."""
        result = build_template("Bug Bash", "Run a bug bash across the codebase")
        assert result.startswith("---")
        assert "name: Bug Bash" in result
        assert "about: Recurring chore — Bug Bash" in result
        assert "title: '[CHORE] Bug Bash'" in result
        assert "labels: chore" in result
        assert "Run a bug bash across the codebase" in result

    def test_preserves_existing_front_matter(self):
        """Content that already has front matter is used as-is."""
        content = "---\nname: Custom\nabout: My custom template\n---\n\nBody here"
        result = build_template("Custom", content)
        assert result.startswith("---")
        assert "name: Custom" in result
        assert "Body here" in result
        # Should NOT have double front matter
        assert result.count("---") == 2

    def test_whitespace_handling(self):
        """Content with leading whitespace before front matter is detected."""
        content = "  ---\nname: Spaced\n---\nBody"
        result = build_template("Spaced", content)
        # Should detect existing front matter
        assert result.count("name: Spaced") == 1


# =============================================================================
# derive_template_path
# =============================================================================


class TestDeriveTemplatePath:
    """Tests for template path generation."""

    def test_basic_slug(self):
        assert derive_template_path("Bug Bash") == ".github/ISSUE_TEMPLATE/chore-bug-bash.md"

    def test_special_characters(self):
        result = derive_template_path("Dependency Update (weekly)")
        assert result == ".github/ISSUE_TEMPLATE/chore-dependency-update-weekly.md"

    def test_numbers_preserved(self):
        result = derive_template_path("Sprint 42 Review")
        assert result == ".github/ISSUE_TEMPLATE/chore-sprint-42-review.md"


# =============================================================================
# is_sparse_input
# =============================================================================


class TestIsSparseInput:
    """Tests for sparse vs rich input detection heuristic."""

    def test_empty_is_sparse(self):
        assert is_sparse_input("") is True

    def test_short_phrase_is_sparse(self):
        assert is_sparse_input("create refactor chore") is True

    def test_medium_phrase_without_structure_is_sparse(self):
        assert is_sparse_input("bug bash review all code for security issues") is True

    def test_single_line_under_40_words_is_sparse(self):
        text = " ".join(["word"] * 30)
        assert is_sparse_input(text) is True

    def test_long_text_without_structure_is_rich(self):
        text = " ".join(["word"] * 50)
        assert is_sparse_input(text) is False

    def test_markdown_with_headings_is_rich(self):
        text = "## Overview\nThis is a bug bash\n\n## Steps\n1. Do this\n2. Do that"
        assert is_sparse_input(text) is False

    def test_markdown_with_lists_is_rich(self):
        text = "- Item one\n- Item two\n- Item three"
        assert is_sparse_input(text) is False

    def test_multi_paragraph_is_rich(self):
        text = "First paragraph\n\nSecond paragraph\n\nThird paragraph\n\nFourth"
        assert is_sparse_input(text) is False


# =============================================================================
# _strip_front_matter
# =============================================================================


class TestStripFrontMatter:
    """Tests for YAML front matter stripping from issue bodies."""

    def test_strips_yaml_front_matter(self):
        text = "---\nname: Bug Bash\nabout: Chore\n---\n## Steps\n1. Do stuff"
        from src.services.chores.service import _strip_front_matter

        assert _strip_front_matter(text) == "## Steps\n1. Do stuff"

    def test_no_front_matter_unchanged(self):
        text = "## Steps\n1. Do stuff"
        from src.services.chores.service import _strip_front_matter

        assert _strip_front_matter(text) == text

    def test_empty_string(self):
        from src.services.chores.service import _strip_front_matter

        assert _strip_front_matter("") == ""


# =============================================================================
# chat._is_template_ready defensive parsing
# =============================================================================


class TestIsTemplateReady:
    """Tests for template readiness detection in chat module."""

    def test_complete_template_detected(self):
        from src.services.chores.chat import _is_template_ready

        response = "Here is your template:\n```template\n---\nname: X\n---\nbody\n```\nDone!"
        ready, content = _is_template_ready(response)
        assert ready is True
        assert content is not None
        assert "name: X" in content

    def test_unterminated_fence_returns_false(self):
        from src.services.chores.chat import _is_template_ready

        response = "Here is your template:\n```template\n---\nname: X\n---\nbody"
        ready, content = _is_template_ready(response)
        assert ready is False
        assert content is None

    def test_no_template_marker(self):
        from src.services.chores.chat import _is_template_ready

        ready, content = _is_template_ready("Just a regular message")
        assert ready is False
        assert content is None


# =============================================================================
# chat._evict_stale_conversations
# =============================================================================


class TestConversationEviction:
    """Tests for TTL and size-bound eviction of in-memory conversations."""

    def test_evicts_expired_conversations(self):
        from datetime import timedelta

        from src.services.chores.chat import (
            _conversations,
            _evict_stale_conversations,
        )

        _conversations.clear()
        # Add a conversation that expired 2 hours ago
        _conversations["old"] = {
            "messages": [],
            "created_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        }
        _conversations["recent"] = {
            "messages": [],
            "created_at": datetime.now(UTC).isoformat(),
        }
        _evict_stale_conversations()
        assert "old" not in _conversations
        assert "recent" in _conversations
        _conversations.clear()

    def test_evicts_when_over_capacity(self):
        from src.services.chores.chat import (
            _MAX_CONVERSATIONS,
            _conversations,
            _evict_stale_conversations,
        )

        _conversations.clear()
        for i in range(_MAX_CONVERSATIONS + 5):
            _conversations[f"c{i}"] = {
                "messages": [],
                "created_at": datetime.now(UTC).isoformat(),
            }
        _evict_stale_conversations()
        assert len(_conversations) <= _MAX_CONVERSATIONS
        _conversations.clear()


# =============================================================================
# ChoresService.create_chore duplicate rejection
# =============================================================================


class TestCreateChoreValidation:
    """Tests for chore creation validation."""

    @pytest.mark.anyio
    async def test_duplicate_name_rejected(self, mock_db):
        """Attempting to create a chore with a duplicate name raises ValueError."""
        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Weekly Review", template_content="Review content")

        await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-weekly-review.md"
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_chore(
                "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-weekly-review-2.md"
            )

    @pytest.mark.anyio
    async def test_same_name_different_project_allowed(self, mock_db):
        """Same name in different projects should succeed."""
        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Shared Name", template_content="Content")

        c1 = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-shared-name.md"
        )
        c2 = await service.create_chore(
            "PVT_2", body, template_path=".github/ISSUE_TEMPLATE/chore-shared-name.md"
        )

        assert c1.project_id == "PVT_1"
        assert c2.project_id == "PVT_2"


class TestInlineUpdateChore:
    """Tests for inline chore updates that create PRs."""

    @pytest.mark.anyio
    async def test_conflict_detected_when_expected_sha_mismatches(self, mock_db):
        """Inline edits should reject when the repository file SHA changed."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate, ChoreInlineUpdate
        from src.services.chores.service import ChoreConflictError, ChoresService

        service = ChoresService(mock_db)
        chore = await service.create_chore(
            "PVT_1",
            ChoreCreate(name="Conflict Test", template_content="Original content"),
            template_path=".github/ISSUE_TEMPLATE/chore-conflict-test.md",
        )

        mock_github = AsyncMock()
        mock_github.rest_request.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {
                "sha": "current-sha",
                "content": "VXBkYXRlZCBjb250ZW50",
            },
        )

        with pytest.raises(ChoreConflictError) as exc_info:
            await service.inline_update_chore(
                chore.id,
                ChoreInlineUpdate(
                    template_content="Updated content",
                    expected_sha="stale-sha",
                ),
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert exc_info.value.current_sha == "current-sha"
        assert exc_info.value.current_content == "Updated content"

    @pytest.mark.anyio
    async def test_name_change_updates_template_path_and_deletes_old_file(self, mock_db):
        """Renaming a chore should update template_path in DB and delete the old file in the PR."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate, ChoreInlineUpdate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        chore = await service.create_chore(
            "PVT_1",
            ChoreCreate(name="Old Name", template_content="Body content"),
            template_path=".github/ISSUE_TEMPLATE/chore-old-name.md",
        )
        assert chore.template_path == ".github/ISSUE_TEMPLATE/chore-old-name.md"

        mock_github = AsyncMock()
        mock_github.get_repository_info.return_value = {
            "repository_id": "R_1",
            "default_branch": "main",
            "head_oid": "abc123",
        }
        mock_github.create_branch.return_value = "ref-id"
        mock_github.commit_files.return_value = "commit-oid"
        mock_github.create_pull_request.return_value = {
            "number": 99,
            "url": "https://github.com/test/repo/pull/99",
        }

        result = await service.inline_update_chore(
            chore.id,
            ChoreInlineUpdate(name="New Name", template_content="Updated body"),
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        # DB should have the new template_path
        updated = result["chore"]
        assert updated.name == "New Name"
        assert updated.template_path == ".github/ISSUE_TEMPLATE/chore-new-name.md"

        # commit_files should have been called with the new path and old path as deletion
        mock_github.commit_files.assert_awaited_once()
        commit_call = mock_github.commit_files.call_args
        files_arg = (
            commit_call.args[5] if len(commit_call.args) > 5 else commit_call.kwargs.get("files")
        )
        # Files may be positional or keyword — check the committed file path
        assert any(f["path"] == ".github/ISSUE_TEMPLATE/chore-new-name.md" for f in files_arg)
        # The old file path should be in the deletions kwarg
        deletions = commit_call.kwargs.get("deletions") or (
            commit_call.args[8] if len(commit_call.args) > 8 else None
        )
        assert deletions == [".github/ISSUE_TEMPLATE/chore-old-name.md"]

        assert result["pr_number"] == 99


# =============================================================================


class TestTriggerChore:
    """Tests for the trigger_chore() method."""

    @pytest.mark.anyio
    async def test_trigger_creates_issue_and_updates_record(self, mock_db):
        """trigger_chore creates a GitHub issue and updates the chore record."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Trigger Test", template_content="Content body")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-trigger-test.md"
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 1,
            "node_id": "I_1",
            "number": 42,
            "html_url": "https://github.com/test/repo/issues/42",
        }
        mock_github.add_issue_to_project.return_value = "item-1"

        result = await service.trigger_chore(
            chore,
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is True
        assert result.issue_number == 42
        mock_github.create_issue.assert_awaited_once()
        mock_github.add_issue_to_project.assert_awaited_once()

        # Verify chore record updated
        updated = await service.get_chore(chore.id)
        assert updated.current_issue_number == 42
        assert updated.current_issue_node_id == "I_1"
        assert updated.last_triggered_at is not None

    @pytest.mark.anyio
    async def test_open_instance_skips_trigger(self, mock_db):
        """trigger_chore skips when an open instance exists."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Skip Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-skip-test.md"
        )

        # Simulate an open issue
        await service.update_chore_fields(
            chore.id, current_issue_number=10, current_issue_node_id="I_10"
        )
        chore = await service.get_chore(chore.id)

        mock_github = AsyncMock()
        mock_github.check_issue_closed.return_value = False

        result = await service.trigger_chore(
            chore,
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is False
        assert "Open instance" in result.skip_reason
        mock_github.create_issue.assert_not_awaited()

    @pytest.mark.anyio
    async def test_closed_issue_allows_retrigger(self, mock_db):
        """trigger_chore proceeds when the open instance was closed externally."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Closed Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-closed-test.md"
        )

        await service.update_chore_fields(
            chore.id, current_issue_number=10, current_issue_node_id="I_10"
        )
        chore = await service.get_chore(chore.id)

        mock_github = AsyncMock()
        mock_github.check_issue_closed.return_value = True
        mock_github.create_issue.return_value = {
            "id": 2,
            "node_id": "I_2",
            "number": 43,
            "html_url": "https://github.com/test/repo/issues/43",
        }
        mock_github.add_issue_to_project.return_value = "item-2"

        result = await service.trigger_chore(
            chore,
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is True
        assert result.issue_number == 43

    @pytest.mark.anyio
    async def test_cas_prevents_double_fire(self, mock_db):
        """CAS update prevents double-fire when last_triggered_at has changed."""
        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="CAS Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-cas-test.md"
        )

        # Simulate a concurrent trigger by modifying last_triggered_at
        await service.update_chore_fields(chore.id, last_triggered_at="2024-01-01T00:00:00Z")

        # Try CAS with the old (None) value — should fail
        result = await service.update_chore_after_trigger(
            chore.id,
            current_issue_number=99,
            current_issue_node_id="I_99",
            last_triggered_at="2024-06-01T00:00:00Z",
            last_triggered_count=0,
            old_last_triggered_at=None,  # stale value
        )
        assert result is False

    @pytest.mark.anyio
    async def test_cas_failure_closes_duplicate_issue(self, mock_db):
        """When CAS fails, trigger_chore closes the duplicate issue and returns not-triggered."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="CAS Close Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-cas-close.md"
        )

        # Simulate a concurrent trigger by modifying last_triggered_at
        await service.update_chore_fields(chore.id, last_triggered_at="2024-01-01T00:00:00Z")
        # But pass the stale chore (old last_triggered_at=None) to trigger_chore
        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 3,
            "node_id": "I_3",
            "number": 50,
            "html_url": "https://github.com/test/repo/issues/50",
        }
        mock_github.add_issue_to_project.return_value = "item-3"

        result = await service.trigger_chore(
            chore,  # stale: last_triggered_at is None
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is False
        assert "CAS conflict" in result.skip_reason
        # Duplicate issue should have been closed
        mock_github.update_issue_state.assert_awaited_once_with(
            "token", "test", "repo", 50, state="closed", state_reason="not_planned"
        )


# =============================================================================
# commit_template_to_repo — existing branch handling
# =============================================================================


class TestCommitTemplateExistingBranch:
    """Tests for commit_template_to_repo when the branch already exists."""

    @pytest.mark.anyio
    async def test_uses_branch_head_when_branch_exists(self):
        """When create_branch returns 'existing', commit should use the branch HEAD OID."""
        from unittest.mock import AsyncMock

        from src.services.chores.template_builder import commit_template_to_repo

        mock_github = AsyncMock()
        mock_github.get_repository_info.return_value = {
            "repository_id": "R_1",
            "default_branch": "main",
            "head_oid": "default-oid",
        }
        mock_github.create_branch.return_value = "existing"
        mock_github.get_branch_head_oid.return_value = "branch-head-oid"
        mock_github.commit_files.return_value = "commit-oid"
        mock_github.create_pull_request.return_value = {
            "id": "PR_1",
            "number": 10,
            "url": "https://github.com/o/r/pull/10",
        }
        mock_github.create_issue.return_value = {
            "id": 1,
            "node_id": "I_1",
            "number": 20,
            "html_url": "https://github.com/o/r/issues/20",
        }
        mock_github.add_issue_to_project.return_value = "item-1"

        await commit_template_to_repo(
            github_service=mock_github,
            access_token="tok",
            owner="o",
            repo="r",
            project_id="PVT_1",
            name="Bug Bash",
            template_content="---\nname: Bug Bash\n---\ncontent",
        )

        # Should have fetched the branch-specific HEAD
        mock_github.get_branch_head_oid.assert_awaited_once_with(
            "tok", "o", "r", "chore/add-template-bug-bash"
        )
        # commit_files should be called with the branch HEAD, not the default branch HEAD
        commit_call = mock_github.commit_files.call_args
        assert commit_call[0][4] == "branch-head-oid"

    @pytest.mark.anyio
    async def test_uses_default_oid_for_new_branch(self):
        """When create_branch returns a new ref ID, commit uses the default branch HEAD."""
        from unittest.mock import AsyncMock

        from src.services.chores.template_builder import commit_template_to_repo

        mock_github = AsyncMock()
        mock_github.get_repository_info.return_value = {
            "repository_id": "R_1",
            "default_branch": "main",
            "head_oid": "default-oid",
        }
        mock_github.create_branch.return_value = "ref-id-new"
        mock_github.commit_files.return_value = "commit-oid"
        mock_github.create_pull_request.return_value = {
            "id": "PR_1",
            "number": 10,
            "url": "https://github.com/o/r/pull/10",
        }
        mock_github.create_issue.return_value = {
            "id": 1,
            "node_id": "I_1",
            "number": 20,
            "html_url": "https://github.com/o/r/issues/20",
        }
        mock_github.add_issue_to_project.return_value = "item-1"

        await commit_template_to_repo(
            github_service=mock_github,
            access_token="tok",
            owner="o",
            repo="r",
            project_id="PVT_1",
            name="Bug Bash",
            template_content="---\nname: Bug Bash\n---\ncontent",
        )

        # Should NOT have fetched branch HEAD
        mock_github.get_branch_head_oid.assert_not_awaited()
        # commit_files should be called with the default branch HEAD
        commit_call = mock_github.commit_files.call_args
        assert commit_call[0][4] == "default-oid"


# =============================================================================
# Column whitelist regression (bug-bash)
# =============================================================================


class TestUpdateChoreFieldsColumnWhitelist:
    """Regression test: update_chore_fields must reject unknown column names."""

    async def test_rejects_unknown_columns(self, mock_db):
        from src.services.chores.service import ChoresService

        svc = ChoresService(mock_db)
        with pytest.raises(ValueError, match="Invalid update columns"):
            await svc.update_chore_fields("some-id", evil_column="DROP TABLE chores")

    async def test_accepts_valid_columns_used_by_callers(self, mock_db):
        """Columns actually passed by create_chore/inline_update must be accepted."""
        from src.services.chores.service import ChoresService

        svc = ChoresService(mock_db)
        # These are the exact kwargs used by the API layer (chores.py create_chore)
        # and by inline_update_chore in service.py. They must NOT be rejected.
        # If the whitelist rejects a column, update_chore_fields raises ValueError,
        # so reaching the end of this call without an exception proves acceptance.
        await svc.update_chore_fields(
            "some-id",
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            tracking_issue_number=7,
        )
