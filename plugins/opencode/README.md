# legroom-opencode

OpenCode integration helpers for Legroom. The package supports two integration paths:

1. Provider config helpers used by `legroom wrap opencode` and persistent installs.
2. A native OpenCode plugin that installs Legroom transport interception and exposes the retrieve tool.

## Install

```bash
npm install legroom-opencode
```

## Provider Config Helpers

Use these helpers when you need to generate OpenCode config that routes a `legroom` provider through a running Legroom proxy.

```ts
import {
  buildOpencodeConfigContent,
  createLegroomProvider,
} from "legroom-opencode";

const provider = createLegroomProvider({ proxyPort: 8787 });
const config = buildOpencodeConfigContent({
  proxyPort: 8787,
  defaultModel: "claude-sonnet-4-6",
});

console.log(provider.provider.legroom.npm);
console.log(config.model);
```

The generated provider uses `@ai-sdk/openai-compatible` and points model requests at `http://127.0.0.1:<port>/v1`.

## Native OpenCode Plugin

Use `LegroomPlugin` when OpenCode should intercept provider traffic in-process and expose Legroom tooling from a plugin.

```ts
import { LegroomPlugin } from "legroom-opencode";

export default async function plugin(input) {
  return LegroomPlugin(input, {
    proxyUrl: process.env.LEGROOM_PROXY_URL ?? "http://127.0.0.1:8787",
  });
}
```

`LegroomPlugin`:

- installs Legroom transport interception for OpenCode provider traffic.
- exposes the `legroom_retrieve` tool.
- publishes `LEGROOM_PROXY_URL` in the plugin output env.
- defaults to `http://127.0.0.1:8787` when no proxy URL is supplied.

## Retrieve Tool

```ts
import { createLegroomRetrieveTool } from "legroom-opencode";

const retrieve = createLegroomRetrieveTool({
  proxyBaseUrl: "http://127.0.0.1:8787",
});

const result = await retrieve.execute({
  hash: "0123456789abcdef01234567",
});
```

The tool calls `/v1/retrieve/<hash>` on the Legroom proxy.

## Compression Helper

```ts
import { compressWithLegroom } from "legroom-opencode";

const result = await compressWithLegroom(
  [{ role: "user", content: "Summarize this file" }],
  { model: "gpt-4o", proxyUrl: "http://127.0.0.1:8787" },
);

console.log(`Saved ${result.tokensSaved} tokens`);
```

## Models

| Model | Context | Output |
|---|---:|---:|
| `claude-sonnet-4-6` | 200K | 16K |
| `claude-opus-4-6` | 200K | 16K |
| `claude-haiku-4-5-20251001` | 200K | 8K |
| `gpt-4o` | 128K | 16K |
| `gpt-4.1` | 1M | 32K |

The provider config exposes these as `legroom/<model>` and defaults to `legroom/claude-sonnet-4-6`.

## Environment

| Variable | Used by | Description |
|---|---|---|
| `LEGROOM_PROXY_URL` | Native plugin | Proxy URL used by `LegroomPlugin` |
| `OPENCODE_CONFIG_CONTENT` | OpenCode wrapper | Generated OpenCode provider, model, and MCP config |

## License

Apache-2.0
