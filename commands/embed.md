# Embed

Generates and manages vector embeddings for your brain content.

## Synopsis

```bash
gbrain embed [flags]
gbrain embed <slug> [slug...]
```

## Description

The `embed` command generates vector embeddings for pages in your brain. Embeddings enable semantic search, allowing you to find content by meaning rather than just keywords.

## How Embeddings Work

When you add content to GBrain:

1. Content is split into chunks (paragraphs, sections)
2. Each chunk is sent to an embedding model (OpenAI `text-embedding-3-small` by default)
3. Embeddings are stored alongside chunks in the database
4. Search queries are embedded and matched against stored embeddings

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--stale` | Regenerate embeddings for pages without them | `false` |
| `--all` | Regenerate all embeddings | `false` |
| `--force` | Force regeneration even for up-to-date content | `false` |
| `--workers <n>` | Number of parallel embedding workers | `4` |

## Examples

### Embed New Content

```bash
# Embed a specific page
gbrain embed people/alice

# Embed multiple pages
gbrain embed people/alice companies/acme deals/acme-seed
```

### Regenerate Stale Embeddings

```bash
# Find and embed pages missing embeddings
gbrain embed --stale

# Force regenerate all
gbrain embed --all --force
```

### Parallel Embedding

```bash
# Use more workers for faster processing
gbrain embed --stale --workers 8
```

## Configuration

### Embedding Model

Configure the embedding model in `~/.gbrain/config.json`:

```json
{
  "embedding": {
    "model": "text-embedding-3-small",
    "dimensions": 1536
  }
}
```

Supported models:
- `text-embedding-3-small` (default, 1536 dims)
- `text-embedding-3-large` (3072 dims)
- `text-embedding-ada-002` (legacy)

### API Key

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-...
# or
gbrain config set OPENAI_API_KEY "$OPENAI_API_KEY"
```

## Troubleshooting

### Missing Embeddings

If search returns no results, regenerate embeddings:

```bash
gbrain embed --stale
```

### Rate Limiting

If you hit API rate limits, reduce workers:

```bash
gbrain embed --stale --workers 1
```

## See Also

- {doc}`search` - Search operations
- {doc}`query` - Query operations
- {doc}`../concepts/search-ranking` - How search ranking works
