# Sync

Synchronizes content from external sources into your GBrain.

## Synopsis

```bash
gbrain sync [flags]
gbrain sync <source> [source...]
```

## Description

The `sync` command imports content from various sources into your brain. It supports:

- File system imports (markdown, PDF, text)
- URL scraping (web pages, articles)
- Direct content ingestion (stdin, arguments)
- Git repository synchronization

## Source Types

### File System

```bash
gbrain sync ~/notes/           # Import directory
gbrain sync ~/notes/*.md       # Glob pattern
gbrain sync --no-embed ~/brain/  # Import without embedding
```

### URLs

```bash
gbrain sync https://example.com/article
gbrain sync --source-url "https://news.example.com" ./article.html
```

### Git Repositories

```bash
gbrain sync --repo https://github.com/user/repo
gbrain sync --repo ~/my-knowledge --branch main
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--no-embed` | Skip embedding generation | `false` |
| `--no-pull` | Skip git pull for repos | `false` |
| `--source <url>` | Source URL for content | `none` |
| `--repo <path>` | Git repository to sync | `none` |
| `--branch <name>` | Git branch for repo sync | `main` |
| `--dry-run` | Show what would be imported | `false` |

## Examples

### Import a Directory

```bash
# Basic import
gbrain sync ~/brain/

# With dry-run to preview
gbrain sync ~/brain/ --dry-run

# Skip embeddings for faster import
gbrain sync ~/brain/ --no-embed
```

### Sync a Git Repository

```bash
# Clone and sync
gbrain sync --repo https://github.com/user/knowledge-base

# Update existing repo
gbrain sync --repo ~/brain --no-embed
```

### Import Web Content

```bash
# Scrape and ingest URL
gbrain sync https://example.com/article

# With explicit source attribution
gbrain sync --source-url "https://news.example.com" ./article.html
```

## Post-Sync

After sync, run embed to generate vector embeddings:

```bash
gbrain sync ~/brain/
gbrain embed --stale  # Generate embeddings for new content
```

## See Also

- {doc}`embed` - Embedding generation
- {doc}`ingest` - Alternative ingestion
- {doc}`../guides/live-sync` - Continuous synchronization
