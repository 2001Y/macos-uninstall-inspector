# Confidence Model

## Ownership classes

### app_owned
Strong evidence that the asset belongs to the selected app specifically.

Examples:
- bundle-embedded helper tied to selected app
- exact bundle-id container
- exact bundle-id plist/cache/log path
- pkg/BOM-installed path belonging to selected package
- Homebrew cask artifact/zap entry for selected app

### system_integrated
App-specific component installed into a system-managed location.

Examples:
- launch agent with exact bundle/helper label
- privileged helper with matching embedded signature
- exact audio plugin installed by app package
- system extension embedded in the app

### vendor_shared
Likely shared across multiple apps from same vendor or suite.

Examples:
- Adobe shared support directories
- TeamViewer shared application support
- shared vendor caches

### heuristic_only
Found only by broad matching and not backed by structured provenance.

Examples:
- vendor token match only
- stripped app name partial match
- Spotlight result without corroboration

## Suggested scoring bands

- **90–100**: strongly attributable
- **70–89**: attributable with minor caveats
- **40–69**: uncertain, requires review
- **0–39**: low-confidence heuristic result

## Example weighting

### Positive evidence
- pkg/BOM exact ownership: +40
- Homebrew cask uninstall/zap artifact: +35
- exact bundle-id path: +30
- embedded helper/system extension: +30
- entitlement app group exact match: +25
- exact launchd label/helper match: +20
- exact app-name conventional path: +15
- vendor/team partial: +8
- Spotlight broad hit: +5

### Negative evidence / caution
- shared vendor directory: -25
- path contains another installed app identity: -20
- only broad vendor token hit: -15
- path discovered only via aggressive heuristic: -10

## Mode thresholds

### Safe
Include only scores >= 80 and no vendor-shared warning.

### Balanced
Include scores >= 60 plus system-integrated items requiring review.

### Aggressive
Include scores >= 35 and all heuristic-only items labeled clearly.

## Review expectations
A UI/CLI should always tell the user:
- why a candidate was included
- what evidence matched
- whether the asset may be shared
- whether an official manager/uninstaller should be used instead
