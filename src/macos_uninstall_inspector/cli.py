from __future__ import annotations

import argparse
import json
from pathlib import Path

from .inspector import Inspector
from .runtime import RuntimeContextCollector
from .schema_tools import load_json, load_packaged_schema, validate_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mui")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a macOS app bundle")
    inspect_parser.add_argument("app_path")
    inspect_parser.add_argument("--context", dest="context_path")
    inspect_parser.add_argument("--mode", choices=["safe", "balanced", "aggressive"])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        provided_context = load_json(args.context_path) if args.context_path else {}
        identity_context = RuntimeContextCollector().collect(Inspector().identity_extractor.extract(args.app_path))
        context = dict(identity_context)
        context.update(provided_context)
        report = Inspector().inspect(args.app_path, context=context)
        payload = report.to_document()
        if args.mode:
            payload["candidates"] = [
                candidate for candidate in payload["candidates"] if args.mode in candidate["modes"]
            ]
        schema = load_packaged_schema()
        validate_document(payload, schema)
        print(json.dumps(payload, indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
