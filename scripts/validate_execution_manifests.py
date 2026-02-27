#!/usr/bin/env python3
"""Validate legal execution manifests used by document generation."""

from __future__ import annotations

import sys
from pathlib import Path

from execution_manifests import ManifestValidationError, load_active_manifests

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        manifests = load_active_manifests(ROOT)
    except ManifestValidationError as exc:
        print("Execution manifest validation failed:", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Execution manifest validation passed ({len(manifests)} active manifests).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
