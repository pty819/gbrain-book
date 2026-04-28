# Doctor

Runs health checks and diagnostics on your GBrain installation.

## Synopsis

```bash
gbrain doctor [flags]
```

## Description

The `doctor` command verifies that your GBrain installation is healthy and functioning correctly. It checks:

- Database connectivity and schema
- Required directories and permissions
- Configuration validity
- Skill manifest integrity
- Embedding service status
- Link consistency

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--json` | Output results as JSON | `false` |
| `--fix` | Automatically fix detected issues | `false` |
| `--verbose` | Show detailed diagnostic output | `false` |

## Output

When run without flags, `doctor` displays a human-readable report:

```
GBrain Doctor
============

✓ Database: Connected (PGLite)
✓ Schema: Up to date (v0.12.2)
✓ Config: Valid
✓ Skills: 29/29 loaded
✓ Embeddings: 1,247 chunks indexed
✓ Links: 3,421 links, 12 orphaned
✓ Directories: OK

Run 'gbrain doctor --fix' to repair 12 orphaned links.
```

When run with `--json`, outputs structured JSON:

```json
{
  "status": "needs_repair",
  "checks": {
    "database": { "status": "ok" },
    "schema": { "status": "ok", "version": "0.12.2" },
    "skills": { "status": "ok", "count": 29 },
    "embeddings": { "status": "ok", "chunks": 1247 },
    "links": { "status": "needs_repair", "total": 3421, "orphaned": 12 }
  }
}
```

## Repair Mode

Use `--fix` to automatically repair detected issues:

```bash
gbrain doctor --fix
```

Repairs include:
- Fixing orphaned backlinks
- Regenerating corrupted embeddings
- Cleaning up stale cache files
- Repairing JSONB encoding issues

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | One or more checks failed |
| `2` | Fatal error (database unreachable, etc.) |

## See Also

- {doc}`sync` - Synchronization
- {doc}`maintain` - Maintenance operations
- {doc}`../guides/troubleshooting` - Common issues
