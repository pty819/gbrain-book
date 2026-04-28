# Signal Detector

**Always-on** skill that fires on every message.

## Purpose

Captures original thinking and entity mentions as they happen, enabling the brain to compound knowledge without explicit user prompts.

## How It Works

```{mermaid}
graph LR
    A[User Message] --> B[Spawn Cheap Model<br/>Parallel, Non-blocking]
    B --> C[Extract Ideas]
    B --> D[Extract Entities]
    C --> E[Write to brain]
    D --> E
```

Signal detector runs in parallel — never blocks the main response. A cheap model (Haiku) extracts:
- Original ideas or insights
- Entity mentions (people, companies, topics)
- Sentiment and context

## Trigger

Always active. No explicit trigger needed.

## Outputs

- New pages in `signals/` directory
- Entity links to existing people/company pages
- Timelines updated for relevant entities

## Configuration

No configuration required. Always-on by default.

## Quality Gates

- Extract at least one idea per message
- Link entities to existing pages when possible
- Create stub pages for new entities (Tier 3)

## See Also

- {doc}`../skills/brain-ops` - Brain-first lookup
- {doc}`../skills/ingest` - Content ingestion router