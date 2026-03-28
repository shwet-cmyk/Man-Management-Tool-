"""Generate API endpoint inventory grouped by module using static source parsing.

Usage:
  python backend/scripts/api_module_inventory.py --format markdown
  python backend/scripts/api_module_inventory.py --format json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAIN_FILE = ROOT / "app" / "main.py"
MODULES_DIR = ROOT / "app" / "modules"

IMPORT_RE = re.compile(r"from app\.modules\.([a-zA-Z0-9_]+)\.router import router as ([a-zA-Z0-9_]+)")
INCLUDE_RE = re.compile(r"app\.include_router\(([a-zA-Z0-9_]+),\s*prefix=\"([^\"]+)\"\)")
ROUTER_PREFIX_RE = re.compile(r"router\s*=\s*APIRouter\(.*prefix=\"([^\"]*)\"")
DECORATOR_RE = re.compile(r"@router\.(get|post|put|delete|patch)\(\"([^\"]*)\"")
DEF_RE = re.compile(r"def\s+([a-zA-Z0-9_]+)\(")


def parse_main() -> tuple[dict[str, str], dict[str, list[str]]]:
    text = MAIN_FILE.read_text(encoding="utf-8")

    alias_to_module: dict[str, str] = {}
    for module, alias in IMPORT_RE.findall(text):
        alias_to_module[alias] = module

    module_prefixes: dict[str, list[str]] = defaultdict(list)
    for alias, prefix in INCLUDE_RE.findall(text):
        module = alias_to_module.get(alias)
        if not module:
            continue
        if prefix not in module_prefixes[module]:
            module_prefixes[module].append(prefix)

    return alias_to_module, module_prefixes


def parse_router(module: str) -> tuple[str, list[dict[str, str]]]:
    router_file = MODULES_DIR / module / "router.py"
    text = router_file.read_text(encoding="utf-8")

    router_prefix_match = ROUTER_PREFIX_RE.search(text)
    router_prefix = router_prefix_match.group(1) if router_prefix_match else ""

    lines = text.splitlines()
    routes: list[dict[str, str]] = []

    for idx, line in enumerate(lines):
        deco = DECORATOR_RE.search(line)
        if not deco:
            continue

        method = deco.group(1).upper()
        path = deco.group(2)
        handler = "<unknown>"

        for j in range(idx + 1, min(idx + 7, len(lines))):
            d = DEF_RE.search(lines[j])
            if d:
                handler = d.group(1)
                break

        routes.append({"method": method, "path": path, "handler": handler})

    return router_prefix, routes


def join_paths(*parts: str) -> str:
    normalized = []
    for part in parts:
        if not part:
            continue
        normalized.append(part.strip("/"))
    return "/" + "/".join(p for p in normalized if p)


def build_inventory() -> dict[str, list[dict[str, Any]]]:
    _, module_prefixes = parse_main()
    inventory: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for module in sorted(module_prefixes.keys()):
        router_prefix, routes = parse_router(module)

        expanded: list[dict[str, Any]] = []
        for app_prefix in module_prefixes[module]:
            for route in routes:
                full_path = join_paths(app_prefix, router_prefix, route["path"])
                expanded.append(
                    {
                        "method": route["method"],
                        "path": full_path,
                        "handler": route["handler"],
                    }
                )

        inventory[module] = sorted(expanded, key=lambda x: (x["path"], x["method"]))

    return dict(inventory)


def as_markdown(inventory: dict[str, list[dict[str, Any]]]) -> str:
    lines: list[str] = [
        "# API Endpoint Inventory by Module",
        "",
        "Generated via static parsing of `backend/app/main.py` and each module `router.py`.",
        "",
    ]

    for module, rows in inventory.items():
        lines.append(f"## {module}")
        lines.append("")
        lines.append("| Method | Path | Handler |")
        lines.append("|---|---|---|")
        for row in rows:
            lines.append(f"| `{row['method']}` | `{row['path']}` | `{row['handler']}` |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate API endpoint inventory by module")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    inventory = build_inventory()

    if args.format == "json":
        print(json.dumps(inventory, indent=2))
        return

    print(as_markdown(inventory))


if __name__ == "__main__":
    main()
