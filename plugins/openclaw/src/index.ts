export { default, registerLegroomPlugin } from "./plugin/index.js";
export { LegroomContextEngine } from "./engine.js";
export { ProxyManager, normalizeAndValidateProxyUrl, isLocalProxyUrl, defaultLogger, probeLegroomProxy } from "./proxy-manager.js";
export { agentToOpenAI, normalizeAgentMessages, openAIToAgent } from "./convert.js";
export { createLegroomRetrieveTool } from "./tools/legroom-retrieve.js";
export {
  DEFAULT_GATEWAY_PROVIDER_IDS,
  applyGatewayProviderBaseUrls,
  applyGatewayProviderBaseUrlsInPlace,
  resolveGatewayProviderIds,
} from "./gateway-config.js";
