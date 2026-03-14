"""Tests for clean module boundaries (US8 — FR-015, SC-006).

T038: Verify no cross-module private attribute access using grep analysis.
"""

import re
import subprocess
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parent.parent.parent / "src"

# Patterns that indicate cross-module private access:
# - accessing ._client on a service object from api/ or copilot_polling/
# - calling ._private_method on an object imported from another package
FORBIDDEN_PATTERNS = [
    # Direct httpx client access from outside github_projects
    (r"github_projects_service\._client\b", "Direct _client access on GitHubProjectsService"),
    # Private method access from copilot_polling into github_projects
    (r"github_projects_service\._check_copilot", "Private method access across module boundary"),
]


class TestModuleBoundaries:
    """Cross-module private attribute access is forbidden (SC-006)."""

    @pytest.mark.parametrize("pattern,description", FORBIDDEN_PATTERNS)
    def test_no_cross_module_private_access(self, pattern: str, description: str):
        """Grep the source tree for forbidden cross-module private access patterns."""
        result = subprocess.run(
            ["grep", "-rn", "-E", pattern, str(BACKEND_SRC)],
            capture_output=True,
            text=True,
        )
        violations = result.stdout.strip()
        if violations:
            # Filter out test files and __pycache__
            real_violations = [
                line
                for line in violations.splitlines()
                if "__pycache__" not in line and "/tests/" not in line
            ]
            assert not real_violations, f"Found forbidden pattern ({description}):\n" + "\n".join(
                real_violations
            )

    def test_no_private_attr_access_in_api_layer(self):
        """API modules (src/api/) must not access private attrs of service objects."""
        api_dir = BACKEND_SRC / "api"
        violations = []
        # Match patterns like `some_service._anything` but NOT `self._anything`
        pattern = re.compile(r"(?<!self)\.\s*_[a-z]\w*\b")

        for py_file in api_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), start=1):
                # Skip comments and self-access
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "self._" in line:
                    continue
                if "__init__" in line or "__name__" in line or "__all__" in line:
                    continue
                matches = pattern.findall(line)
                for m in matches:
                    attr = m.strip().lstrip(".")
                    # Allow known standard library / FastAPI privates
                    if attr in ("_get_session_dep", "_env_file"):
                        continue
                    violations.append(f"{py_file.name}:{i}: {line.strip()}")

        assert not violations, "API layer accesses private attributes:\n" + "\n".join(violations)
