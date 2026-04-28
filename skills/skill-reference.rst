# Skill Reference

GBrain ships with 29 built-in skills organized by category.

## Skill Overview

| Category | Skills |
|----------|--------|
| **Always-on** | signal-detector, brain-ops |
| **Content Ingestion** | ingest, idea-ingest, media-ingest, meeting-ingestion |
| **Brain Operations** | enrich, query, maintain, citation-fixer, repo-architecture, publish, data-research |
| **Operational** | daily-task-manager, daily-task-prep, cron-scheduler, reports, cross-modal-review, webhook-transforms, testing, skill-creator, skillify, skillpack-check, smoke-test, minion-orchestrator |
| **Identity & Setup** | soul-audit, setup, migrate, briefing |
| **Conventions** | conventions/quality, conventions/brain-first, conventions/model-routing, conventions/test-before-bulk, conventions/cross-modal |

## Conventions

Cross-cutting rules applied across all skills:

### Quality Conventions (`skills/conventions/quality.md`)
- Citations required for external claims
- Back-links required (Iron Law)
- Notability gate for mentions
- Source attribution mandatory

### Brain-First Conventions (`skills/conventions/brain-first.md`)
1. Check brain before external API
2. Use gbrain search, gbrain get
3. Write findings back to brain
4. Attribute all sources

### Model Routing (`skills/conventions/model-routing.md`)
- Cheap models for classification
- Mid-tier for structured extraction
- Best model for synthesis

### Test Before Bulk (`skills/conventions/test-before-bulk.md`)
- Test 3-5 items before batch
- Catch errors early
- Adjust prompt if needed

## Skill Manifest

Each skill is registered in `skills/manifest.json`:

```json
{
  "skills": [
    {
      "name": "idea-ingest",
      "description": "Ingest links, articles, tweets",
      "triggers": ["ingest link", "add article"],
      "conventions": ["quality/citations"]
    }
  ]
}
```

## Creating Skills

See {doc}`../guides/skill-development` for the full skill creation workflow.

## See Also

- {doc}`../concepts/skills-system` - Skills philosophy
- {doc}`../skills/skill-creator` - Create new skills
- {doc}`../skills/skillify` - Skillify meta-skill