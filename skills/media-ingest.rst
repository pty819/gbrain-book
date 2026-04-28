# Media Ingest

Ingest video, audio, PDF, and book content.

## Purpose

Converts multimedia content into brain pages with transcription and entity extraction.

## Supported Types

| Type | Processing |
|------|------------|
| Video (YouTube, etc.) | Transcribe → Extract |
| Audio | Transcribe → Extract |
| PDF | OCR/text extraction |
| Book | Chapter extraction |
| Screenshot | OCR via LLM |

## Preconditions

- Media file or URL available
- Appropriate processing tool available

## Steps

1. **Download** — Fetch media file
2. **Transcribe** — Convert to text (Groq Whisper default)
3. **Extract** — Pull entities, topics, quotes
4. **Write** — Create brain page with transcript
5. **Link** — Connect entities
6. **Propagate** — Update relevant timelines

## Transcription

Default provider: Groq Whisper (fast, accurate)
Fallback: OpenAI Whisper

For files >25MB, ffmpeg segmentation is applied.

## Entity Extraction

Extract from transcript:
- People mentioned
- Companies referenced
- Topics discussed
- Key quotes

## Quality Gates

- Transcript complete
- Entities linked to existing pages
- Timestamps preserved for video/audio

## See Also

- {doc}`../skills/meeting-ingestion` - Meeting transcripts
- {doc}`../skills/ingest` - Router skill
- {doc}`../skills/enrich` - Entity enrichment