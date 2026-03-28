#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to openapi.json.

Usage:
    python3 solune/scripts/export-openapi.py [--output path]

Requires the backend to be importable (uv sync in solune/backend).
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure the backend package is importable
backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))

# Provide dummy env vars so Settings() can instantiate without real secrets.
# DEBUG=true avoids production-mode validation that requires extra secrets.
# Only the OpenAPI schema is extracted — no server is started.
_CI_PLACEHOLDERS = {
    "DEBUG": "true",
    "GITHUB_CLIENT_ID": "ci-placeholder",
    "GITHUB_CLIENT_SECRET": "ci-placeholder",
    "SESSION_SECRET_KEY": "ci-placeholder",
}
for var, default in _CI_PLACEHOLDERS.items():
    os.environ.setdefault(var, default)

from src.main import create_app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI schema")
    parser.add_argument(
        "--output",
        default=str(backend_root / "openapi.json"),
        help="Output path for the OpenAPI JSON file",
    )
    args = parser.parse_args()

    app = create_app()
    schema = app.openapi()

    output_path = Path(args.output)
    output_path.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    main()
