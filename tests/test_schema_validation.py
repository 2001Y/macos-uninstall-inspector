import json
from pathlib import Path

import pytest

from macos_uninstall_inspector.schema_tools import load_packaged_schema, validate_document

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def read_json(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text())


def test_valid_homebrew_example_conforms():
    schema = load_packaged_schema()
    validate_document(read_json("homebrew-claude.json"), schema)


def test_valid_vendor_suite_example_conforms():
    schema = load_packaged_schema()
    validate_document(read_json("adobe-creative-cloud.json"), schema)


def test_invalid_example_is_rejected():
    schema = load_packaged_schema()
    with pytest.raises(Exception):
        validate_document(read_json("invalid-missing-distribution-kind.json"), schema)
