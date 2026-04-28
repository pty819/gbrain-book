# Maintain

Periodic brain health maintenance.

## Purpose

Runs scheduled maintenance to keep the brain healthy: stale pages, orphans, dead links, citation audit, back-link enforcement.

## Maintenance Tasks

### Stale Pages
- Pages without updates in 90+ days
- Mark as stale or archive

### Orphans
- Pages with zero inbound links
- Find or create relevant links

### Dead Links
- Links to non-existent pages
- Fix or remove

### Citation Audit
- Missing citations on claims
- Malformed citation formats
- Fix using citation-fixer skill

### Back-link Enforcement
- Pages that should link but don't
- Apply Iron Law: if A links B, B links A

## Schedule

Run via cron-scheduler:
- Weekly: Full maintenance cycle
- Daily: Stale check, orphans

## Running Maintenance

```bash
# Full maintenance
gbrain maintain

# Specific task
gbrain maintain --task orphans
gbrain maintain --task dead-links

# Dry run
gbrain maintain --dry-run
```

## See Also

- {doc}`../skills/cron-scheduler` - Scheduling
- {doc}`../skills/citation-fixer` - Citation fixes
- {doc}`../commands/orphans` - Orphan detection