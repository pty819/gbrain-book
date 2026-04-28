# Operations Contract

GBrain's operations are defined contract-first in `src/core/operations.ts`. This single source powers both the CLI and MCP server.

## Operation Categories

### Brain Operations

| Operation | Description |
|-----------|-------------|
| `put_page` | Create or update a brain page |
| `get_page` | Retrieve a page by slug |
| `delete_page` | Remove a page |
| `list_pages` | List pages with filters |
| `search` | Hybrid search across all content |
| `search_keyword` | Keyword BM25 search |
| `search_vector` | Vector similarity search |

### Link Operations

| Operation | Description |
|-----------|-------------|
| `add_links` | Add typed links between pages |
| `add_links_batch` | Bulk add links |
| `get_links` | Get outgoing/incoming links |
| `get_backlinks` | Get pages linking to a page |
| `find_orphans` | Find pages with no inbound links |

### Timeline Operations

| Operation | Description |
|-----------|-------------|
| `add_timeline_entries` | Add timeline events |
| `add_timeline_entries_batch` | Bulk add timeline events |
| `get_timeline` | Get timeline for a page |

### Embedding Operations

| Operation | Description |
|-----------|-------------|
| `embed_page` | Generate embeddings for a page |
| `embed_pages` | Bulk embed multiple pages |
| `search_similar` | Find similar content |

### File Operations

| Operation | Description |
|-----------|-------------|
| `file_upload` | Upload file with safety checks |
| `file_download` | Download file |
| `file_delete` | Delete file |

### Sync Operations

| Operation | Description |
|-----------|-------------|
| `sync_page` | Sync a single page |
| `sync_all` | Full brain sync |
| `sync_status` | Get sync status |

## Operation Context

Every operation receives an `OperationContext`:

```typescript
interface OperationContext {
  remote: boolean;        // true for MCP callers, false for CLI
  cliOpts?: CliOptions;   // CLI flags (quiet, progress, etc.)
  userId?: string;        // User identifier
  timestamp: Date;        // Operation timestamp
}
```

### Trust Boundary

The `remote` flag enforces security:
- `remote: false` (CLI): Full access, default safe behavior
- `remote: true` (MCP): Tightened filesystem confinement

## Upload Validators

Operations exports upload validators:
- `validateUploadPath`: Checks file path safety
- `validatePageSlug`: Ensures slug format
- `validateFilename`: Validates filename characters

## See Also

- `src/core/operations.ts` - Full operations contract
- {doc}`../commands/cli-overview` - CLI command mapping
- {doc}`../concepts/engines` - Engine interface