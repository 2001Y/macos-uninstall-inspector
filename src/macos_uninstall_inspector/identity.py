from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import plistlib
import re


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

        return AppIdentity(
            path=app,
            display_name=display_name,
            bundle_id=bundle_id,
            executable_name=executable_name,
            vendor=vendor,
            is_setapp=bundle_id.endswith("-setapp"),
            embedded_bundle_ids=embedded_bundle_ids,
            search_tokens=SearchTokens(
                exact_names=exact_names,
                normalized_names=normalized_names,
                bundle_ids=bundle_ids,
            ),
        )
