"""Guard service — evaluates file paths against protection rules.

Implements ``@admin`` and ``@adminlock`` guard enforcement to protect
platform core files from agent modifications during app-building.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml

from src.logging_utils import get_logger
from src.models.guard import GuardResult

logger = get_logger(__name__)

# Default guard config location (relative to this file → solune/)
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "guard-config.yml"

# Cached rules (loaded lazily)
_cached_rules: list[dict[str, str]] | None = None
_cached_mtime: float = 0.0


def _load_rules(config_path: Path | None = None) -> list[dict[str, str]]:
    """Load guard rules from YAML config, with hot-reload on file change."""
    global _cached_rules, _cached_mtime

    path = config_path or _CONFIG_PATH
    if not path.exists():
        logger.warning("Guard config not found at %s — defaulting to fail-closed (admin)", path)
        return []

    mtime = path.stat().st_mtime
    if _cached_rules is not None and mtime == _cached_mtime:
        return _cached_rules

    with path.open(encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    rules: list[dict[str, str]] = data.get("guard_rules", [])
    _cached_rules = rules
    _cached_mtime = mtime
    logger.info("Loaded %d guard rules from %s", len(rules), path)
    return rules


def _match_guard_level(file_path: str, rules: list[dict[str, str]]) -> str:
    """Return the guard level for a single file path.

    Uses most-specific-match-wins logic (longest matching pattern prefix).
    Unmatched paths default to ``admin`` (fail-closed).
    """
    best_match: str = "admin"  # Default: fail-closed
    best_length: int = 0

    for rule in rules:
        pattern = rule.get("path_pattern", "")
        level = rule.get("guard_level", "admin")

        if fnmatch.fnmatch(file_path, pattern):
            # Use pattern specificity (length) as a proxy for "most specific"
            if len(pattern) >= best_length:
                best_match = level
                best_length = len(pattern)

    return best_match


def check_guard(
    file_paths: list[str],
    *,
    elevated: bool = False,
    config_path: Path | None = None,
) -> GuardResult:
    """Evaluate a list of file paths against guard rules.

    Args:
        file_paths: Paths to check (relative to repo root).
        elevated: If True, ``admin``-level blocks are bypassed
                  (``adminlock`` blocks are never bypassed).
        config_path: Override config path (for testing).

    Returns:
        ``GuardResult`` with paths categorised into allowed,
        admin_blocked, and locked lists.
    """
    rules = _load_rules(config_path)
    result = GuardResult()

    for fp in file_paths:
        level = _match_guard_level(fp, rules)

        if level == "adminlock":
            result.locked.append(fp)
        elif level == "admin":
            if elevated:
                result.allowed.append(fp)
            else:
                result.admin_blocked.append(fp)
        else:
            # "none" or any other value → allowed
            result.allowed.append(fp)

    return result


def reset_cache() -> None:
    """Clear the cached rules (useful for testing)."""
    global _cached_rules, _cached_mtime
    _cached_rules = None
    _cached_mtime = 0.0
