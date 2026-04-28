# CLI Overview

GBrain provides a comprehensive command-line interface for managing your personal knowledge brain.

## Command Categories

GBrain commands are organized into logical groups:

| Category | Commands |
|----------|----------|
| **Core** | `init`, `doctor`, `sync`, `query` |
| **Content** | `ingest`, `embed`, `extract` |
| **Search** | `search`, `graph-query`, `backlinks` |
| **Maintenance** | `maintain`, `migrate`, `lint` |
| **Publishing** | `publish` |
| **Utilities** | `jobs`, `dream`, `report`, `orphans`, `code-def` |

## Global Flags

These flags work with all commands:

| Flag | Description |
|------|-------------|
| `--json` | Output results as JSON |
| `--quiet` | Suppress informational output |
| `--verbose` | Enable verbose logging |
| `--help` | Show help for any command |

## Common Workflows

### Initialize a New Brain

```bash
gbrain init                    # PGLite (default)
gbrain init --engine postgres  # Full Postgres
```

### Daily Usage

```bash
# Ingest content
gbrain ingest "https://example.com/article"
gbrain ingest --idea "My original thought"
gbrain ingest --meeting ./transcript.txt

# Search your brain
gbrain query "what did I learn about X?"
gbrain search "keyword"

# Check brain health
gbrain doctor
gbrain stats
```

### Maintenance

```bash
# Regenerate embeddings for stale content
gbrain embed --stale

# Check and fix broken links
gbrain backlinks check
gbrain backlinks fix

# Run quality lint
gbrain lint --fix
```

## Getting Help

```bash
gbrain --help                 # Global help
gbrain <command> --help       # Command-specific help
gbrain <command> <subcommand> --help  # Subcommand help
```

## See Also

- {doc}`doctor` - Health checks and diagnostics
- {doc}`sync` - Synchronization and imports
- {doc}`embed` - Embedding management
- {doc}`query` - Query and search operations
- {doc}`extract` - Data extraction tools
