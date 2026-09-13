#!/usr/bin/env python3
"""Enforce the one-way dependency direction for the fork runtime.

The new ``hermes_core`` control plane may eventually adapt legacy Hermes,
but legacy Hermes must not import ``hermes_core`` before an explicitly
reviewed integration seam exists. This guard is intentionally simple and
syntax-light so it can run before the rest of the test suite.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PREFIXES = (
    ROOT / "hermes_core",
    ROOT / "tests",
)
PATTERNS = (
    re.compile(r"^\s*from\s+hermes_core(?:\.|\s)"),
    re.compile(r"^\s*import\s+hermes_core(?:\.|\s|$)"),
)


def allowed(path: Path) -> bool:
    return any(path == prefix or prefix in path.parents for prefix in ALLOWED_PREFIXES)


def main() -> int:
    violations: list[str] = []
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts or allowed(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in PATTERNS):
                violations.append(f"{path.relative_to(ROOT)}:{line_no}: {line.strip()}")

    if violations:
        print("Runtime dependency direction violation(s):")
        print("\n".join(violations))
        print("Legacy Hermes code must not depend on hermes_core outside an approved integration adapter.")
        return 1

    print("Runtime dependency direction: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
