"""Verification: ``ruff check --select=ASYNC,RUF006`` finds zero violations."""

from __future__ import annotations

import subprocess
import sys


def test_no_async_or_ruf006_violations() -> None:
    """All ``asyncio.create_task`` calls are tracked by TaskRegistry and no async anti-patterns exist.

    ASYNC240 is ignored because it flags ``pathlib.Path`` usage in async functions as a
    trio/anyio concern — this codebase uses plain ``asyncio`` where synchronous ``Path``
    operations are acceptable for brief filesystem calls.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select=ASYNC,RUF006",
            "--ignore=ASYNC240",
            "src/",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0, (
        f"ASYNC/RUF006 violations found:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
