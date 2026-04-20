from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import plistlib
import re
import subprocess


@dataclass(frozen=True)
class SearchTokens:
    exact_names: list[str]
    normalized_names: list[str]
    bundle_ids: list[str]


@dataclass(frozen=True)
class AppIdentity:
    path: Path
    display_name: str
    bundle_id: str
    executable_name: str | None
    vendor: str | None
    is_setapp: bool
    embedded_bundle_ids: list[str]
    app_groups: list[str]
    search_tokens: SearchTokens


class IdentityExtractor:
    def extract(self, app_path: str | Path) -> AppIdentity:
        app = Path(app_path)
        info = app / "Contents" / "Info.plist"
        data = plistlib.loads(info.read_bytes())

        display_name = (
            data.get("CFBundleDisplayName")
            or data.get("CFBundleName")
            or app.stem
        )
        bundle_id = data.get("CFBundleIdentifier", "")
        executable_name = data.get("CFBundleExecutable")
        vendor = None
        parts = bundle_id.split(".")
        if len(parts) >= 3:
            vendor = parts[1]

        embedded_bundle_ids = sorted((data.get("SMPrivilegedExecutables") or {}).keys())
        exact_names = [display_name]
        if executable_name and executable_name not in exact_names:
            exact_names.append(executable_name)

        normalized_names = []
        for name in exact_names:
            lowered = name.lower()
            if lowered not in normalized_names:
                normalized_names.append(lowered)
            compact = re.sub(r"[^a-z0-9]+", "", lowered)
            if compact and compact not in normalized_names:
                normalized_names.append(compact)

        bundle_ids = [bundle_id] if bundle_id else []
        app_groups = self._extract_app_groups(app, data)

        return AppIdentity(
            path=app,
            display_name=display_name,
            bundle_id=bundle_id,
            executable_name=executable_name,
            vendor=vendor,
            is_setapp=bundle_id.endswith("-setapp"),
            embedded_bundle_ids=embedded_bundle_ids,
            app_groups=app_groups,
            search_tokens=SearchTokens(
                exact_names=exact_names,
                normalized_names=normalized_names,
                bundle_ids=bundle_ids,
            ),
        )

    def _extract_app_groups(self, app: Path, info: dict) -> list[str]:
        groups: list[str] = []

        def add(values: object) -> None:
            if isinstance(values, list):
                for value in values:
                    if (
                        isinstance(value, str)
                        and value
                        and self._is_valid_app_group(value)
                        and value not in groups
                    ):
                        groups.append(value)

        add(info.get("com.apple.security.application-groups"))

        for candidate in [
            app / "Contents" / "Entitlements.plist",
            app / "Contents" / "Resources" / "Entitlements.plist",
        ]:
            if not candidate.exists():
                continue
            try:
                payload = plistlib.loads(candidate.read_bytes())
            except Exception:
                continue
            add(payload.get("com.apple.security.application-groups"))

        try:
            results = [
                subprocess.run(
                    ["codesign", "-d", "--entitlements", "-", str(app)],
                    capture_output=True,
                    check=False,
                ),
                subprocess.run(
                    ["codesign", "-d", "--entitlements", ":-", str(app)],
                    capture_output=True,
                    check=False,
                ),
            ]
        except FileNotFoundError:
            results = []
        for result in results:
            for blob in [result.stdout, result.stderr]:
                if not blob:
                    continue
                add(self._extract_app_groups_from_codesign_blob(blob))

        return sorted(groups)

    def _extract_app_groups_from_codesign_blob(self, blob: bytes) -> list[str]:
        start = blob.find(b"<?xml")
        if start != -1:
            try:
                payload = plistlib.loads(blob[start:])
            except Exception:
                payload = None
            if isinstance(payload, dict):
                values = payload.get("com.apple.security.application-groups")
                if isinstance(values, list):
                    return [value for value in values if isinstance(value, str)]

        groups: list[str] = []
        capture = False
        for raw_line in blob.decode("utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if line == "[Key] com.apple.security.application-groups":
                capture = True
                continue
            if capture and line.startswith("[Key] "):
                break
            if capture and line.startswith("[String] "):
                groups.append(line.removeprefix("[String] ").strip())
        return groups

    def _is_valid_app_group(self, value: str) -> bool:
        return re.fullmatch(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value) is not None
