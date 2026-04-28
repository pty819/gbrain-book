# Storage Engines

GBrain supports two pluggable storage engines through the `BrainEngine` interface.

## Engine Overview

| Engine | Type | Use Case | Setup Time |
|--------|------|----------|------------|
| **PGLite** | Embedded WASM | Local, dev, <1000 files | 2 seconds |
| **Postgres** | Server-based | Production, 1000+ files | ~2 minutes |

## PGLite Engine

**PGLite** is an embedded Postgres 17.5 running via WebAssembly. It's the default engine and requires no external database.

### Features

- Zero-config, ready in 2 seconds
- Full Postgres compatibility
- In-memory with optional persistence
- Perfect for development and small-scale deployments

### Configuration

```bash
gbrain init  # Defaults to PGLite
```

### Technical Details

- Uses `pglite-engine.ts` implementation
- Schema loaded from `pglite-schema.ts`
- Supports pgvector for vector search
- Supports pg_trgm for fuzzy text search

## Postgres Engine

**Postgres** with pgvector extension is recommended for production use with large brains.

### Features

- Horizontal scaling via connection pooling
- Multi-machine sync support
- pgvector for semantic search
- Full-text search with ranking
- JSONB for structured data

### Configuration

```bash
# Self-hosted
gbrain init --engine postgres --connection-string "postgresql://..."

# Supabase
gbrain init --engine supabase --url "https://xxx.supabase.co" --key "xxx"
```

### Connection Management

The Postgres engine uses `src/core/db.ts` for connection management with:
- Statement timeout (default: 5 minutes)
- Idle transaction timeout (default: 5 minutes)
- Configurable pool size via `GBRAIN_POOL_SIZE`

## Engine Factory

The engine factory (`src/core/engine-factory.ts`) dynamically imports the configured engine:

```typescript
import { createEngine } from './engine-factory';

// Returns PgliteEngine or PostgresEngine based on config
const engine = await createEngine('pglite');
const engine = await createEngine('postgres', { connectionString: '...' });
```

## Engine Selection Guide

Use this decision tree:

```{mermaid}
graph TD
    A[How many files?] --> B{>1000?}
    B -->|Yes| C[Use Postgres]
    B -->|No| D[Concurrent users?]
    D -->|Yes| C
    D -->|No| E[Multi-machine?]
    E -->|Yes| C
    E -->|No| F[Use PGLite]
```

## See Also

- {doc}`../commands/migrate` - Switching engines
- {doc}`../commands/doctor` - Engine health checks
- {doc}`../guides/engine-selection` - Detailed comparison