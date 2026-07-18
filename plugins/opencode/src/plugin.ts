import type { Plugin } from "@opencode-ai/plugin";
import { tool } from "@opencode-ai/plugin";
import { z } from "zod";

import { createLegroomRetrieveTool, getDefaultProxyUrl } from "./retrieve.js";
import { installLegroomTransport } from "./transport.js";

export interface LegroomOpenCodePluginOptions {
  proxyUrl?: string;
  project?: string;
  backend?: string;
  debug?: boolean;
}

function normalizeProxyUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

function resolveProxyUrl(options?: LegroomOpenCodePluginOptions): string {
  return normalizeProxyUrl(
    options?.proxyUrl ??
      process.env.LEGROOM_PROXY_URL ??
      process.env.LEGROOM_BASE_URL ??
      getDefaultProxyUrl(),
  );
}

export const LegroomPlugin: Plugin = async (input, options = {}) => {
  const pluginOptions = options as LegroomOpenCodePluginOptions;
  const proxyUrl = resolveProxyUrl(pluginOptions);
  const retrieveTool = createLegroomRetrieveTool({ proxyBaseUrl: proxyUrl });
  const uninstallTransport = installLegroomTransport({
    proxyUrl,
    debug: pluginOptions.debug,
  });

  return {
    dispose: async () => {
      uninstallTransport();
    },
    tool: {
      legroom_retrieve: tool({
        description: retrieveTool.description,
        args: {
          hash: z
            .string()
            .regex(/^[a-f0-9]{24}$/i, "Expected 24-character hex hash"),
        },
        async execute(args) {
          return retrieveTool.execute(args);
        },
      }),
    },
    "shell.env": async (_input, output) => {
      output.env.LEGROOM_ACTIVE = "1";
      output.env.LEGROOM_PROXY_URL = proxyUrl;
      output.env.LEGROOM_PROJECT =
        pluginOptions.project ??
        (input.project as { id?: string }).id ??
        input.directory;
      if (pluginOptions.backend) {
        output.env.LEGROOM_BACKEND = pluginOptions.backend;
      }
    },
  };
};

export default LegroomPlugin;
