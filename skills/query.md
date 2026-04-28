# Query

3-layer search with synthesis and citations.

## Purpose

Provides comprehensive answers by searching the brain and synthesizing information from multiple pages.

## Search Layers

### Layer 1: Recall
- Hybrid search (vector + keyword)
- Graph-boosted ranking
- Source-aware ranking

### Layer 2: Synthesis
- Aggregate multiple relevant pages
- Identify consensus
- Note contradictions

### Layer 3: Response
- Synthesize into coherent answer
- Cite all sources
- Note knowledge gaps

## Preconditions

- Query provided by user
- Brain has relevant content (or confirmed lack)

## Response Format

```
Based on the brain:

[Synthesized answer]

Sources:
- [Page 1](slug) - relevance score
- [Page 2](slug) - relevance score

Knowledge gaps:
- The brain doesn't have info on [topic]
```

## The "Don't Hallucinate" Rule

If brain doesn't have information:
> "The brain doesn't have information on X"

NEVER make up facts. Always admit what you don't know.

## Quality Gates

- All cited pages actually exist
- Synthesis logically follows from sources
- Gaps explicitly noted

## See Also

- {doc}`../skills/brain-ops` - Brain-first lookup
- {doc}`../concepts/search-ranking` - Search architecture
- {doc}`../commands/query` - Query CLI command