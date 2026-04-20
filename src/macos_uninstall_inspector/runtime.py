from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

from .identity import AppIdentity


CommandRunner = Callable[[list[str]], str]


def receipt_matches_identity(receipt_id: str, bundle_id: str) -> bool:
    receipt_parts = receipt_id.lower().split(".")
    bundle_parts = bundle_id.lower().split(".")
    if receipt_id.lower() == bundle_id.lower():
        return True
    for window in range(min(len(bundle_parts), len(receipt_parts)), 2, -1):
        if receipt_parts[-window:] == bundle_parts[-window:]:
            return True
    return False


class RuntimeContextCollector:
    def __init__(self, command_runner: CommandRunner | None = None) -> None:
        self.command_runner = command_runner or self._run

    def collect(self, identity: AppIdentity) -> dict:
        homebrew_casks = self._collect_homebrew_casks(identity)
        pkg_receipts = self._collect_pkg_receipts(identity)
        return {
            "homebrew_casks": homebrew_casks,
            "pkg_receipts": pkg_receipts,
        }

    def _collect_homebrew_casks(self, identity: AppIdentity) -> dict[str, str]:
        results: dict[str, str] = {}
        output = self.command_runner(["brew", "list", "--cask"])
        tokens = [line.strip() for line in output.splitlines() if line.strip()]
        app_name = identity.path.name
        for token in tokens:
            raw = self.command_runner(["brew", "info", "--cask", "--json=v2", token])
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for cask in data.get("casks", []):
                for artifact in cask.get("artifacts", []):
                    if isinstance(artifact, dict) and "app" in artifact:
                        app_entries = artifact["app"]
                        if isinstance(app_entries, list) and app_entries:
                            source_name = app_entries[0] if isinstance(app_entries[0], str) else None
                            target_name = None
                            for entry in app_entries[1:]:
                                if isinstance(entry, dict) and entry.get("target"):
                                    target_name = entry["target"]
                            if app_name in {source_name, target_name}:
                                results[identity.bundle_id] = cask.get("full_token") or cask["token"]
                    elif isinstance(artifact, list) and len(artifact) >= 2 and artifact[0] == "app":
                        if artifact[1] == app_name:
                            results[identity.bundle_id] = cask["token"]
        return results

    def _collect_pkg_receipts(self, identity: AppIdentity) -> dict[str, list[str]]:
        output = self.command_runner(["pkgutil", "--pkgs"])
        receipts = []
        for line in output.splitlines():
            value = line.strip()
            if not value:
                continue
            if receipt_matches_identity(value, identity.bundle_id):
                receipts.append(value)
        return {identity.bundle_id: receipts} if receipts else {}

    @staticmethod
    def _run(command: list[str]) -> str:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            return ""
        return result.stdout
