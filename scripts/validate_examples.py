#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from macos_uninstall_inspector.schema_tools import load_json, load_packaged_schema, validate_document

EXAMPLES_DIR = ROOT / "examples"


def main() -> int:
    schema = load_packaged_schema()
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
