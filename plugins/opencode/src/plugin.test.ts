import { afterEach, describe, expect, it, vi } from "vitest";

import { LegroomPlugin } from "./plugin.js";

function pluginInput() {
  return {
    client: {},
    project: { id: "project-1" },
    directory: "/repo",
    worktree: "/repo",
    experimental_workspace: {
      register: vi.fn(),
    },
    $: {},
  } as never;
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("LegroomPlugin", () => {
  it("adds only Legroom metadata to shell env", async () => {
    const plugin = await LegroomPlugin(pluginInput(), {
      proxyUrl: "http://127.0.0.1:8787/",
      backend: "litellm",
    });
    const output = {
      env: {
        OPENAI_BASE_URL: "https://deepseek.example/v1",
        ANTHROPIC_BASE_URL: "https://anthropic.example",
      },
    };

    await plugin["shell.env"]?.({ cwd: "/repo" }, output);

    expect(output.env).toMatchObject({
      LEGROOM_ACTIVE: "1",
      LEGROOM_PROXY_URL: "http://127.0.0.1:8787",
      LEGROOM_PROJECT: "project-1",
      LEGROOM_BACKEND: "litellm",
      OPENAI_BASE_URL: "https://deepseek.example/v1",
      ANTHROPIC_BASE_URL: "https://anthropic.example",
    });
  });

  it("exposes a legroom_retrieve tool backed by the proxy", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => "original content",
    }));
    vi.stubGlobal("fetch", fetchMock);

    const plugin = await LegroomPlugin(pluginInput(), {
      proxyUrl: "http://127.0.0.1:8787",
    });
    const result = await plugin.tool?.legroom_retrieve.execute(
      { hash: "0123456789abcdef01234567" },
      {} as never,
    );

    expect(result).toBe("original content");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8787/v1/retrieve/0123456789abcdef01234567",
      expect.any(Object),
    );
  });
});
