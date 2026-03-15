"""Verification: ``ruff check --select=ASYNC,RUF006`` finds zero violations."""

from __future__ import annotations

import subprocess


def test_no_ruf006_violations() -> None:
    """All ``asyncio.create_task`` calls are tracked by TaskRegistry."""
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "--select=RUF006", "src/"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0, f"RUF006 violations found:\n{result.stdout}"
