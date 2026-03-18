"""Unit tests for the template file reader (solune/backend/src/services/template_files.py)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.template_files import (
    GENERIC_COPILOT_INSTRUCTIONS,
    build_template_files,
    clear_template_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Ensure template cache is cleared before each test."""
    clear_template_cache()
    yield  # type: ignore[misc]
    clear_template_cache()


def _make_template_tree(tmp_path: Path) -> Path:
    """Create a minimal template directory structure for testing."""
    gh_dir = tmp_path / ".github"
    gh_dir.mkdir()
    (gh_dir / "CODEOWNERS").write_text("* @team\n")
    (gh_dir / "copilot-instructions.md").write_text("PROJECT-SPECIFIC CONTENT\n")

    spec_dir = tmp_path / ".specify"
    spec_dir.mkdir()
    (spec_dir / "constitution.md").write_text("# Constitution\n")

    (tmp_path / ".gitignore").write_text("node_modules/\n")
    return tmp_path


class TestBuildTemplateFiles:
    @pytest.mark.asyncio
    async def test_reads_files_from_source_dir(self, tmp_path: Path) -> None:
        source = _make_template_tree(tmp_path)
        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": str(source)}):
            files, warnings = await build_template_files("my-app", "My App")

        paths = {f["path"] for f in files}
        assert ".github/CODEOWNERS" in paths
        assert ".specify/constitution.md" in paths
        assert ".gitignore" in paths
        assert warnings == []

    @pytest.mark.asyncio
    async def test_replaces_copilot_instructions_with_generic(self, tmp_path: Path) -> None:
        source = _make_template_tree(tmp_path)
        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": str(source)}):
            files, _warnings = await build_template_files("my-app", "My App")

        copilot_file = next(f for f in files if f["path"].endswith("copilot-instructions.md"))
        assert copilot_file["content"] == GENERIC_COPILOT_INSTRUCTIONS
        assert "PROJECT-SPECIFIC" not in copilot_file["content"]

    @pytest.mark.asyncio
    async def test_caches_files_after_first_call(self, tmp_path: Path) -> None:
        source = _make_template_tree(tmp_path)
        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": str(source)}):
            first_call, _ = await build_template_files("a", "A")
            # Mutate the source dir — cached result should be returned
            (source / ".github" / "extra.md").write_text("extra\n")
            second_call, _ = await build_template_files("b", "B")

        assert len(first_call) == len(second_call)
        # "extra.md" was written AFTER cache, so it should NOT appear
        second_paths = {f["path"] for f in second_call}
        assert ".github/extra.md" not in second_paths

    @pytest.mark.asyncio
    async def test_skips_symlinks(self, tmp_path: Path) -> None:
        source = _make_template_tree(tmp_path)
        # Create a symlink inside .github/
        target = tmp_path / "secret.txt"
        target.write_text("secret\n")
        symlink = source / ".github" / "linked.md"
        symlink.symlink_to(target)

        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": str(source)}):
            files, _warnings = await build_template_files("x", "X")

        paths = {f["path"] for f in files}
        assert ".github/linked.md" not in paths

    @pytest.mark.asyncio
    async def test_returns_empty_for_missing_dir(self) -> None:
        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": "/nonexistent/path"}):
            files, warnings = await build_template_files("x", "X")
        assert files == []
        assert warnings == []

    @pytest.mark.asyncio
    async def test_path_traversal_rejection(self, tmp_path: Path) -> None:
        """Paths that escape the source directory should be rejected."""
        source = _make_template_tree(tmp_path)
        # Create a .github file with a path-traversal name — this is a filesystem
        # concern: we verify that _is_safe_path rejects symlinks pointing outside.
        outside = tmp_path.parent / "outside.txt"
        outside.write_text("escaped\n")
        evil_link = source / ".github" / "evil"
        evil_link.symlink_to(outside)

        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": str(source)}):
            files, _warnings = await build_template_files("x", "X")

        paths = {f["path"] for f in files}
        assert ".github/evil" not in paths

    @pytest.mark.asyncio
    async def test_unreadable_file_produces_warning(self, tmp_path: Path) -> None:
        """Files that cannot be read should produce warnings, not be silently skipped."""
        source = _make_template_tree(tmp_path)
        # Create a file that will fail to read — make it a binary file
        bad_file = source / ".github" / "binary.dat"
        bad_file.write_bytes(b"\x80\x81\x82\x83")

        with patch.dict(os.environ, {"TEMPLATE_SOURCE_DIR": str(source)}):
            files, warnings = await build_template_files("x", "X")

        paths = {f["path"] for f in files}
        assert ".github/binary.dat" not in paths
        assert len(warnings) == 1
        assert ".github/binary.dat" in warnings[0]


class TestGenericCopilotInstructions:
    def test_contains_todo_sections(self) -> None:
        assert "## Tech Stack" in GENERIC_COPILOT_INSTRUCTIONS
        assert "## Coding Conventions" in GENERIC_COPILOT_INSTRUCTIONS
        assert "## Testing" in GENERIC_COPILOT_INSTRUCTIONS
        assert "## Deployment" in GENERIC_COPILOT_INSTRUCTIONS
        assert "TODO" in GENERIC_COPILOT_INSTRUCTIONS

    def test_mentions_solune(self) -> None:
        assert "Solune" in GENERIC_COPILOT_INSTRUCTIONS
