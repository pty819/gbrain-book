# Meeting Ingestion

Ingest meeting transcripts with attendee enrichment.

## Purpose

Converts meeting transcripts into brain pages with automatic attendee linking and company timelines.

## Preconditions

- Meeting transcript available
- Attendees identified

## Steps

1. **Parse** — Extract transcript, attendees, date
2. **Identify** — Match attendees to people pages
3. **Enrich attendees** — Run enrich skill for each
4. **Enrich companies** — Update company timelines
5. **Write** — Create meeting page
6. **Link** — Create attended links

## Attendee Enrichment Chain

For each attendee:
1. Check if people page exists
2. If not, create stub
3. Run Tier 2 enrichment (8+ mentions or meeting)
4. Link person to meeting

## Company Timeline Updates

If attendees are linked to companies:
1. Add timeline entry for meeting
2. Update company's last_contact field
3. Check for deal/progress updates

## Filing Rules

- Meetings → `meetings/YYYY-MM-DD-title/`
- Recurring → `meetings/recurring/title/`

## Quality Gates

- All attendees linked to people pages
- Company timelines updated
- Transcript preserved
- Key decisions noted

## See Also

- {doc}`../skills/media-ingest` - Media processing
- {doc}`../skills/enrich` - Entity enrichment
- {doc}`../skills/briefing` - Daily briefing