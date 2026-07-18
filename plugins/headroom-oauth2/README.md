# legroom-oauth2

Generic **OAuth2 client-credentials** upstream-auth extension for the
[Legroom](https://github.com/legroom-ai/legroom-ai.github.io) proxy.

When Legroom routes to an OpenAI-compatible backend that is protected by an
OAuth2 client-credentials flow (enterprise AI gateways, Azure AD / Entra, Okta,
Auth0, Keycloak, Cognito, …), this extension mints a bearer token from a
configurable token endpoint, caches + refreshes it (single-flight), and injects
`Authorization: Bearer <token>` on each upstream request. Optional static upstream
headers are sent via litellm. **Fully vendor-neutral — no provider is hard-coded.**

It plugs into Legroom's public `legroom.proxy_extension` entry-point seam, so it
is fully out-of-tree and opt-in.

## Install & enable
```bash
pip install legroom-oauth2
legroom proxy --backend litellm-openai --proxy-extension oauth2
```

## Configure (env; no-op unless LEGROOM_OAUTH2_TOKEN_URL is set)
| Env | Meaning |
|-----|---------|
| `LEGROOM_OAUTH2_TOKEN_URL` | token endpoint (client_credentials grant) |
| `LEGROOM_OAUTH2_CLIENT_ID` / `_CLIENT_SECRET` | credentials (secrets) |
| `LEGROOM_OAUTH2_SCOPES` | space/comma-separated scopes |
| `LEGROOM_OAUTH2_AUDIENCE` | optional audience |
| `LEGROOM_OAUTH2_GRANT_TYPE` | default `client_credentials` |
| `LEGROOM_OAUTH2_AUTH_STYLE` | `post` (form creds) or `basic` (HTTP Basic) |
| `LEGROOM_OAUTH2_HEADERS` | static upstream headers, `K=V,K2=V2` |

Tokens are minted with the standard library (`urllib`, system cert store), which
works behind corporate SSL-inspection where bundled-root TLS stacks fail.


**Effective backends:** the injected bearer reaches the upstream only for OpenAI-compatible /
passthrough litellm providers. `bedrock` / `vertex` / `sagemaker` authenticate from env and
ignore it, so this extension is a no-op there (it logs a warning at startup).

**Transport:** `token_url` must be `https` (loopback `http` is allowed for tests; set
`LEGROOM_OAUTH2_ALLOW_INSECURE=1` to override). Tokens are minted with the standard library
(`urllib`, system cert store), so a corporate-injected CA is trusted without bundling roots.
