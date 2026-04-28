# Migrate

Migrates data between engines or applies schema migrations.

## Synopsis

```bash
gbrain migrate <subcommand> [flags]
```

## Subcommands

### Switch Engines

```bash
# Migrate from PGLite to Postgres/Supabase
gbrain migrate --to supabase --url "https://xxx.supabase.co" --key "xxx"

# Migrate from Postgres to PGLite
gbrain migrate --to pglite

# Migrate between Supabase projects
gbrain migrate --to supabase --url "https://yyy.supabase.co" --key "yyy"
```

### Apply Schema Migrations

```bash
gbrain migrate --apply
gbrain migrate --apply --yes
```

### Export/Import

```bash
# Export brain to file
gbrain migrate --export ./backup.tar.gz

# Import brain from file
gbrain migrate --import ./backup.tar.gz
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--to <engine>` | Target engine (`pglite`, `supabase`, `postgres`) | `none` |
| `--url <url>` | Supabase URL (for Supabase target) | `none` |
| `--key <key>` | Supabase anon key (for Supabase target) | `none` |
| `--apply` | Apply pending schema migrations | `false` |
| `--yes` | Skip confirmation prompts | `false` |
| `--export <path>` | Export brain to file | `none` |
| `--import <path>` | Import brain from file | `none` |

## Migration Path

```
PGLite <-> Postgres <-> Supabase
```

All migrations are bidirectional and lossless. The migration exports:
- All pages and metadata
- Vector embeddings
- Links and relationships
- Tags and timeline entries
- Configuration

## Examples

### Move to Supabase for Production

```bash
# 1. Create Supabase project
# 2. Enable pgvector extension in Supabase dashboard
# 3. Migrate
gbrain migrate \
  --to supabase \
  --url "https://xxx.supabase.co" \
  --key "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Move Back to PGLite

```bash
gbrain migrate --to pglite
```

### Backup and Restore

```bash
# Create backup
gbrain migrate --export ~/gbrain-backup-$(date +%Y%m%d).tar.gz

# Restore from backup
gbrain migrate --import ~/gbrain-backup-20240315.tar.gz
```

## Post-Migration

After migration, verify integrity:

```bash
gbrain doctor
gbrain embed --stale  # Regenerate any missing embeddings
```

## See Also

- {doc}`../concepts/engines` - Engine details
- {doc}`doctor` - Health verification
- {doc}`embed` - Embedding regeneration
