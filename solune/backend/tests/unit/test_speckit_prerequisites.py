"""Regression tests for Speckit prerequisite handling on Copilot branches."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE_SCRIPTS_DIR = REPO_ROOT / ".specify" / "scripts" / "bash"


def _init_test_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    scripts_dir = repo / ".specify" / "scripts" / "bash"
    feature_dir = repo / "specs" / "001-bug-basher"

    scripts_dir.mkdir(parents=True)
    feature_dir.mkdir(parents=True)

    shutil.copy2(SOURCE_SCRIPTS_DIR / "check-prerequisites.sh", scripts_dir / "check-prerequisites.sh")
    shutil.copy2(SOURCE_SCRIPTS_DIR / "common.sh", scripts_dir / "common.sh")

    (feature_dir / "spec.md").write_text("# Spec\n")
    (feature_dir / "plan.md").write_text("# Plan\n")
    (feature_dir / "tasks.md").write_text("# Tasks\n")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "copilot/test-analyze"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    return repo


def test_check_prerequisites_guides_copilot_branches_to_specify_feature(tmp_path: Path) -> None:
    repo = _init_test_repo(tmp_path)

    result = subprocess.run(
        [
            "bash",
            ".specify/scripts/bash/check-prerequisites.sh",
            "--json",
            "--require-tasks",
            "--include-tasks",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Current branch: copilot/test-analyze" in result.stderr
    assert "set SPECIFY_FEATURE" in result.stderr
    assert "SPECIFY_FEATURE=001-my-feature" in result.stderr


def test_check_prerequisites_accepts_specify_feature_on_copilot_branches(tmp_path: Path) -> None:
    repo = _init_test_repo(tmp_path)

    env = os.environ.copy()
    env["SPECIFY_FEATURE"] = "001-bug-basher"
    result = subprocess.run(
        [
            "bash",
            ".specify/scripts/bash/check-prerequisites.sh",
            "--json",
            "--require-tasks",
            "--include-tasks",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["FEATURE_DIR"] == str(repo / "specs" / "001-bug-basher")
    assert "tasks.md" in payload["AVAILABLE_DOCS"]
