# Knowledge Graph

GBrain's knowledge graph is the self-wiring layer that makes every page part of a connected whole.

## Graph Architecture

```{mermaid}
graph LR
    A[Person Page] -->|works_at| B[Company Page]
    C[Company Page] -->|invested_in| D[Deal Page]
    E[Person Page] -->|founded| B
    F[Person Page] -->|attended| G[Event Page]
    H[Person Page] -->|advises| B
```

## Link Types

GBrain extracts and creates typed links automatically on every page write:

| Link Type | Meaning | Example |
|-----------|---------|---------|
| `attended` | Person attended event | Alice attended YC W24 |
| `works_at` | Person employed at company | Bob works at Acme |
| `invested_in` | Investor placed in deal | Alice invested in Acme |
| `founded` | Person started company | Alice founded Acme |
| `advises` | Person advises company | Alice advises Acme |
| `source` | Content source | Source: arstechnica.com |
| `mentions` | Reference to entity | Mentions: Alice |

## Auto-Link Extraction

On every `put_page` operation, GBrain:

1. Parses markdown and wikilinks from body text
2. Extracts entity references via `extractEntityRefs()`
3. Infers link type via `inferLinkType()` heuristics
4. Creates typed links with zero LLM calls

### Supported Formats

- Markdown: `[Name](people/slug)`
- Wikilinks: `[[people/slug|Name]]`
- Obsidian-style: `[[slug|Display Text]]`

## Graph Queries

```bash
# Who works at Acme?
gbrain graph-query "acme" --type works_at

# Who invested in this deal?
gbrain graph-query "deal-slug" --type invested_in

# Full relationship map
gbrain graph-query "alice" --depth 2
```

## Backlink Enforcement

The **Iron Law** of GBrain: if page A links to page B, page B should backlink to page A.

```{mermaid}
graph LR
    A[Page A] -->|links to| B[Page B]
    B -->|backlinks to| A
```

Use `gbrain backlinks check` to audit and `gbrain backlinks fix` to repair.

## Knowledge Graph in Search

Links boost ranking:
- Pages with more quality backlinks rank higher
- Entity co-occurrence affects relevance
- Temporal queries respect graph structure

## See Also

- {doc}`../commands/graph-query` - Relationship traversal
- {doc}`../commands/backlinks` - Backlink management
- {doc}`../concepts/search-ranking` - Graph in search