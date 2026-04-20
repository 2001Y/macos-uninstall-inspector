# macos-uninstall-inspector

- 日本語: [README.ja.md](README.ja.md)

**Know what an app owns before you delete it.**

A provenance-aware macOS uninstall inspector that explains **what should be removed**, **why it was matched**, and **how confident it is** — before anything destructive happens.

Instead of acting like every Mac app is just a loose `.app` bundle, `macos-uninstall-inspector` treats uninstall inspection as a provenance problem:

- Was it installed by **Homebrew**?
- Did it come from a **pkg** with receipts/BOMs?
- Is it a **Mac App Store** app?
- Is it **Setapp-managed**?
- Is it part of a **vendor-managed suite** like Adobe?
- Is this file **app-owned**, **system-integrated**, **vendor-shared**, or just a **heuristic guess**?

## Why this exists

Traditional Mac uninstall tools are often good at collecting *possible* leftovers, but weaker at explaining *ownership*. This project focuses on the missing layer:

- structured provenance before name matching
- confidence scoring instead of false certainty
- safe/balanced/aggressive review modes
- vendor-aware handling without collapsing into vendor-specific hacks everywhere

Running with `sudo` helps with **visibility and deletion permissions**, but it does **not** solve the harder problem: deciding whether a file truly belongs to a specific app versus a shared vendor asset or unrelated bystander.

## What it does today

Implemented now:
- read-only inspection CLI: `mui inspect <App.app>`
- automatic runtime context collection for Homebrew and pkg hints
- identity extraction from app bundles
- distribution classification: plain / MAS / Homebrew / pkg / Setapp / Adobe vendor-suite
- conventional scanning for embedded helpers and common Library state
- generic scanning for LaunchAgents / LaunchDaemons / PrivilegedHelperTools
- stronger launchd correlation via bundle id / app name / executable path matching
- evidence scoring and ownership classification
- mode filtering: `safe`, `balanced`, `aggressive`
- JSON output validated against `schemas/finding.schema.json`

Still future work:
- deeper system integration scanning (audio plugins, QuickLook, PreferencePanes, widgets)
- full entitlements/container metadata correlation
- richer vendor adapters beyond Adobe
- reviewed deletion engine

## Core idea

The discovery pipeline always tries **all applicable approaches**, but not all evidence is treated equally.

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

## Generic formulas matter more than vendor one-offs

This project values **generic, reusable rules** over brittle per-vendor special-casing.

The goal is not to hardcode every vendor forever. The goal is to identify reusable formulas such as:

- official manager first, generic fallback second
- structured provenance first, heuristic fallback last
- separate app-owned vs vendor-shared assets
- classify system integrations explicitly
- keep confidence and evidence attached to every candidate

Vendor adapters still matter, but they should exist mainly to express a **general policy pattern** clearly enough to reuse across many vendors.

See [`docs/generic-vendor-formulas.md`](docs/generic-vendor-formulas.md) for the policy direction.

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

## Example

```bash
mui inspect /Applications/Claude.app --mode safe
```

The output is JSON and includes:
- app identity
- detected distribution kind
- mode thresholds
- candidate paths
- ownership class
- score
- evidence
- warnings
- included modes

## Repository contents

- `docs/architecture.md` — full system architecture
- `docs/pipeline.md` — step-by-step discovery order
- `docs/distribution-strategies.md` — Homebrew / pkg / MAS / Setapp / Adobe handling
- `docs/confidence-model.md` — scoring and candidate classification
- `docs/roadmap.md` — implementation roadmap and milestones
- `docs/generic-vendor-formulas.md` — reusable vendor-handling principles
- `schemas/finding.schema.json` — canonical JSON shape for an inspection result
- `examples/` — sample inspection outputs
- `scripts/validate_examples.py` — schema validation helper
- `tests/` — tests for schema/example validation and inspector behavior

## Initial scope

This public repo now contains both the detailed design and an implemented read-only MVP inspector.

## License

MIT
