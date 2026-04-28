# Skills System

GBrain's intelligence lives in its **skills** — fat markdown files that encode entire workflows.

## Philosophy: Thin Harness, Fat Skills

```{mermaid}
graph TB
    subgraph "GBrain Runtime (Thin)"
        CORE[Core Engine<br/>Search, Embed, Import]
        OPS[Operations Contract]
        CLI[CLI + MCP]
    end
    
    subgraph "Skills (Fat)"
        SK1[Signal Detector]
        SK2[Brain-Ops]
        SK3[Ingest]
        SK4[Enrich]
        SK5[Query]
    end
    
    CORE --> SK1
    CORE --> SK2
    CORE --> SK3
    CORE --> SK4
    CORE --> SK5
```

The runtime provides bindings to deterministic code (search, embed, import). The intelligence — when to use what, how to chain, quality bars — lives in the skills.

## Skill Structure

Every skill is a markdown file with YAML frontmatter:

```yaml
---
name: skill-name
description: What this skill does
triggers:
  - "ingest a link"
  - "add article to brain"
writes_pages:
  - "articles/slug"
writes_to:
  - "people/author"
conventions:
  - "quality/citations"
---
```

### Required Sections

1. **Frontmatter**: Metadata, triggers, conventions
2. **Purpose**: What the skill does
3. **Preconditions**: What must be true before running
4. **Steps**: The workflow (numbered)
5. **Quality gates**: How to verify success

## Skill Resolver

`skills/RESOLVER.md` (or `AGENTS.md`) routes intents to skills:

```markdown
## Intent Routing

| Trigger Pattern | Skill |
|-----------------|-------|
| ingest link/article | idea-ingest |
| transcribe meeting | meeting-ingestion |
| enrich person/company | enrich |
```

## Built-in Skills (29 total)

### Always-On
- **signal-detector**: Fires on every message, captures ideas + entities
- **brain-ops**: Brain-first lookup before any external API

### Content Ingestion
- **ingest**: Router that delegates to right ingestion skill
- **idea-ingest**: Links, articles, tweets → brain pages
- **media-ingest**: Video, audio, PDF, books
- **meeting-ingestion**: Transcripts with attendee enrichment

### Brain Operations
- **enrich**: Tiered enrichment (Tier 1/2/3)
- **query**: 3-layer search with synthesis
- **maintain**: Periodic health checks
- **citation-fixer**: Fix missing/malformed citations
- **repo-architecture**: Where files go
- **publish**: Share pages as password-protected HTML
- **data-research**: YAML recipes for structured research

### Operational
- **daily-task-manager**: Task lifecycle (P0-P3)
- **daily-task-prep**: Morning prep with calendar
- **cron-scheduler**: Quiet hours, staggering, idempotency
- **reports**: Timestamped reports
- **cross-modal-review**: Second-model quality gate
- **webhook-transforms**: External events → brain signals
- **testing**: Validates skill conformance
- **skill-creator**: Create MECE-conforming skills
- **skillify**: Meta-skill for skill development
- **skillpack-check**: Health report for CI
- **smoke-test**: 8 health checks
- **minion-orchestrator**: Background work via jobs

### Identity & Setup
- **soul-audit**: Generate identity docs
- **setup**: Auto-provision PGLite or Supabase
- **migrate**: Import from Obsidian, Notion, etc.
- **briefing**: Daily briefing

## Creating Custom Skills

```bash
# Scaffold a new skill
gbrain skillify scaffold my-skill

# Check conformance
gbrain skillify check scripts/my-skill.ts
```

See {doc}`../guides/skill-development` for the full workflow.

## See Also

- {doc}`../guides/skill-development` - Skill creation guide
- {doc}`../skills/skill-creator` - Skill creator skill
- {doc}`../skills/skillify` - Skillify meta-skill