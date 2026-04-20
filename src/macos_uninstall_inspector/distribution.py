from __future__ import annotations

from dataclasses import dataclass

from .identity import AppIdentity


@dataclass(frozen=True)
class DistributionResolution:
    kind: str
    resolver_priority: list[str]
    manager_hint: str | None


class DistributionResolver:
    def resolve(
        self,
        identity: AppIdentity,
        context: dict | None = None,
    ) -> DistributionResolution:
        context = context or {}
        homebrew_casks = context.get("homebrew_casks", {})
        pkg_receipts = context.get("pkg_receipts", {})

        if identity.bundle_id in homebrew_casks:
            token = homebrew_casks[identity.bundle_id]
            return DistributionResolution(
                kind="homebrew_cask",
                resolver_priority=["homebrew", "bundle_embedded", "containers", "user_state", "heuristic_fallback"],
                manager_hint=f"brew uninstall --cask {token}",
            )

        if identity.bundle_id in pkg_receipts:
            receipts = ", ".join(pkg_receipts[identity.bundle_id])
            return DistributionResolution(
                kind="pkg",
                resolver_priority=["pkg_receipt", "bundle_embedded", "system_integration", "user_state", "heuristic_fallback"],
                manager_hint=f"pkgutil receipts: {receipts}",
            )

        if (identity.path / "Contents" / "_MASReceipt" / "receipt").exists():
            return DistributionResolution(
                kind="mas",
                resolver_priority=["mas_receipt", "bundle_embedded", "containers", "user_state", "heuristic_fallback"],
                manager_hint=None,
            )

        if identity.is_setapp:
            return DistributionResolution(
                kind="setapp",
                resolver_priority=["setapp", "bundle_embedded", "containers", "user_state", "heuristic_fallback"],
                manager_hint="Use Setapp desktop uninstall / Uninstall Completely",
            )

        if identity.bundle_id.startswith("com.adobe."):
            return DistributionResolution(
                kind="vendor_suite",
                resolver_priority=["vendor_adapter", "pkg", "bundle_embedded", "system_integration", "user_state", "heuristic_fallback"],
                manager_hint="Use Adobe Creative Cloud uninstall flow or Cleaner Tool before generic deletion",
            )

        return DistributionResolution(
            kind="plain_app",
            resolver_priority=["bundle_embedded", "containers", "system_integration", "user_state", "heuristic_fallback"],
            manager_hint=None,
        )
