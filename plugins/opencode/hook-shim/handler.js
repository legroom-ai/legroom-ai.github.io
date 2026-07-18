import { installLegroomTransport } from "../dist/index.js";

const proxyUrl = process.env.LEGROOM_OPENCODE_TRANSPORT_PROXY_URL;
if (!proxyUrl) {
  throw new Error("Legroom OpenCode transport shim loaded without LEGROOM_OPENCODE_TRANSPORT_PROXY_URL");
}

installLegroomTransport({ proxyUrl });
