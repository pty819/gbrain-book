# Publish

Publishes brain content to external platforms and formats.

## Synopsis

```bash
gbrain publish [subcommand] [flags]
```

## Subcommands

### Publish to Web

```bash
# Publish a page to web
gbrain publish web people/alice

# Publish with custom domain
gbrain publish web companies/acme --domain example.com
```

### Export to Markdown

```bash
# Export entire brain to markdown
gbrain publish markdown ./export/

# Export specific section
gbrain publish markdown people/ --output ~/my-people/
```

### Export to PDF

```bash
# Generate PDF from page
gbrain publish pdf deals/acme-seed --output ./deal-sheet.pdf

# Generate PDF with custom template
gbrain publish pdf people/alice --template brief --output ./alice.pdf
```

### RSS Feed

```bash
# Generate RSS feed
gbrain publish rss --output feed.xml

# Private feed with token
gbrain publish rss --output feed.xml --token secret123
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--output <path>` | Output file or directory | `stdout` |
| `--domain <domain>` | Custom domain for web publish | `none` |
| `--template <name>` | Template to use | `default` |
| `--token <token>` | Auth token for private feeds | `none` |
| `--dry-run` | Preview without publishing | `false` |

## Examples

### Generate Public Page

```bash
# Create a public profile page
gbrain publish web people/alice --domain alice.example.com

# Preview what would be published
gbrain publish web people/alice --dry-run
```

### Backup to Markdown

```bash
# Full brain export
gbrain publish markdown ~/.gbrain/exports/$(date +%Y%m%d)/

# Incremental export since last sync
gbrain publish markdown ./exports/ --since 2024-03-01
```

### Create Deal Sheet

```bash
gbrain publish pdf deals/acme-seed --template deal-sheet --output ./acme-sheet.pdf
```

## See Also

- {doc}`sync` - Synchronization
- {doc}`report` - Report generation
- {doc}`../skills/publish` - Publishing skill details
