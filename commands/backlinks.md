# Backlinks

Manages bidirectional links between brain pages.

## Synopsis

```bash
gbrain backlinks <subcommand> [flags]
```

## Description

GBrain enforces the **Iron Law**: if page A links to page B, page B should backlink to page A. The `backlinks` command helps audit and repair these relationships.

## Subcommands

### Check

```bash
gbrain backlinks check
gbrain backlinks check people/alice
```

Checks for broken or missing backlinks:

```
Backlink Check
==============
Total pages: 1,247
Pages with issues: 23

Issue Types:
  - Missing backlink: 18
  - Broken link: 4
  - Circular link: 1
```

### Fix

```bash
gbrain backlinks fix
gbrain backlinks fix people/alice
gbrain backlinks fix --dry-run
```

Automatically repairs backlink issues:

```bash
# Preview changes
gbrain backlinks fix --dry-run

# Apply fixes
gbrain backlinks fix
```

### List

```bash
gbrain backlinks list people/alice
```

Lists all backlinks for a page:

```
Backlinks for people/alice
===========================
Inbound:
  - companies/acme (works_at)
  - deals/acme-seed (invested_in)
  - events/yc-w24 (attended)

Outbound:
  - companies/acme
  - events/yc-w24
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--dry-run` | Preview changes without applying | `false` |
| `--type <type>` | Filter by link type | `none` |
| `--json` | Output as JSON | `false` |

## Link Types

| Type | Meaning |
|------|---------|
| `attended` | Person attended event |
| `works_at` | Person employed at company |
| `invested_in` | Investor placed in deal |
| `founded` | Person started company |
| `advises` | Person advises company |
| `source` | Content source |
| `mentions` | Reference to entity |

## Examples

### Full Brain Audit

```bash
# Check all backlinks
gbrain backlinks check --json > backlink-report.json

# Fix all issues
gbrain backlinks fix

# Fix only specific type
gbrain backlinks fix --type works_at
```

### Page-Specific

```bash
# Check one page
gbrain backlinks check people/alice

# List backlinks
gbrain backlinks list people/alice

# Fix one page
gbrain backlinks fix people/alice --dry-run
```

## See Also

- {doc}`../concepts/knowledge-graph` - Knowledge graph concepts
- {doc}`lint` - Quality checks
- {doc}`../commands/extract` - Extract link data
