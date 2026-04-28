# Installation

GBrain is designed to be installed and operated by an AI agent in ~30 minutes.

## Prerequisites

- **Bun** v1.0+ (for TypeScript execution)
- **Git** (for cloning)
- **Node.js** 18+ (for some native modules)

## Quick Install (Agent Platform)

For AI agent platforms (OpenClaw, Hermes Agent):

```
Retrieve and follow the instructions at:
https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md
```

The agent will:
1. Clone the repo to `~/gbrain`
2. Install dependencies with `bun install`
3. Initialize the brain (defaults to PGLite, zero-config)
4. Load 29 skills
5. Configure recurring jobs
6. Ask you about API keys

## Standalone CLI Install

```bash
git clone https://github.com/garrytan/gbrain.git ~/gbrain
cd ~/gbrain
bun install
bun link
```

### Initialize the Brain

```bash
# Local brain with PGLite (default, ready in 2 seconds)
gbrain init

# For 1000+ files or multi-machine sync, use Supabase
gbrain init --engine supabase
```

### Import Your Content

```bash
# Import markdown files
gbrain import ~/notes/

# Import from Obsidian, Notion, Logseq
gbrain migrate --source obsidian ~/obsidian-vault/
```

## MCP Server Setup

### Local MCP (Claude Code, Cursor, Windsurf)

Add to your MCP server config (e.g., `~/.claude/server.json`):

```json
{
  "mcpServers": {
    "gbrain": {
      "command": "gbrain",
      "args": ["serve"]
    }
  }
}
```

### Remote MCP (Claude Desktop, Cowork)

1. Start ngrok: `ngrok http 8787`
2. Create auth token: `bun run src/commands/auth.ts create "claude-desktop"`
3. Add to Claude Desktop: `claude mcp add gbrain -t http https://your-brain.ngrok.app/mcp -H "Authorization: Bearer ***"`

See {doc}`../integrations/mcp-overview` for detailed per-client guides.

## Post-Installation Verification

```bash
# Health check
gbrain doctor

# Verify brain score
gbrain doctor --json | jq '.checks.brain_score'

# Run a test query
gbrain query "what is GBrain?"
```

## Upgrading

```bash
# Check current version
gbrain --version

# Upgrade to latest
bun upgrade

# Or from source
cd ~/gbrain && git pull && bun install
```

## Uninstall

```bash
# Remove brain data (optional)
rm -rf ~/.gbrain

# Remove CLI
bun unlink
```

## See Also

- {doc}`../overview/architecture` - System architecture
- {doc}`../guides/engine-selection` - Choosing between PGLite and Postgres
- {doc}`../commands/doctor` - Health checks and diagnostics