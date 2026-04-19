# Architecture

## Goal

Build a provenance-aware macOS uninstall inspector that can discover candidate files for removal more accurately than heuristic-only uninstallers.

## Non-goals for the first implementation

- Automatic deletion without review
- Perfect certainty for vendor-shared assets
- Reimplementing every official vendor uninstaller internally
- Treating `sudo` as an attribution solution

## High-level components

### 1. App Identity Extractor
Inputs:
- app path
- `Info.plist`
- code signing metadata
- entitlements
- embedded bundle structure

Outputs:
- display name
- bundle identifier
- executable name
- team identifier
- authority chain summary
- app groups / relevant entitlements
- embedded helper bundle identifiers

### 2. Provenance Resolvers
Each resolver produces candidate assets and evidence.

#### Homebrew Resolver
Sources:
- installed cask list
- cask metadata
- uninstall artifacts
- zap rules
- generate-zap output when available

#### PKG Resolver
Sources:
- `pkgutil --pkgs`
- `pkgutil --files`
- receipt metadata
- BOM-derived files

#### MAS Resolver
Sources:
- `_MASReceipt`
- App Store metadata
- container presence

#### Setapp Resolver
Sources:
- bundle identifier suffixes such as `-setapp`
- Setapp-managed metadata/signals
- Setapp app removal behavior as authoritative preference

#### Vendor Resolver
Special handlers for suites that should defer to official tooling.
Initial class:
- Adobe Creative Cloud / Cleaner Tool

### 3. Embedded Artifact Enumerator
Finds app-bundled integrations:
- login items
- system extensions
- helper apps
- XPC services
- plugins

### 4. Container and Entitlement Mapper
Maps:
- sandbox containers
- group containers
- UUID-backed containers via metadata plist
- app-group entitlements

### 5. System Integration Scanner
Scans structured locations for system-bound components:
- `/Library/LaunchAgents`
- `/Library/LaunchDaemons`
- `/Library/PrivilegedHelperTools`
- audio plug-ins
- preference panes
- QuickLook plugins
- Internet Plug-Ins
- widgets / screen savers / Spotlight importers

### 6. User State Scanner
Scans user-owned state:
- `~/Library/Application Support`
- `~/Library/Caches`
- `~/Library/Preferences`
- `~/Library/Preferences/ByHost`
- `~/Library/Logs`
- `~/Library/Saved Application State`
- `~/Library/WebKit`
- `~/Library/HTTPStorages`

### 7. Heuristic Fallback Scanner
Used last, never first.
Signals:
- app name exact / partial
- bundle id exact / partial
- stripped app names
- vendor token matches
- team identifier hints
- Spotlight metadata matches

### 8. Candidate Scorer
Each candidate gets:
- ownership class
- confidence score
- evidence set
- warnings
- delete recommendation per mode

### 9. Review Output Layer
Primary output is machine-readable JSON plus human-readable grouped summary.

## Modes

### Safe
Only high-confidence assets:
- explicit Homebrew/pkg/MAS/Setapp/vendor signals
- bundle-embedded helpers
- exact bundle-id container/prefs/cache matches

### Balanced
Safe plus conventional related files:
- LaunchAgents/Daemons
- PrivilegedHelperTools
- exact Application Support / Logs / SavedState

### Aggressive
Balanced plus broad heuristics:
- vendor folders
- stripped-name matches
- Spotlight broad matches
- lower-confidence candidates flagged for review

## Why `sudo` is not enough

`sudo` improves access and deletion rights for:
- system-level launchd assets
- privileged helpers
- root-owned support files

But it does not answer:
- Is this file owned by this app or shared across a suite?
- Is this vendor directory shared by multiple apps?
- Is this path merely name-similar but unrelated?

Therefore, privilege escalation is an execution concern, not an attribution strategy.
