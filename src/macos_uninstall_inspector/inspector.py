from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .distribution import DistributionResolution, DistributionResolver
from .identity import AppIdentity, IdentityExtractor
from .scanner import ConventionalScanner


EVIDENCE_WEIGHTS = {
    "homebrew_cask_artifact": 35,
    "bundle_path_exact": 30,
    "bundle_id_exact": 30,
    "preferences_conventional_path": 15,
    "logs_conventional_path": 8,
    "app_name_exact": 15,
    "vendor_suite_path": 8,
    "shared_support_directory": -25,
    "vendor_token_match": -15,
}

MODE_THRESHOLDS = {"safe": 80, "balanced": 60, "aggressive": 35}


@dataclass(frozen=True)
class Candidate:
    path: str
    ownership: str
    score: int
    evidence: list[str]
    warnings: list[str]
    modes: list[str]


@dataclass(frozen=True)
class InspectionReport:
    identity: AppIdentity
    distribution: DistributionResolution
    candidates: list[Candidate]
    mode_thresholds: dict[str, int]

    def to_document(self) -> dict:
        return {
            "app": {
                "path": str(self.identity.path),
                "display_name": self.identity.display_name,
                "bundle_id": self.identity.bundle_id,
                "team_id": None,
                "vendor": self.identity.vendor,
            },
            "distribution": {
                "kind": self.distribution.kind,
                "resolver_priority": self.distribution.resolver_priority,
                "manager_hint": self.distribution.manager_hint,
            },
            "mode_thresholds": self.mode_thresholds,
            "candidates": [
                {
                    "path": c.path,
                    "ownership": c.ownership,
                    "score": c.score,
                    "evidence": c.evidence,
                    "warnings": c.warnings,
                    "modes": c.modes,
                }
                for c in self.candidates
            ],
        }


class Inspector:
    def __init__(self, home: str | Path | None = None) -> None:
        self.identity_extractor = IdentityExtractor()
        self.distribution_resolver = DistributionResolver()
        self.scanner = ConventionalScanner(home=home)

    def inspect(self, app_path: str | Path, context: dict | None = None) -> InspectionReport:
        context = context or {}
        identity = self.identity_extractor.extract(app_path)
        distribution = self.distribution_resolver.resolve(identity, context=context)
        raw_candidates = list(context.get("candidates", []))
        raw_candidates.extend(self.scanner.scan(identity))
        candidates = [self._candidate_from_raw(item, distribution.kind) for item in raw_candidates]
        deduped: dict[str, Candidate] = {}
        for candidate in candidates:
            existing = deduped.get(candidate.path)
            if existing is None:
                deduped[candidate.path] = candidate
                continue
            merged_evidence = list(dict.fromkeys(existing.evidence + candidate.evidence))
            merged_warnings = list(dict.fromkeys(existing.warnings + candidate.warnings))
            merged_candidate = self._candidate_from_raw(
                {"path": candidate.path, "evidence": merged_evidence},
                distribution.kind,
            )
            deduped[candidate.path] = Candidate(
                path=merged_candidate.path,
                ownership=merged_candidate.ownership,
                score=merged_candidate.score,
                evidence=merged_candidate.evidence,
                warnings=merged_warnings,
                modes=merged_candidate.modes,
            )
        sorted_candidates = sorted(deduped.values(), key=lambda item: item.score, reverse=True)
        return InspectionReport(
            identity=identity,
            distribution=distribution,
            candidates=sorted_candidates,
            mode_thresholds=dict(MODE_THRESHOLDS),
        )

    def _candidate_from_raw(self, item: dict, distribution_kind: str) -> Candidate:
        evidence = list(item.get("evidence", []))
        score = max(0, min(100, 50 + sum(EVIDENCE_WEIGHTS.get(ev, 0) for ev in evidence)))
        ownership = self._ownership(evidence, distribution_kind)
        warnings = []
        if ownership == "vendor_shared":
            warnings.append("likely_shared_across_suite")
        modes = [name for name, threshold in MODE_THRESHOLDS.items() if score >= threshold]
        return Candidate(
            path=item["path"],
            ownership=ownership,
            score=score,
            evidence=evidence,
            warnings=warnings,
            modes=modes,
        )

    @staticmethod
    def _ownership(evidence: list[str], distribution_kind: str) -> str:
        if "shared_support_directory" in evidence or distribution_kind == "vendor_suite" and "vendor_suite_path" in evidence:
            return "vendor_shared"
        if any(ev in evidence for ev in ["homebrew_cask_artifact", "bundle_path_exact", "bundle_id_exact"]):
            return "app_owned"
        if any(ev in evidence for ev in ["launchd_exact", "privileged_helper_exact", "system_extension_embedded"]):
            return "system_integrated"
        return "heuristic_only"
