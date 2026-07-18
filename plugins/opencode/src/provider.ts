export interface LegroomModelMapping {
  name: string;
  limit: {
    context: number;
    output: number;
  };
}

export interface LegroomProviderOptions {
  proxyBaseUrl?: string;
  proxyPort?: number;
  defaultModel?: string;
  models?: Record<string, LegroomModelMapping>;
}

export const DEFAULT_MODELS: Record<string, LegroomModelMapping> = {
  "claude-sonnet-4-6": {
    name: "Claude Sonnet 4.6",
    limit: { context: 200000, output: 16384 },
  },
  "claude-opus-4-6": {
    name: "Claude Opus 4.6",
    limit: { context: 200000, output: 16384 },
  },
  "claude-haiku-4-5-20251001": {
    name: "Claude Haiku 4.5",
    limit: { context: 200000, output: 8192 },
  },
  "gpt-4o": {
    name: "GPT-4o",
    limit: { context: 128000, output: 16384 },
  },
  "gpt-4.1": {
    name: "GPT-4.1",
    limit: { context: 1048576, output: 32768 },
  },
};

export const DEFAULT_MODEL = "claude-sonnet-4-6";

function resolveBaseUrl(options: LegroomProviderOptions): string {
  if (options.proxyBaseUrl) return options.proxyBaseUrl.replace(/\/+$/, "");
  const port = options.proxyPort ?? 8787;
  return `http://127.0.0.1:${port}`;
}

export interface LegroomProvider {
  npm: string;
  name: string;
  options: {
    baseURL: string;
    apiKey?: string;
  };
  models: Record<string, LegroomModelMapping>;
}

export function createLegroomProvider(
  options: LegroomProviderOptions = {},
): LegroomProvider {
  const baseUrl = resolveBaseUrl(options);
  const models = options.models ?? DEFAULT_MODELS;

  return {
    npm: "@ai-sdk/openai-compatible",
    name: "Legroom Proxy",
    options: { baseURL: `${baseUrl}/v1` },
    // OpenCode namespaces model ids by provider key, so entries must be bare
    // ids ("claude-sonnet-4-6"), referenced as "legroom/<id>".
    models: { ...models },
  };
}

export function buildOpencodeConfigContent(
  options: LegroomProviderOptions = {},
): Record<string, unknown> {
  const defaultModel = options.defaultModel ?? DEFAULT_MODEL;
  const provider = createLegroomProvider(options);

  return {
    provider: { legroom: provider },
    model: `legroom/${defaultModel}`,
  };
}

export function buildOpencodeConfigContentJson(
  options: LegroomProviderOptions = {},
): string {
  return JSON.stringify(buildOpencodeConfigContent(options));
}
