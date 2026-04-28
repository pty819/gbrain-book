# Extract

Extracts structured data from your brain for analysis and export.

## Synopsis

```bash
gbrain extract <type> [flags]
```

## Description

The `extract` command pulls structured information from your brain for analysis, reporting, and export.

## Extract Types

### Links

Extract all links and relationships from your brain:

```bash
gbrain extract links
gbrain extract links --source db
gbrain extract links --dry-run
```

Output format:

```
Link Summary
============
Total links: 3,421
Types:
  - works_at: 892
  - invested_in: 234
  - founded: 156
  - attended: 445
  - advises: 89
  - mentions: 1,605
```

### Timeline

Extract dated events and timeline entries:

```bash
gbrain extract timeline
gbrain extract timeline --source db
gbrain extract timeline --since 2024-01-01
```

Output format:

```
Timeline Events (2024)
======================
2024-03-15: Alice founded Acme (source: people/alice)
2024-03-10: Acme raised seed round (source: deals/acme-seed)
2024-02-20: Alice attended YC W24 Demo Day (source: events/yc-w24)
```

### People

Extract all person entities:

```bash
gbrain extract people
```

### Companies

Extract all company entities:

```bash
gbrain extract companies
```

### Deals

Extract all deal/investment records:

```bash
gbrain extract deals
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--source <source>` | Data source (`db` or `fs`) | `db` |
| `--since <date>` | Filter events after date | `none` |
| `--until <date>` | Filter events before date | `none` |
| `--dry-run` | Preview without committing | `false` |
| `--json` | Output as JSON | `false` |

## Examples

### Full Link Audit

```bash
# Preview changes
gbrain extract links --source db --dry-run

# Commit to database
gbrain extract links --source db

# Show only new links
gbrain extract links --since 2024-01-01
```

### Timeline Report

```bash
# All events this year
gbrain extract timeline --since 2024-01-01

# Date range
gbrain extract timeline --since 2024-01-01 --until 2024-06-30

# JSON export
gbrain extract timeline --json > timeline.json
```

## See Also

- {doc}`report` - Generate reports
- {doc}`backlinks` - Backlink management
- {doc}`stats` - Brain statistics
