# INFRA_PLAN.md — Azure deploy (SWA Standard + App Service + Key Vault)

> Gegenereerd 2026-05-29. Doel: zaterdag is de deploy mechanisch, geen ontdekkingstocht.
> Subscription: Visual Studio dev/test (€50/m krediet). Regio: **West Europe**.

## Wat we provisioneren

| Resource | Rol |
|---|---|
| Resource Group | Container voor alles (1 keer weggooien = alles weg) |
| **Static Web App (Standard)** | Frontend (SvelteKit static) + reverse-proxy van `/api/*` naar de backend |
| **App Service Plan (B1, Linux)** | Compute voor de backend; B1 = "Always On" mogelijk |
| **App Service (Python 3.12)** | FastAPI-backend — draagt de live `/api/search` (LLM-call) |
| **Key Vault (RBAC)** | Houdt `LLM_API_KEY` als secret |
| System-assigned identity op de App Service | Leest het secret uit Key Vault, geen key in config |

## Wat we NIET nodig hebben

- **Storage Account** — geojson (~7 MB) ship met de deploy; ruwe 12.4 GB blijft lokaal; App Service vereist (anders dan managed Functions) geen los storage account.
- **Database** — platte geojson-bestanden, geen DB.
- **Container Registry** — App Service draait Python native, geen image nodig (je hebt ook geen Dockerfile).
- **Application Insights** — kán, maar valt **buiten** het dev/test-krediet. Overslaan, anders losse kosten.

## Provisioning — `az` in volgorde

```bash
# 0. Variabelen
RG=scarp-rg
REGION=westeurope
SWA=scarp-web
PLAN=scarp-plan
APP=scarp-api            # wordt scarp-api.azurewebsites.net
VAULT=scarp-kv-<uniek>   # KV-naam moet globaal uniek zijn

az login
az account set --subscription "<jouw-devtest-sub>"

# 1. Resource group
az group create -n $RG -l $REGION

# 2. App Service Plan (B1) + Python web app
az appservice plan create -g $RG -n $PLAN --is-linux --sku B1
az webapp create -g $RG -p $PLAN -n $APP --runtime "PYTHON:3.12"
az webapp config set -g $RG -n $APP --always-on true   # geen cold start bij jurybezoek

# 3. Key Vault (RBAC-model)
az keyvault create -g $RG -n $VAULT -l $REGION --sku standard --enable-rbac-authorization
VAULT_ID=$(az keyvault show -n $VAULT --query id -o tsv)
MY_ID=$(az ad signed-in-user show --query id -o tsv)
az role assignment create --role "Key Vault Secrets Officer" \
  --assignee-object-id $MY_ID --assignee-principal-type User --scope $VAULT_ID

# 4. Managed identity op de app + leesrecht op de vault (1 commando)
az webapp identity assign -g $RG -n $APP --scope $VAULT_ID --role "Key Vault Secrets User"

# 5. Secret erin, en als Key Vault-reference koppelen aan een app setting
SECRET_URI=$(az keyvault secret set --vault-name $VAULT --name llm-api-key \
  --value "<DE-ECHTE-KEY>" --query id -o tsv)
az webapp config appsettings set -g $RG -n $APP \
  --settings LLM_API_KEY="@Microsoft.KeyVault(SecretUri=$SECRET_URI)"

# 6. Static Web App (Standard) — global, regio niet kritisch
az staticwebapp create -n $SWA -g $RG --sku Standard
# (valt 'm op Free terug? -> az staticwebapp update -n $SWA -g $RG --sku Standard)

# 7. Backend linken: SWA proxyt /api/* naar de App Service
APP_ID=$(az webapp show -g $RG -n $APP --query id -o tsv)
az staticwebapp backends link -n $SWA -g $RG \
  --backend-resource-id $APP_ID --backend-region $REGION
```

## Drie dingen die de deploy maken of breken

1. **SWA proxyt alléén `/api/*`.** Na het linken is de App Service niet meer publiek bereikbaar (krijgt een "Azure Static Web Apps (Linked)" identity provider die enkel proxy-verkeer toelaat), en alleen routes onder `/api` komen door. Gevolg:
   - `/api/search` heeft die prefix al → OK.
   - Serveer `zones.geojson`, `slides.geojson`, enz. als **static assets in de SWA** (snel, geen backend-load). Zo hoeven `/zones` en `/layers` niet via de backend. Doen `zones`/`layers` toch live? Geef ze dan ook een `/api`-prefix, anders zijn ze onbereikbaar.

2. **Frontend op `adapter-static`.** Nu staat het op `adapter-auto` — dat detecteert Azure SWA niet en de build faalt. Zet de adapter om vóór de build (in de phase-spec verwerken).

3. **Startup command voor FastAPI.** App Service Linux serveert Python met gunicorn; FastAPI heeft de uvicorn-worker nodig. Deploy-root = `backend/`, app = `scarp.api.main:app`:
   ```bash
   az webapp config set -g $RG -n $APP \
     --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker scarp.api.main:app"
   ```
   Dit is hét ding dat je morgen in de test-deploy wil zien werken (src-layout op de path, uv-install via Oryx). Niet pas zaterdag ontdekken.

## Custom domain (jouw DNS)

```bash
az staticwebapp hostname set -n $SWA -g $RG --hostname scarp.<jouwdomein>
```
Daarna bij je DNS een **CNAME** `scarp` → de `*.azurestaticapps.net`-hostname. SSL regelt Azure gratis en automatisch. Custom domain zet je op de SWA, niet op de App Service — het hele verkeer loopt via de SWA.

## Kosten / krediet

B1 ±€11–13/m + SWA Standard ±€9/m + Key Vault verwaarloosbaar (per-operatie) → ruim binnen je €50, en je betaalt pro rata per uur, dus een weekend kost centen. **Check vrijdag wel je resterende maandkrediet** (dev/test-sub schakelt uit bij uitputting — zie vorige notitie); zet desnoods de spending limit af met een kaart als vangnet.

## Afbreken na de wedstrijd
```bash
az group delete -n $RG --yes --no-wait   # alles in één keer weg
```
