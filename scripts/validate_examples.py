#!/usr/bin/env python3
import sys
from pathlib import Path

from macos_uninstall_inspector.schema_tools import load_json, load_schema, validate_document

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "finding.schema.json"
EXAMPLES_DIR = ROOT / "examples"


def main() -> int:
    schema = load_schema(SCHEMA_PATH)
    checked = 0
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        if path.name.startswith("invalid-"):
            continue
        validate_document(load_json(path), schema)
        checked += 1
        print(f"validated: {path.name}")
    print(f"validated {checked} example(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
