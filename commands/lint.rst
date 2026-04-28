# Lint

Runs quality checks on brain content.

## Synopsis

```bash
gbrain lint [flags]
gbrain lint <slug> [slug...]
```

## Description

The `lint` command checks brain content for quality issues including:
- Missing citations
- Broken links
- Missing backlinks (Iron Law violations)
- Notability gate failures
- Formatting issues

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--fix` | Automatically fix issues | `false` |
| `--category <cat>` | Check only specific category | `none` |
| `--strict` | Treat warnings as errors | `false` |
| `--json` | Output results as JSON | `false` |

## Categories

| Category | Checks |
|----------|--------|
| `citations` | External claims have sources |
| `links` | All links are valid |
| `backlinks` | Iron Law compliance |
| `formatting` | Markdown formatting |
| `notability` | Subject meets notability threshold |

## Examples

### Check Entire Brain

```bash
gbrain lint
gbrain lint --strict
```

### Check Specific Page

```bash
gbrain lint people/alice
gbrain lint people/alice --fix
```

### Auto-Fix Issues

```bash
# Fix all issues
gbrain lint --fix

# Fix only link issues
gbrain lint --category links --fix
```

### JSON Output

```bash
gbrain lint --json > lint-report.json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | Issues found (non-strict) |
| `2` | Fatal error |
| `3` | Issues found in strict mode |

## See Also

- {doc}`doctor` - Health checks
- {doc}`backlinks` - Backlink management
- {doc}`maintain` - Maintenance operations
