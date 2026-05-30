# Scarp — Deployment Guide

> Azure Static Web App (frontend) + App Service B1 Linux (backend).
> Estimated cost: ~€22/month; hackathon weekend ≈ cents.

---

## Required secrets (GitHub → Settings → Secrets → Actions)

| Secret | Where to get it |
|--------|----------------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Azure Portal → Static Web App → Manage deployment token |
| `AZURE_APP_SERVICE_PUBLISH_PROFILE` | Azure Portal → App Service → Get publish profile (download XML) |

---

## One-time Azure provisioning

Run these `az` commands once before the first deploy. Swap placeholder values.

```bash
# Variables
RG=scarp-rg
REGION=westeurope
SWA=scarp-web
PLAN=scarp-plan
APP=scarp-api          # becomes scarp-api.azurewebsites.net
VAULT=scarp-kv-$(openssl rand -hex 4)   # globally unique KV name

az login
az account set --subscription "<YOUR-DEVTEST-SUB-ID>"

# 1. Resource group
az group create -n $RG -l $REGION

# 2. App Service Plan (B1 Linux) + Python 3.12 web app
az appservice plan create -g $RG -n $PLAN --is-linux --sku B1
az webapp create -g $RG -p $PLAN -n $APP --runtime "PYTHON:3.12"
az webapp config set -g $RG -n $APP --always-on true

# 3. Key Vault (RBAC)
az keyvault create -g $RG -n $VAULT -l $REGION --sku standard --enable-rbac-authorization
VAULT_ID=$(az keyvault show -n $VAULT --query id -o tsv)
MY_ID=$(az ad signed-in-user show --query id -o tsv)
az role assignment create --role "Key Vault Secrets Officer" \
  --assignee-object-id $MY_ID --assignee-principal-type User --scope $VAULT_ID

# 4. Managed identity → Key Vault read access
az webapp identity assign -g $RG -n $APP --scope $VAULT_ID --role "Key Vault Secrets User"

# 5. Store LLM API key in Key Vault, wire to App Service
SECRET_URI=$(az keyvault secret set --vault-name $VAULT --name llm-api-key \
  --value "<YOUR-DEEPINFRA-OR-OPENAI-KEY>" --query id -o tsv)
az webapp config appsettings set -g $RG -n $APP \
  --settings LLM_API_KEY="@Microsoft.KeyVault(SecretUri=$SECRET_URI)"

# 6. App Service startup command + remaining settings
SWA_HOSTNAME="<your-swa-name>.azurestaticapps.net"
az webapp config set -g $RG -n $APP \
  --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 scarp.api.main:app"
az webapp config appsettings set -g $RG -n $APP \
  --settings \
    CORS_ALLOW_ORIGINS="https://$SWA_HOSTNAME" \
    LLM_BASE_URL="https://api.deepinfra.com/v1/openai" \
    LLM_MODEL="zai-org/GLM-4.7-Flash" \
    DATA_DIR="/home/site/wwwroot/data/processed"

# 7. Static Web App (Standard tier for backend linking)
az staticwebapp create -n $SWA -g $RG --sku Standard

# 8. Link backend: SWA proxies /api/* to App Service
APP_ID=$(az webapp show -g $RG -n $APP --query id -o tsv)
az staticwebapp backends link -n $SWA -g $RG \
  --backend-resource-id $APP_ID --backend-region $REGION
```

---

## Manual deploy (fallback — no CI needed)

If CI is not set up or fails, deploy manually:

### Frontend
```bash
cd frontend
pnpm install --frozen-lockfile
pnpm build
# Get deployment token from Azure Portal:
az staticwebapp secrets list -n scarp-web -g scarp-rg --query "properties.apiKey" -o tsv
# Then use SWA CLI:
npx @azure/static-web-apps-cli deploy ./build \
  --deployment-token <TOKEN> \
  --env production
```

### Backend
```bash
cd backend
uv sync
# Download publish profile from Azure Portal → App Service → Get publish profile
# Then use VS Code Azure App Service extension, or:
az webapp deploy -g scarp-rg -n scarp-api \
  --src-path . --type zip
```

---

## Verify deployment

```bash
# Backend health
curl https://scarp-api.azurewebsites.net/health

# Via SWA proxy (after linking)
curl https://<your-swa>.azurestaticapps.net/api/health

# Top 10 zones
curl "https://<your-swa>.azurestaticapps.net/api/zones?limit=10" | python -m json.tool | head -40
```

---

## Data: uploading processed GeoJSON

The App Service needs the processed GeoJSON files at runtime. Upload them once:

```bash
# Via az webapp (Kudu REST API)
az webapp deploy -g scarp-rg -n scarp-api \
  --src-path data/processed \
  --target-path /home/site/wwwroot/data/processed \
  --type static
```

Or use the Kudu file manager at `https://scarp-api.scm.azurewebsites.net/api/vfs/`.

---

## Tear down after the event

```bash
az group delete -n scarp-rg --yes --no-wait   # removes everything at once
```
