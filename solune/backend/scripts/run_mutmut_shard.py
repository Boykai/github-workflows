#!/usr/bin/env python3
"""Run mutmut against a scoped subset of backend service paths."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SHARDS: dict[str, list[str]] = {
    "auth-and-projects": [
        "src/services/github_auth.py",
        "src/services/completion_providers.py",
        "src/services/model_fetcher.py",
        "src/services/github_projects/",
    ],
    "orchestration": [
        "src/services/workflow_orchestrator/",
        "src/services/pipelines/",
        "src/services/copilot_polling/",
        "src/services/task_registry.py",
        "src/services/pipeline_state_store.py",
        "src/services/agent_tracking.py",
    ],
    "app-and-data": [
        "src/services/app_service.py",
        "src/services/guard_service.py",
        "src/services/metadata_service.py",
        "src/services/cache.py",
        "src/services/database.py",
        "src/services/done_items_store.py",
        "src/services/chat_store.py",
        "src/services/session_store.py",
        "src/services/settings_store.py",
        "src/services/mcp_store.py",
        "src/services/cleanup_service.py",
        "src/services/encryption.py",
        "src/services/websocket.py",
    ],
    "agents-and-integrations": [
        "src/services/ai_agent.py",
        "src/services/agent_creator.py",
        "src/services/github_commit_workflow.py",
        "src/services/signal_bridge.py",
        "src/services/signal_chat.py",
        "src/services/signal_delivery.py",
        "src/services/tools/",
        "src/services/agents/",
        "src/services/chores/",
    ],
    "api-and-middleware": [
        "src/api/",
        "src/middleware/",
        "src/utils.py",
    ],
}


def _build_paths_block(paths: list[str]) -> str:
    if len(paths) == 1:
        return f'paths_to_mutate = ["{paths[0]}"]'

    items = "\n".join(f'    "{path}",' for path in paths)
    return f"paths_to_mutate = [\n{items}\n]"


def _replace_paths_to_mutate(pyproject_text: str, paths: list[str]) -> str:
    pattern = re.compile(r"^paths_to_mutate\s*=\s*\[[^\]]*\]", re.MULTILINE | re.DOTALL)
    replacement = _build_paths_block(paths)
    updated_text, count = pattern.subn(replacement, pyproject_text, count=1)
    if count != 1:
        raise RuntimeError("Could not find [tool.mutmut].paths_to_mutate in pyproject.toml")
    return updated_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", choices=sorted(SHARDS), help="Named mutmut shard to run")
    parser.add_argument("--max-children", type=int, default=1, help="mutmut worker count")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected shard paths and exit without running mutmut",
    )
    args = parser.parse_args()

    if not args.shard:
        parser.error("--shard is required")

    paths = SHARDS[args.shard]
    if args.dry_run:
        print(args.shard)
        for path in paths:
            print(path)
        return 0

    backend_dir = Path(__file__).resolve().parent.parent
    pyproject_path = backend_dir / "pyproject.toml"
    original_text = pyproject_path.read_text()
    patched_text = _replace_paths_to_mutate(original_text, paths)

    try:
        pyproject_path.write_text(patched_text)
        command = [sys.executable, "-m", "mutmut", "run", "--max-children", str(args.max_children)]
        completed = subprocess.run(command, cwd=backend_dir)
        return completed.returncode
    finally:
        pyproject_path.write_text(original_text)


if __name__ == "__main__":
    raise SystemExit(main())
