# Code-Def

Indexes code definitions and generates a code knowledge base.

## Synopsis

```bash
gbrain code-def [subcommand] [flags]
```

## Description

The `code-def` command extracts and indexes code definitions from your projects, enabling code-aware search and intelligence.

## Subcommands

### Index

```bash
gbrain code-def index ./src/
gbrain code-def index ./src/ --language typescript
```

Indexes code files and extracts definitions.

### Search

```bash
gbrain code-def search "function name"
gbrain code-def search "ClassName" --type class
```

Searches indexed code definitions.

### List

```bash
gbrain code-def list
gbrain code-def list --language python
```

Lists all indexed code definitions.

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--language <lang>` | Filter by language | `none` |
| `--type <type>` | Filter by type (`function`, `class`, `interface`) | `none` |
| `--project <path>` | Project path to index | `current` |

## Supported Languages

- TypeScript / JavaScript
- Python
- Go
- Rust
- Java
- C / C++
- Ruby

## Examples

### Index a Project

```bash
# Index entire project
gbrain code-def index .

# Index specific language
gbrain code-def index ./src/ --language typescript

# Multiple projects
gbrain code-def index ./src/ ./libs/
```

### Search Code

```bash
# Find a function
gbrain code-def search "parseConfig"

# Find classes
gbrain code-def search "BrainEngine" --type class
```

### List by Language

```bash
# List all TypeScript definitions
gbrain code-def list --language typescript

# List all functions
gbrain code-def list --type function
```

## Integration with Brain

Code definitions are linked to:
- Documentation pages that reference them
- People who authored them (via git blame)
- Projects they belong to

## See Also

- {doc}`search` - Search operations
- {doc}`query` - Query operations
- {doc}`../guides/skill-development` - Skill development
