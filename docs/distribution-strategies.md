# Distribution-Specific Strategies

## Plain DMG / ZIP app bundles
Characteristics:
- no package receipts
- often no installer provenance
- ownership mostly inferred from bundle metadata + conventional file locations

Strategy:
- inspect bundle identity
- inspect embedded helpers/plugins
- inspect containers/app groups
- inspect conventional Library paths
- use heuristics only as fallback

## Mac App Store (MAS)
Signals:
- `_MASReceipt`
- App Store signatures / metadata
- bundle-id aligned containers

Strategy:
- trust bundle id + MAS signals
- search containers and sandboxed state first
- receipt cleanup is lower priority than exact app-state cleanup

## Homebrew casks
Signals:
- `brew list --cask`
- `brew info --cask`
- cask uninstall artifacts
- zap definitions
- optional `brew generate-zap`

Strategy:
- treat Homebrew metadata as authoritative for cask-managed assets
- augment with local exact bundle/container state
- do not rely solely on heuristic name search
- note that `brew generate-zap` can fail on permissions/visibility and should be advisory, not mandatory

## PKG-installed apps
Signals:
- `pkgutil --pkgs`
- `pkgutil --files`
- BOM-derived installed file lists

Strategy:
- prefer receipt/BOM file ownership over name heuristics
- aggregate related package ids for suites with multiple helpers/components
- forget receipts only after actual installed paths are handled

## Setapp-managed apps
Signals:
- bundle identifier suffixes such as `-setapp`
- Setapp-managed installation behavior
- Setapp’s own uninstall pathways

Strategy:
- identify the app as Setapp-managed early
- prefer Setapp removal semantics as the primary uninstall path
- still inspect exact containers, groups, caches, logs, and preferences for visibility
- avoid pretending the app is equivalent to an unmanaged plain `.app`

## Adobe Creative Cloud and similar vendor-managed suites
Signals:
- Adobe bundle/team metadata
- Creative Cloud installation state
- official uninstallers
- official Cleaner Tool

Strategy:
- prefer official Creative Cloud uninstall flow
- use Cleaner Tool as a vendor-level cleanup/remediation path
- treat shared Adobe assets with caution
- classify many vendor folders as potentially shared rather than app-owned

## Why vendor-specific paths matter
Some products encode uninstall semantics outside the app bundle:
- suite-level shared services
- sync daemons
- plug-ins
- licensing components
- repair tools

A generic inspector can discover candidates, but in some families the official manager remains the highest-confidence removal authority.
