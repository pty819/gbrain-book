# Dream

Uses AI to generate insights and connections from your brain content.

## Synopsis

```bash
gbrain dream [flags]
gbrain dream <topic>
```

## Description

The `dream` command applies AI synthesis to your brain content, finding patterns, generating hypotheses, and creating connections between disparate pieces of knowledge.

## How It Works

1. Collects relevant pages and chunks from your brain
2. Identifies patterns and connections
3. Applies synthesis prompting to generate insights
4. Optionally writes findings back to a new brain page

## Use Cases

### Explore a Topic

```bash
# Explore a topic across your brain
gbrain dream "What themes emerge in my research on AI agents?"

# Find connections between concepts
gbrain dream "Connect my notes on startups with my notes on machine learning"
```

### Generate Hypotheses

```bash
# Generate testable hypotheses
gbrain dream --hypothesize "What predictions can I make about the AI industry?"

# Find gaps in knowledge
gbrain dream --gaps "What should I learn more about for my startup?"
```

### Summarize and Synthesize

```bash
# Create a summary document
gbrain dream --summarize --output synthesis.md

# Generate a briefing on a person
gbrain dream --person alice --output people/alice-briefing.md
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--topic <text>` | Topic or question to explore | `none` |
| `--hypothesize` | Generate hypotheses mode | `false` |
| `--gaps` | Identify knowledge gaps | `false` |
| `--summarize` | Create summary document | `false` |
| `--person <slug>` | Generate briefing on person | `none` |
| `--output <path>` | Write output to file | `stdout` |
| `--model <name>` | AI model to use | `gpt-4o` |
| `--max-pages <n>` | Max pages to analyze | `50` |

## Examples

### Creative Exploration

```bash
gbrain dream "What surprising connections exist between my favorite films and my work?"
```

### Investment Research

```bash
gbrain dream --topic "Synthesize my due diligence on AI infrastructure startups"
```

### Personal Briefing

```bash
# Generate briefing before meeting
gbrain dream --person alice --output /tmp/alice-briefing.md
cat /tmp/alice-briefing.md
```

## Models

Configure the AI model in `~/.gbrain/config.json`:

```json
{
  "dream": {
    "model": "gpt-4o",
    "temperature": 0.7
  }
}
```

## See Also

- {doc}`query` - Search and query operations
- {doc}`report` - Generate reports
- {doc}`../skills/brain-ops` - Brain operations
