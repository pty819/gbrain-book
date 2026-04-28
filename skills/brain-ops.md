# Brain-Ops

**Always-on** skill for brain-first lookup.

## Purpose

Ensures every response is grounded in existing brain knowledge before making external API calls.

## The Loop

```{mermaid}
graph LR
    A[User Query] --> B{GBrain has<br/>info?}
    B -->|Yes| C[Lookup brain]
    B -->|No| D[External API]
    C --> E[Enrich with new info]
    D --> F[Update brain]
    E --> G[Respond]
    F --> G
```

## Preconditions

- None (always runs first)

## Steps

1. **Lookup** — Run `gbrain query` or `gbrain get` for the topic
2. **Ground** — Build response from existing knowledge
3. **Enrich** — If external API was needed, write findings back
4. **Attribute** — Cite sources in response

## Quality Gates

- Response must reference brain pages
- New information written back within 1 exchange
- Source attribution on all external claims

## Convention: Brain-First

This skill enforces the brain-first convention:
1. Always lookup brain before external API
2. Write findings back after external calls
3. Attribute all sources

## See Also

- {doc}`../skills/signal-detector` - Always-on capture
- {doc}`../skills/query` - Search and synthesis