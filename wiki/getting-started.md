# Getting Started with Legroom

This guide will help you get up and running with Legroom in under 5 minutes.

## Installation

**CLI on macOS Apple Silicon/Linux with uv:**

```bash
uv tool install --python 3.13 "legroom-ai[all]"
legroom --version
```

Use `uv tool update-shell` if the install succeeds but `legroom` is not on
`PATH`.

**Python project / virtualenv:**

```bash
# Core package (minimal dependencies)
pip install legroom-ai

# With proxy server
pip install "legroom-ai[proxy]"

# With semantic relevance (for smarter compression)
pip install "legroom-ai[relevance]"

# Everything
pip install "legroom-ai[all]"
```

**TypeScript / Node.js:**

```bash
npm install legroom-ai
```

**Docker-native:**

```bash
curl -fsSL https://raw.githubusercontent.com/ghaliba3/legroom/main/scripts/install.sh | bash
```

PowerShell:

```powershell
irm https://raw.githubusercontent.com/ghaliba3/legroom/main/scripts/install.ps1 | iex
```

See [Docker-native install](docker-install.md) for wrapper behavior, compose usage, and host-integrated `wrap` flows.

If you want Legroom to stay up in the background and automatically serve supported tools, use [Persistent Installs](persistent-installs.md):

```bash
legroom install apply --preset persistent-service --providers auto
```

## Quick Start: Proxy Mode (Recommended)

The easiest way to use Legroom is as a proxy server:

```bash
# Start the proxy
legroom proxy --port 8787
```

Then point your LLM client at it:

```bash
# Claude Code
ANTHROPIC_BASE_URL=http://localhost:8787 claude

# GitHub Copilot CLI (default Anthropic-style proxy route)
legroom wrap copilot -- --model claude-sonnet-4-20250514

# OpenAI-compatible clients
OPENAI_BASE_URL=http://localhost:8787/v1 your-app
```

That's it! All your requests now go through Legroom and get optimized automatically.

## Quick Start: Python SDK

If you want programmatic control:

```python
from legroom import LegroomClient
from openai import OpenAI

# Create a wrapped client
client = LegroomClient(
    original_client=OpenAI(),
    default_mode="optimize",
)

# Use exactly like the original
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
```

## Modes

### Audit Mode

Observe without modifying:

```python
client = LegroomClient(
    original_client=OpenAI(),
    default_mode="audit",
)
# Logs metrics but doesn't change requests
```

### Optimize Mode

Apply transforms to reduce tokens:

```python
client = LegroomClient(
    original_client=OpenAI(),
    default_mode="optimize",
)
# Compresses tool outputs, aligns cache prefixes, etc.
```

### Simulate Mode

Preview what optimizations would do:

```python
plan = client.chat.completions.simulate(
    model="gpt-4o",
    messages=[...],
)
print(f"Would save {plan.tokens_saved} tokens")
print(f"Transforms: {plan.transforms_applied}")
```

## Next Steps

- [Proxy Server Documentation](proxy.md) - Configure the proxy
- [Transforms Reference](transforms.md) - Understand each transform
- [API Reference](api.md) - Full API documentation
