#!/usr/bin/env python3
"""scripts/generate-constants.py — Extract constants from Python to TypeScript.

Reads a Python constants module, extracts UPPERCASE assignments and class
namespaces (e.g. StatusNames), and writes TypeScript ``export const`` declarations.

Handles annotated assignments (``X: str = "v"``), class attribute namespaces,
and values that reference class attributes (``StatusNames.BACKLOG``).
"""

import ast
import argparse
import json
from pathlib import Path

_UNRESOLVED = object()


def _resolve_node(
    node: ast.expr,
    class_values: dict[str, dict[str, object]],
) -> object:
    """Resolve an AST node to a Python value.

    Tries ``ast.literal_eval`` first, then falls back to resolving class
    attribute references (e.g. ``StatusNames.BACKLOG``) using *class_values*.
    """
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        pass

    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        cls_attrs = class_values.get(node.value.id)
        if cls_attrs and node.attr in cls_attrs:
            return cls_attrs[node.attr]

    elif isinstance(node, ast.List):
        items = [_resolve_node(e, class_values) for e in node.elts]
        if _UNRESOLVED not in items:
            return items

    elif isinstance(node, ast.Tuple):
        items = [_resolve_node(e, class_values) for e in node.elts]
        if _UNRESOLVED not in items:
            return items

    elif isinstance(node, ast.Dict):
        keys: list[object] = []
        vals: list[object] = []
        for k, v in zip(node.keys, node.values):
            if k is None:
                return _UNRESOLVED  # ** spread — not supported
            rk = _resolve_node(k, class_values)
            rv = _resolve_node(v, class_values)
            if rk is _UNRESOLVED or rv is _UNRESOLVED:
                return _UNRESOLVED
            keys.append(rk)
            vals.append(rv)
        return dict(zip(keys, vals))

    return _UNRESOLVED


def _extract_target(node: ast.stmt) -> tuple[ast.expr | None, ast.expr | None]:
    """Return (name_node, value_node) for Assign or AnnAssign, else (None, None)."""
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.targets[0], node.value
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return node.target, node.value
    return None, None


def extract_constants(source: str) -> list[tuple[str, str]]:
    """Parse Python source and extract UPPERCASE constants and class namespaces."""
    tree = ast.parse(source)
    constants: list[tuple[str, str]] = []
    class_values: dict[str, dict[str, object]] = {}

    # Pass 1: class definitions → const object namespaces
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        attrs: dict[str, object] = {}
        for item in node.body:
            name_node, value_node = _extract_target(item)
            if (
                name_node
                and value_node
                and isinstance(name_node, ast.Name)
                and not name_node.id.startswith("_")
            ):
                try:
                    attrs[name_node.id] = ast.literal_eval(value_node)
                except (ValueError, TypeError):
                    pass
        if attrs:
            class_values[node.name] = attrs
            constants.append((node.name, json.dumps(attrs)))

    # Pass 2: top-level UPPERCASE assignments
    for node in ast.iter_child_nodes(tree):
        name_node, value_node = _extract_target(node)
        if not (
            name_node
            and value_node
            and isinstance(name_node, ast.Name)
            and name_node.id.isupper()
        ):
            continue
        value = _resolve_node(value_node, class_values)
        if value is _UNRESOLVED:
            continue
        try:
            constants.append((name_node.id, json.dumps(value)))
        except (TypeError, ValueError):
            pass  # skip non-serialisable values

    return constants


def generate_typescript(constants: list[tuple[str, str]]) -> str:
    """Generate TypeScript ``export const`` declarations."""
    lines = [
        "/* eslint-disable */",
        "/* This file is auto-generated from backend/src/constants.py */",
        "/* Run: npm run generate:types */",
        "",
    ]
    for name, value in constants:
        lines.append(f"export const {name} = {value} as const;")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate TypeScript constants from a Python constants module.",
    )
    parser.add_argument("--input", required=True, help="Path to Python constants file")
    parser.add_argument("--output", required=True, help="Path to write TypeScript file")
    args = parser.parse_args()

    source = Path(args.input).read_text()
    constants = extract_constants(source)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(generate_typescript(constants))
    print(f"Generated {len(constants)} constants \u2192 {args.output}")


if __name__ == "__main__":
    main()
