# Idea Ingest

Ingest links, articles, and tweets into brain.

## Purpose

Converts external content (articles, links, tweets) into brain pages with proper entity linking and citations.

## Preconditions

- URL or content available
- Author identified (for articles)

## Steps

1. **Fetch** — Retrieve content from URL
2. **Parse** — Extract text, metadata, author
3. **Enrich** — Identify people, companies, topics
4. **Write** — Create brain page in `originals/` or `articles/`
5. **Link** — Create entity links
6. **Cite** — Add source citation

## Author People Page

Every ingested article must have an author people page:
- Create `people/author-name` if doesn't exist
- Link article to author
- Add to author's timeline

## Filing Rules

- Original articles → `originals/`
- Curated links → `links/`
- Tweets → `signals/twitter/`

## Quality Gates

- Author people page exists or created
- All entities linked
- Source citation present
- Backlink from article to author

## See Also

- {doc}`../skills/ingest` - Router skill
- {doc}`../skills/media-ingest` - Media ingestion
- {doc}`../skills/enrich` - Entity enrichment