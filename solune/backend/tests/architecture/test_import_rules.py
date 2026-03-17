"""Architecture boundary tests — enforce import direction rules via AST analysis."""

import ast
import typing
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src"

# Known pre-existing violations that are permitted (add sparingly)
ALLOWLIST: set[tuple[str, str]] = {
    # services → api: signal integration bridges back into chat API
    ("src/services/signal_bridge.py", "src.api.chat"),
    ("src/services/signal_chat.py", "src.api.chat"),
}


def _extract_imports(filepath: Path) -> list[str]:
    """Parse a Python file and return all imported module names."""
    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def _relative_key(filepath: Path) -> str:
    """Return a relative path key like 'src/services/foo.py'."""
    return str(filepath.relative_to(SRC_ROOT.parent))


class TestServicesBoundary:
    """services/ must never import from api/."""

    def test_services_do_not_import_api(self) -> None:
        services_dir = SRC_ROOT / "services"
        if not services_dir.exists():
            pytest.skip("services/ directory not found")

        violations: list[str] = []
        for py_file in services_dir.rglob("*.py"):
            rel = _relative_key(py_file)
            for mod in _extract_imports(py_file):
                if "api" in mod.split(".") or mod.startswith("src.api"):
                    if (rel, mod) in ALLOWLIST:
                        continue
                    violations.append(f"{rel} imports {mod}")

        assert violations == [], (
            "services/ must not import from api/. Violations:\n  " + "\n  ".join(violations)
        )


class TestApiBoundary:
    """api/ must not import *_store modules directly."""

    # Pre-existing api → _store imports (legacy; do not add new ones)
    _API_STORE_ALLOWLIST: typing.ClassVar[set[tuple[str, str]]] = {
        ("src/api/mcp.py", "src.services.mcp_store"),
        ("src/api/chat.py", "src.services.settings_store"),
        ("src/api/chat.py", "src.services.chat_store"),
        ("src/api/settings.py", "src.services.settings_store"),
        ("src/api/board.py", "src.services.done_items_store"),
        ("src/api/pipelines.py", "src.services.settings_store"),
        ("src/api/projects.py", "src.services.done_items_store"),
        ("src/api/workflow.py", "src.services.settings_store"),
        ("src/api/workflow.py", "src.services.chat_store"),
    }

    def test_api_does_not_import_store_modules(self) -> None:
        api_dir = SRC_ROOT / "api"
        if not api_dir.exists():
            pytest.skip("api/ directory not found")

        violations: list[str] = []
        for py_file in api_dir.rglob("*.py"):
            rel = _relative_key(py_file)
            for mod in _extract_imports(py_file):
                if "_store" in mod:
                    if (rel, mod) in self._API_STORE_ALLOWLIST:
                        continue
                    violations.append(f"{rel} imports {mod}")

        assert violations == [], (
            "api/ must not import *_store modules directly. Violations:\n  "
            + "\n  ".join(violations)
        )


class TestModelsBoundary:
    """models/ must never import from services/."""

    def test_models_do_not_import_services(self) -> None:
        models_dir = SRC_ROOT / "models"
        if not models_dir.exists():
            pytest.skip("models/ directory not found")

        violations: list[str] = []
        for py_file in models_dir.rglob("*.py"):
            rel = _relative_key(py_file)
            violations.extend(
                f"{rel} imports {mod}"
                for mod in _extract_imports(py_file)
                if "services" in mod.split(".") or mod.startswith("src.services")
            )

        assert violations == [], (
            "models/ must not import from services/. Violations:\n  " + "\n  ".join(violations)
        )
