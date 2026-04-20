# Generic Vendor Formulas

## Goal

Vendor support matters, but the long-term goal is not to pile up one-off vendor-specific rules forever.

The goal is to identify **generic formulas** that hold across many vendor-managed distributions and suites.

## Principle

A vendor adapter is acceptable when it expresses a reusable policy pattern.

A vendor adapter is a smell when it exists only as a bag of special-case path hacks with no reusable rule behind it.

## Core formulas

### Formula 1 — Official manager first, generic fallback second
If a product family has a trusted official manager/uninstaller/cleaner, the inspector should:
1. detect that manager path
2. classify it as the preferred removal authority
3. still inspect local state generically
4. avoid pretending generic file matching alone is equally authoritative

Examples:
- Adobe Creative Cloud
- Setapp desktop
- Homebrew cask uninstall/zap

### Formula 2 — Structured provenance first, heuristics last
Order matters.

This is the project-wide rule: **structured provenance first**, heuristic fallback last.

Preferred order:
1. distribution metadata
2. embedded bundle structure
3. containers and entitlements
4. system integrations
5. user-space state
6. heuristic fallback

This formula should remain stable even as vendors change.

### Formula 3 — Separate ownership from proximity
A path being *near* an app name does not mean the app *owns* it.

Always classify candidates into at least:
- `app_owned`
- `system_integrated`
- `vendor_shared`
- `heuristic_only`

This general rule prevents suite-level collateral damage.

### Formula 4 — Preserve evidence, never collapse to a naked path list
Every candidate should keep:
- path
- evidence
- score
- ownership class
- warnings
- included modes

Without this, the system becomes un-auditable and difficult to improve.

### Formula 5 — `sudo` changes access, not attribution
Privilege escalation may be needed to:
- read more locations
- unload system assets
- remove protected files

But it does not solve ownership inference.

This formula should be applied uniformly across vendors.

### Formula 6 — Prefer policy adapters over path adapters
A good adapter encodes policy like:
- use official manager first
- mark suite-shared support as shared
- avoid deleting vendor-level roots in safe mode

A weak adapter only hardcodes many directories.

## Adapter design template

Each vendor adapter should answer these questions:

1. **Manager authority**
   - Is there an official manager/uninstaller/cleaner?
2. **Shared asset model**
   - Which roots are likely shared across the suite?
3. **App-local asset model**
   - Which assets are typically app-owned?
4. **System integration model**
   - What launchd/helper/plugin/system-extension patterns are common?
5. **Fallback policy**
   - What should generic scanning still inspect even if the official manager exists?
6. **Mode policy**
   - What appears only in `aggressive`?

## Immediate implications for this project

### Adobe
Use Adobe mainly to define the reusable formula:
- official manager first
- cleaner tool available
- many shared assets should not be treated as app-owned

### Setapp
Use Setapp mainly to define another reusable formula:
- external manager controls installation lifecycle
- app bundle alone is not the whole provenance story
- generic scanning still has value for visibility

### Future vendors
The same formulas should generalize to:
- Microsoft
- JetBrains Toolbox
- Steam
- Autodesk
- MAS-adjacent managed products

## Success criterion

The project is succeeding if adding a new vendor mostly means:
- filling a small adapter policy template
- reusing existing pipeline/scoring logic
- adding a few tests

The project is failing if every new vendor requires:
- many bespoke path hacks
- duplicated scanner logic
- special-case deletion ordering with no abstraction
