# Security Policy

## Secrets and API keys

- **No secrets are committed to this repository.** All API keys are injected at runtime via environment variables or Azure Key Vault references.
- The `.env` file is gitignored. Use `.env.example` as a template — it contains only placeholder values.
- On Azure App Service, the LLM API key is stored in Key Vault and referenced via a managed identity; it is never written to `appsettings` in plaintext.

## CORS

The backend enforces a strict allowlist (`CORS_ALLOW_ORIGINS` env var). The wildcard `*` is never used. In production the only allowed origin is the Azure Static Web App hostname.

## HTTP security headers

All responses carry:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |
| `Content-Security-Policy` | (see `staticwebapp.config.json`) |

Headers are set at the Azure Static Web App layer for frontend responses, and via FastAPI middleware for API responses.

## LLM / AI layer

- The LLM endpoint is configured via `LLM_BASE_URL` and is never hardcoded.
- User queries sent to the LLM are truncated to 500 characters before forwarding.
- No user data or query history is persisted.
- LLM tool-call responses are validated before being applied to the dataset.

## Data

All datasets are sourced from US Government agencies (USGS, DGGS, USFS, OSM) and are public domain. No personal data is collected or stored.

## Responsible disclosure

Found a security issue? Email **filip@dsoft.services** with a description and reproduction steps. We aim to respond within 48 hours.

This project is a research/portfolio tool, not a production safety system. Do not rely on it for emergency decision-making.
