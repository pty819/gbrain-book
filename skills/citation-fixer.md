# Citation Fixer

Scans and fixes citation issues.

## Purpose

Ensures all external claims have proper citations and fixes malformed ones.

## What It Fixes

### Missing Citations
- Claims without source attribution
- Statistics without citations
- Quotes without sources

### Malformed Citations
- Wrong format (use standard)
- Incomplete info (author, date, URL)
- Broken links

## Citation Standard

```
[Source: Author, Publication, Date](url)
```

Examples:
```
[Source: Paul Graham, YC Blog, 2013](http://paulgraham.com/scale.html)
[Source: Reuters, 2024-01-15](https://reuters.com/article)
```

## Preconditions

- Page to audit provided
- Citation standards loaded

## Steps

1. **Scan** — Find claims needing citations
2. **Match** — Find appropriate source
3. **Fix** — Insert proper citation format
4. **Verify** — Ensure citation is complete

## Quality Gates

- All claims have citations
- Citation format matches standard
- Links are valid

## See Also

- {doc}`../skills/maintain` - Maintenance runner
- {doc}`../skills/conventions` - Citation conventions