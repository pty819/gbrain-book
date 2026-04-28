# Report

Generates reports from brain content.

## Synopsis

```bash
gbrain report <type> [flags]
```

## Description

The `report` command generates structured reports from your brain data for analysis and sharing.

## Report Types

### Summary Report

```bash
gbrain report summary
gbrain report summary --period month
```

Shows overview statistics and recent activity.

### Person Report

```bash
gbrain report person alice
gbrain report person alice --include-deals
```

Generates comprehensive dossier on a person.

### Company Report

```bash
gbrain report company acme
gbrain report company acme --include-news
```

Generates company profile with related contacts and deals.

### Deal Report

```bash
gbrain report deal acme-seed
```

Investment deal summary with connected parties.

### Activity Report

```bash
gbrain report activity --since 2024-01-01
gbrain report activity --by person
```

Activity across the brain, grouped by entity or time.

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--period <period>` | Time period (`week`, `month`, `year`) | `month` |
| `--since <date>` | Start date | `none` |
| `--until <date>` | End date | `none` |
| `--output <path>` | Output file | `stdout` |
| `--format <fmt>` | Output format (`md`, `json`, `html`) | `md` |
| `--include-news` | Include latest news | `false` |
| `--include-deals` | Include related deals | `false` |

## Examples

### Weekly Summary

```bash
gbrain report summary --period week
gbrain report summary --period week --output weekly.md
```

### Person Dossier

```bash
# Quick summary
gbrain report person alice

# Comprehensive with deals
gbrain report person alice --include-deals --format html --output alice.html
```

### Company Intelligence

```bash
gbrain report company acme --include-news --output acme-intel.md
```

### Activity Timeline

```bash
# All activity since date
gbrain report activity --since 2024-01-01

# Grouped by person
gbrain report activity --since 2024-01-01 --by person
```

## Output Formats

### Markdown (default)

```markdown
# Person Report: Alice

## Overview
...
## Connections
...
## Activity
...
```

### JSON

```json
{
  "type": "person",
  "slug": "alice",
  "overview": {...},
  "connections": [...],
  "activity": [...]
}
```

### HTML

```html
<!DOCTYPE html>
<html>
...
```

## See Also

- {doc}`dream` - AI-powered synthesis
- {doc}`extract` - Data extraction
- {doc}`publish` - Publishing reports
