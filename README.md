# macos-uninstall-inspector

A design-first, provenance-aware framework for inspecting what should be removed when uninstalling macOS applications.

This repository is intentionally **inspection-first**. It now includes a working read-only CLI that discovers, classifies, and scores uninstall candidates before any destructive action. The goal is to outperform AppCleaner/Pearcleaner-style heuristic-only approaches by preferring structured provenance sources such as Homebrew casks, pkg receipts/BOMs, bundle-embedded helpers, containers, app groups, launchd assets, and official vendor uninstall paths.

## Why this exists

macOS app removal is not one problem. Different distribution channels require different logic:

- Plain `.app` bundles dragged from a DMG/ZIP
- Mac App Store apps
- Homebrew casks
- `pkg` installers with receipts/BOMs
- Setapp-managed apps
- Complex vendor-managed suites such as Adobe Creative Cloud

Running with `sudo` helps with **visibility and deletion permissions**, but it does **not** solve the harder problem: deciding whether a file truly belongs to a specific app versus a shared vendor asset or unrelated bystander.

## Principles

1. **Inspect before delete**
2. **Prefer structured evidence over name matching**
3. **Keep provenance by distribution channel**
4. **Treat vendor-managed suites specially**
5. **Support safe / balanced / aggressive modes**
6. **Score confidence per candidate instead of pretending certainty**
7. **Never assume `sudo` fixes attribution accuracy**

## Repository contents

- `docs/architecture.md` — full system architecture
- `docs/pipeline.md` — step-by-step discovery order
- `docs/distribution-strategies.md` — Homebrew / pkg / MAS / Setapp / Adobe handling
- `docs/confidence-model.md` — scoring and candidate classification
- `docs/roadmap.md` — implementation roadmap and milestones
- `schemas/finding.schema.json` — canonical JSON shape for an inspection result
- `examples/` — sample inspection outputs
- `scripts/validate_examples.py` — schema validation helper
- `tests/` — tests for schema/example validation

## Core design

The discovery pipeline always tries **all** applicable approaches, but not all evidence is treated equally.

### Ordered evidence layers

1. **Distribution provenance**
   - Homebrew cask metadata / zap / uninstall artifacts
   - pkg receipts + BOMs
   - MAS receipt / App Store metadata
   - Setapp-managed app markers
   - vendor-provided uninstallers / cleaners (Adobe, etc.)
2. **Bundle-embedded components**
   - `Contents/Library/LoginItems`
   - `Contents/Library/SystemExtensions`
   - `Contents/Helpers`
   - `Contents/XPCServices`
   - `Contents/PlugIns`
3. **Entitlements and containers**
   - app groups
   - sandbox containers
   - `containermanagerd` metadata
4. **System integration assets**
   - LaunchAgents / LaunchDaemons
   - PrivilegedHelperTools
   - audio plug-ins
   - QuickLook, PreferencePanes, Internet Plug-Ins, widgets, etc.
5. **User-space state**
   - Application Support
   - Caches
   - Preferences
   - Logs
   - Saved Application State
   - WebKit / HTTPStorages
6. **Heuristic fallback**
   - Spotlight
   - path/name/vendor matching
   - stripped app names
   - team identifier / vendor hints

## Supported uninstall classes

### Generic
- DMG / ZIP / plain app bundles
- MAS apps
- many pkg-installed apps

### Managed distribution
- Homebrew casks
- Setapp apps

### Vendor-managed suites
- Adobe Creative Cloud and related components
- future: Microsoft Office / Autodesk / JetBrains Toolbox / Steam variants

## Safety model

This repo describes an **inspector**, not an eager deleter.

A future implementation should:
- output candidates with confidence and reasons
- separate app-owned vs vendor-shared assets
- allow review before deletion
- route Adobe/Setapp/Homebrew/pkg cases through the correct manager first

## Quick start

```bash
cd macos-uninstall-inspector
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -q
python scripts/validate_examples.py
mui inspect /Applications/Claude.app
mui inspect /Applications/Claude.app --mode safe
```

## Current implementation status

Implemented now:
- read-only inspection CLI: `mui inspect <App.app>`
- automatic runtime context collection for Homebrew and pkg hints
- identity extraction from app bundles
- distribution classification: plain / MAS / Homebrew / pkg / Setapp / Adobe vendor-suite
- conventional scanning for embedded helpers and common Library state
- evidence scoring and ownership classification
- mode filtering: `safe`, `balanced`, `aggressive`
- JSON output validated against `schemas/finding.schema.json`

Still future work:
- deeper system integration scanning (LaunchAgents/Daemons, PrivilegedHelperTools, audio plugins)
- full entitlements/container metadata correlation
- richer vendor adapters beyond Adobe
- reviewed deletion engine

## Initial scope

This public repo now contains both the detailed design and an implemented read-only MVP inspector.

## License

MIT
