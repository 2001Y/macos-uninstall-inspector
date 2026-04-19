# Discovery Pipeline

This inspector should try all applicable approaches on every run, but in a strict order.

## Step 0 — Normalize input
Collect:
- app path
- display name
- bundle identifier
- executable name
- team identifier
- entitlements
- signer information

Build normalized search tokens:
- exact bundle id
- bundle id suffix tokens
- app name exact
- stripped app name
- vendor token
- team token

## Step 1 — Distribution provenance first
Attempt in this order:

1. Homebrew cask resolution
2. pkg receipt/BOM resolution
3. MAS receipt resolution
4. Setapp resolution
5. vendor-managed suite resolution

Why first:
- highest precision
- best explanation to user
- often includes uninstall semantics the OS itself does not encode elsewhere

## Step 2 — Embedded bundle artifacts
Inspect the bundle tree for:
- login items
- system extensions
- helpers
- plugins
- XPC services

These are commonly missed by naïve name-based scanners.

## Step 3 — Containers and app groups
Resolve:
- exact sandbox containers
- group containers
- UUID container metadata pointing back to bundle id
- entitlement-derived app groups

## Step 4 — System integrations
Inspect structured locations for assets whose ownership can be inferred from labels, bundle ids, helper names, or embedded provenance.

## Step 5 — User state
Search conventional user directories using exact bundle id first.
Only fall back to app-name matching where exact signals are absent.

## Step 6 — Heuristic fallback
Run broad search only after structured discovery completes.
Heuristic matches should be flagged as such and never silently merged into high-confidence ownership.

## Step 7 — Score and classify
For each candidate produce:
- ownership class
- confidence score
- matched evidence
- mode inclusion (`safe`, `balanced`, `aggressive`)
- warning flags for shared/vendor-managed assets

## Step 8 — Present grouped review
Group by:
- app-owned
- helper/system-integrated
- vendor-shared
- uncertain heuristic-only

## Deletion policy (future)
A future deleter should delete in dependency-aware order:
1. stop/quit processes
2. remove launchd references
3. unload helpers if needed
4. remove app bundle and embedded helpers
5. remove system integrations
6. remove user state
7. remove receipts only after installed files are handled

But this repository does **not** implement deletion yet.
