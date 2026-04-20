import json
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def load_schema(path: str | Path) -> dict[str, Any]:
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return schema


def load_packaged_schema() -> dict[str, Any]:
    with resources.files("macos_uninstall_inspector").joinpath("data/finding.schema.json").open("r", encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_document(document: dict[str, Any], schema: dict[str, Any]) -> None:
    Draft202012Validator(schema).validate(document)
