from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    ROOT / "docs" / "EXECUTION_OS_ARCHITECTURE.md",
    ROOT / "docs" / "completeness" / "SCREEN_COVERAGE_MATRIX.md",
    ROOT / "docs" / "completeness" / "API_COVERAGE_MATRIX.md",
    ROOT / "docs" / "completeness" / "KNOWN_GAPS_REGISTER.md",
]

BANNED_TOKENS = ["placeholder", "ui-only", "ghost button"]
SCAN_PATHS = [ROOT / "backend" / "app"]


def check_required_docs() -> list[str]:
    errors: list[str] = []
    for doc in REQUIRED_DOCS:
        if not doc.exists():
            errors.append(f"Missing required artifact: {doc.relative_to(ROOT)}")
    return errors


def check_banned_tokens() -> list[str]:
    errors: list[str] = []
    for base in SCAN_PATHS:
        for file in base.rglob("*.py"):
            text = file.read_text(encoding="utf-8")
            low = text.lower()
            for token in BANNED_TOKENS:
                if token in low:
                    errors.append(f"Banned token '{token}' found in {file.relative_to(ROOT)}")
    return errors


def main() -> int:
    errors = [*check_required_docs(), *check_banned_tokens()]
    if errors:
        print("PRE-PR GUARDRAIL CHECK: FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("PRE-PR GUARDRAIL CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
