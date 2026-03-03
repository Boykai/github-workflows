"""Unit tests for ChoresService and template builder."""

from __future__ import annotations

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


# =============================================================================
# ChoresService.trigger_chore
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
