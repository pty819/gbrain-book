# Repo Architecture

Determines where new brain pages should be filed.

## Purpose

Ensures consistent organization by routing new pages to the correct directory based on primary subject.

## Filing Decision Tree

```{mermaid}
graph TD
    A[New Page] --> B{Primary Subject?}
    B -->|Person| C[people/]
    B -->|Company| D[companies/]
    B -->|Deal| E[deals/]
    B -->|Topic| F[concepts/]
    B -->|Project| G[projects/]
    B -->|Writing| H[writing/]
    B -->|Original| I[originals/]
    B -->|Meeting| J[meetings/]
```

## Primary Subject Rule

**Directory is determined by primary subject, not format.**

- A meeting note with analysis → `meetings/` (primary: meeting)
- A concept explained via examples → `concepts/` (primary: topic)
- A person's thoughts on a topic → `people/` (primary: person)

## Filing Rules

| Subject | Directory |
|---------|-----------|
| Person | `people/` |
| Company | `companies/` |
| Deal/Investment | `deals/` |
| Topic/Concept | `concepts/` |
| Project | `projects/` |
| Original Writing | `writing/` |
| Curated Article | `originals/` |
| Meeting | `meetings/` |
| Event | `events/` |
| Daily Notes | `daily/` |

## See Also

- {doc}`../skills/repo-architecture` - Filing rules
- {doc}`../skills/brain-filing-rules` - Cross-cutting rules