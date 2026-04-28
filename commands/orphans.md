# Orphans

Finds and manages orphaned brain pages (pages with no inbound links).

## Synopsis

```bash
gbrain orphans [subcommand] [flags]
```

## Description

Orphaned pages are pages that no other page links to. They become isolated from the knowledge graph. The `orphans` command helps find and integrate these pages.

## Subcommands

### List Orphans

```bash
gbrain orphans list
gbrain orphans list --category people
```

Shows all orphaned pages:

```
Orphans
=======
Total: 12

People (3):
  - people/alice
  - people/bob
  - people/carol

Companies (2):
  - companies/old-startup

Other (7):
  - notes/untitled
  - ideas/2024-03
```

### Fix

```bash
gbrain orphans fix
gbrain orphans fix people/alice
gbrain orphans fix --auto-link
```

Attempts to fix orphans by:
- Suggesting likely connections
- Auto-linking to related content
- Moving to appropriate categories

### Archive

```bash
gbrain orphans archive
gbrain orphans archive --older-than 90d
```

Archives orphaned pages that haven't been connected.

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--category <cat>` | Filter by category | `none` |
| `--older-than <duration>` | Filter by age | `none` |
| `--auto-link` | Automatically create links | `false` |
| `--dry-run` | Preview without changes | `false` |
| `--json` | Output as JSON | `false` |

## Examples

### Find All Orphans

```bash
# List all orphaned pages
gbrain orphans list

# JSON output
gbrain orphans list --json

# Filter by category
gbrain orphans list --category people
```

### Fix Orphans

```bash
# Preview what would be fixed
gbrain orphans fix --dry-run

# Auto-link suggestions
gbrain orphans fix --auto-link
```

### Clean Up Old Orphans

```bash
# Archive orphans older than 90 days
gbrain orphans archive --older-than 90d

# Preview archive
gbrain orphans archive --older-than 90d --dry-run
```

## Why Orphans Matter

Orphaned pages:
- Don't appear in graph-based search
- Violate the Iron Law (every page should be findable via links)
- May represent outdated or irrelevant content

## See Also

- {doc}`backlinks` - Backlink management
- {doc}`maintain` - Maintenance operations
- {doc}`lint` - Quality checks
