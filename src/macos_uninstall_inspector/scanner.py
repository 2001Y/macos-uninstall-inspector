from __future__ import annotations

from pathlib import Path
import plistlib
import re

from .identity import AppIdentity


class ConventionalScanner:
    def __init__(self, home: str | Path | None = None, system_root: str | Path = "/Library") -> None:
        self.home = Path(home).expanduser() if home else Path.home()
        self.system_root = Path(system_root)

    def scan(self, identity: AppIdentity) -> list[dict]:
        findings: list[dict] = []

        findings.extend(self._scan_embedded(identity))
        findings.extend(self._scan_library_state(identity))
        findings.extend(self._scan_system_integrations(identity))
        findings.extend(self._scan_vendor_shared(identity))

        unique: dict[str, dict] = {}
        for finding in findings:
            current = unique.get(finding["path"])
            if current is None:
                unique[finding["path"]] = {
                    "path": finding["path"],
                    "evidence": list(dict.fromkeys(finding["evidence"])),
                }
            else:
                current["evidence"] = list(
                    dict.fromkeys(current["evidence"] + finding["evidence"])
                )
        return list(unique.values())

    def _scan_embedded(self, identity: AppIdentity) -> list[dict]:
        results = []
        embedded_locations = {
            Path("Contents/Library/LoginItems"): {
                "evidence": ["login_item_embedded"],
                "accept": lambda child: child.is_dir() and child.suffix == ".app",
            },
            Path("Contents/Library/SystemExtensions"): {
                "evidence": ["system_extension_embedded"],
                "accept": lambda child: child.is_dir() and child.suffix == ".systemextension",
            },
            Path("Contents/Library/Helpers"): {
                "evidence": ["bundle_path_exact", "embedded_helper_path"],
                "accept": lambda child: True,
            },
            Path("Contents/Helpers"): {
                "evidence": ["bundle_path_exact", "embedded_helper_path"],
                "accept": lambda child: True,
            },
            Path("Contents/XPCServices"): {
                "evidence": ["bundle_path_exact", "embedded_helper_path"],
                "accept": lambda child: True,
            },
            Path("Contents/PlugIns"): {
                "evidence": ["bundle_path_exact", "embedded_helper_path"],
                "accept": lambda child: True,
            },
        }
        for relative, config in embedded_locations.items():
            base = identity.path / relative
            if base.exists():
                for child in sorted(base.iterdir()):
                    if not config["accept"](child):
                        continue
                    results.append(
                        {
                            "path": str(child),
                            "evidence": config["evidence"],
                        }
                    )
        return results

    def _scan_library_state(self, identity: AppIdentity) -> list[dict]:
        targets = [
            self.home / "Library" / "Preferences" / f"{identity.bundle_id}.plist",
            self.home / "Library" / "Caches" / identity.bundle_id,
            self.home / "Library" / "Containers" / identity.bundle_id,
            self.home / "Library" / "Saved Application State" / f"{identity.bundle_id}.savedState",
            self.home / "Library" / "Logs" / identity.display_name,
        ]
        for group_id in identity.app_groups:
            targets.extend(
                [
                    self.home / "Library" / "Group Containers" / group_id,
                    self.home / "Library" / "Application Scripts" / group_id,
                ]
            )
        for bundle_token in [identity.bundle_id, *identity.embedded_bundle_ids]:
            if bundle_token:
                targets.append(self.home / "Library" / "Application Scripts" / bundle_token)
        results = []
        for path in targets:
            if path.exists():
                evidence = ["bundle_id_exact"]
                if "Group Containers" in path.parts:
                    evidence = ["app_group_entitlement_exact", "group_container_exact"]
                elif "Application Scripts" in path.parts and path.name in identity.app_groups:
                    evidence = ["app_group_entitlement_exact", "application_scripts_exact"]
                elif "Application Scripts" in path.parts:
                    evidence = ["bundle_id_exact", "application_scripts_exact"]
                if "Preferences" in path.parts:
                    evidence.append("preferences_conventional_path")
                elif "Logs" in path.parts:
                    evidence.append("logs_conventional_path")
                    evidence.append("app_name_exact")
                elif evidence == ["bundle_id_exact"]:
                    evidence.append("bundle_path_exact")
                results.append({"path": str(path), "evidence": evidence})
        return results

    def _scan_system_integrations(self, identity: AppIdentity) -> list[dict]:
        results = []
        launchd_roots = [
            self.home / "Library" / "LaunchAgents",
            self._system_subpath("LaunchAgents"),
            self._system_subpath("LaunchDaemons"),
        ]
        launchd_tokens = self._launchd_tokens(identity)
        for root in launchd_roots:
            if not root.exists():
                continue
            for path in sorted(root.glob("*.plist")):
                evidence = self._match_launchd_plist(path, launchd_tokens)
                if evidence:
                    results.append({"path": str(path), "evidence": evidence})

        helper_root = self._system_subpath("PrivilegedHelperTools")
        if helper_root.exists():
            bundle_token = identity.bundle_id.lower()
            helper_tokens = {token.lower() for token in identity.embedded_bundle_ids if token}
            for path in sorted(helper_root.iterdir()):
                path_name = path.name.lower()
                evidence = []
                if bundle_token and bundle_token in path_name:
                    evidence.append("privileged_helper_exact")
                if path_name in helper_tokens:
                    evidence.append("embedded_helper_id_exact")
                if evidence:
                    results.append({"path": str(path), "evidence": evidence})
        return results

    def _launchd_tokens(self, identity: AppIdentity) -> dict[str, set[str]]:
        executable_names = {
            identity.executable_name.lower()
        } if identity.executable_name else set()
        exact_names = {
            name.lower()
            for name in identity.search_tokens.exact_names
            if name and name.lower() not in executable_names
        }
        normalized_names = {
            compact
            for name in identity.search_tokens.exact_names
            if name
            for compact in [self._normalize_text(name)]
            if len(compact) >= 4
        }
        bundle_tokens = {
            token.lower()
            for token in [identity.bundle_id, *identity.embedded_bundle_ids]
            if token
        }
        return {
            "exact_names": exact_names,
            "normalized_names": normalized_names,
            "executable_names": executable_names,
            "bundle_tokens": bundle_tokens,
        }

    def _match_launchd_plist(self, path: Path, tokens: dict[str, set[str]]) -> list[str]:
        evidence: list[str] = []
        path_name = path.name.lower()

        try:
            plist = plistlib.loads(path.read_bytes())
        except Exception:
            contents = path.read_text(errors="ignore")
            launchd_fields = [contents]
        else:
            contents = self._plist_search_text(plist)
            launchd_fields = self._plist_string_values(plist)

        contents = contents.lower()
        launchd_fields = [field.lower() for field in launchd_fields]
        compact_fields = [field for field in launchd_fields if "/" not in field]

        if any(
            self._contains_term(path_name, token) or self._contains_term(contents, token)
            for token in tokens["bundle_tokens"]
        ):
            evidence.append("launchd_exact")
        if any(
            self._contains_term(path_name, token) or self._contains_term(contents, token)
            for token in tokens["exact_names"]
        ):
            evidence.append("launchd_app_name_match")
        if any(
            self._matches_compact_field(path_name, token)
            or any(self._matches_compact_field(field, token) for field in compact_fields)
            for token in tokens["normalized_names"]
        ):
            evidence.append("launchd_program_match")
        if any(
            self._matches_executable_field(path_name, token)
            or any(self._matches_executable_field(field, token) for field in launchd_fields)
            for token in tokens["executable_names"]
        ):
            evidence.append("launchd_program_match")

        return list(dict.fromkeys(evidence))

    def _plist_search_text(self, value: object) -> str:
        if isinstance(value, dict):
            return " ".join(
                f"{key} {self._plist_search_text(item)}" for key, item in value.items()
            )
        if isinstance(value, list):
            return " ".join(self._plist_search_text(item) for item in value)
        return str(value)

    def _plist_string_values(self, value: object) -> list[str]:
        if isinstance(value, dict):
            values: list[str] = []
            for key, item in value.items():
                values.append(str(key))
                values.extend(self._plist_string_values(item))
            return values
        if isinstance(value, list):
            values: list[str] = []
            for item in value:
                values.extend(self._plist_string_values(item))
            return values
        return [str(value)]

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _contains_term(self, text: str, token: str, min_len: int = 1) -> bool:
        if not token or len(token) < min_len:
            return False
        pattern = rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])"
        return re.search(pattern, text) is not None

    def _matches_compact_field(self, text: str, token: str) -> bool:
        if len(token) < 4:
            return False
        allowed_suffixes = {"", "agent", "daemon", "helper", "service", "launcher", "loginitem", "runner", "monitor", "updater", "extension", "host"}
        for segment in re.split(r"[^a-z0-9]+", text.lower()):
            if not segment:
                continue
            if segment == token:
                return True
            if segment.startswith(token) and segment[len(token):] in allowed_suffixes:
                return True
        return False

    def _matches_executable_field(self, text: str, token: str) -> bool:
        if len(token) < 4:
            return False
        candidate = text.strip().rstrip("/")
        if not candidate:
            return False
        basename = candidate.split("/")[-1].lower()
        stem = basename.rsplit(".", 1)[0]
        return basename == token or stem == token

    def _system_subpath(self, name: str) -> Path:
        if self.system_root.name == "Library":
            return self.system_root / name
        return self.system_root / "Library" / name

    def _scan_vendor_shared(self, identity: AppIdentity) -> list[dict]:
        results = []
        if identity.vendor == "adobe":
            for path in [
                self.home / "Library" / "Application Support" / "Adobe",
                self.system_root / "Application Support" / "Adobe",
            ]:
                if path.exists():
                    results.append(
                        {
                            "path": str(path),
                            "evidence": ["vendor_suite_path", "shared_support_directory"],
                        }
                    )
        return results
