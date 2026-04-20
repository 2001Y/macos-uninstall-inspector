from __future__ import annotations

from pathlib import Path

from .identity import AppIdentity


class ConventionalScanner:
    def __init__(self, home: str | Path | None = None, system_root: str | Path = "/Library") -> None:
        self.home = Path(home).expanduser() if home else Path.home()
        self.system_root = Path(system_root)

    def scan(self, identity: AppIdentity) -> list[dict]:
        findings: list[dict] = []

        findings.extend(self._scan_embedded(identity))
        findings.extend(self._scan_library_state(identity))
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
        for relative in [
            Path("Contents/Library/LoginItems"),
            Path("Contents/Library/SystemExtensions"),
            Path("Contents/Library/Helpers"),
            Path("Contents/Helpers"),
            Path("Contents/XPCServices"),
            Path("Contents/PlugIns"),
        ]:
            base = identity.path / relative
            if base.exists():
                for child in sorted(base.iterdir()):
                    results.append(
                        {
                            "path": str(child),
                            "evidence": ["bundle_path_exact", "embedded_helper_path"],
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
        results = []
        for path in targets:
            if path.exists():
                evidence = ["bundle_id_exact"]
                if "Preferences" in path.parts:
                    evidence.append("preferences_conventional_path")
                elif "Logs" in path.parts:
                    evidence.append("logs_conventional_path")
                    evidence.append("app_name_exact")
                else:
                    evidence.append("bundle_path_exact")
                results.append({"path": str(path), "evidence": evidence})
        return results

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
