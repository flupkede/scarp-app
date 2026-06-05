# SvelteKit 5 + FastAPI Dev Environment Script
# Usage: .\dev.ps1 [start|stop|status|logs|restart|deploy|deploy-fe|deploy-be]
# Manages backend (uvicorn) and frontend (pnpm dev) with PID tracking and logs,
# and deploys both to Azure (Static Web App + App Service) directly.
#
# Customize these variables for your project:

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "logs", "restart", "deploy", "deploy-fe", "deploy-be")]
    [string]$Action = "status",

    [Parameter(Mandatory = $false)]
    [int]$BackendPort = 11000,

    [Parameter(Mandatory = $false)]
    [int]$FrontendPort = 11001,

    [Parameter(Mandatory = $false)]
    [string]$BackendDir = "backend",

    [Parameter(Mandatory = $false)]
    [string]$FrontendDir = "frontend"
)

# --- Azure deploy targets ---
$AzResourceGroup   = "scarp"
$AzStaticWebApp    = "scarp-web"
$AzAppService      = "scarp-api"

$ErrorActionPreference = "Stop"

# Paths
$LogDir = Join-Path $PSScriptRoot ".dev-logs"
$BackendLog = Join-Path $LogDir "backend.log"
$BackendErrLog = Join-Path $LogDir "backend-error.log"
$FrontendLog = Join-Path $LogDir "frontend.log"
$FrontendErrLog = Join-Path $LogDir "frontend-error.log"
$BackendPidFile = Join-Path $LogDir "backend.pid"
$FrontendPidFile = Join-Path $LogDir "frontend.pid"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# --- Helper functions ---

function Get-SavedPid {
    param([string]$PidFile)
    if (Test-Path $PidFile) {
        $value = Get-Content $PidFile -Raw -Encoding UTF8
        if ($value -match "\d+") {
            return [int]$value.Trim()
        }
    }
    return $null
}

function Save-Pid {
    param([int]$ProcessId, [string]$PidFile)
    $ProcessId | Out-File -FilePath $PidFile -Encoding ASCII -NoNewline
}

function Test-PortInUse {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return ($null -ne $conn -and $conn.Count -gt 0)
    } catch {
        return $false
    }
}

function Get-ProcessByPort {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($conn) {
            return Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        }
    } catch {
        return $null
    }
    return $null
}

function Stop-ProcessTree {
    param([int]$ProcessId)
    # Kill children first
    $children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ProcessId }
    foreach ($child in $children) {
        Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue
    }
    # Kill the process itself
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Write-Label {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

# --- Actions ---

function Start-Services {
    Write-Label "`nStarting dev environment..." "Cyan"

    $backendDir = Join-Path $PSScriptRoot $BackendDir
    $frontendDir = Join-Path $PSScriptRoot $FrontendDir

    # --- Backend ---
    if (Test-PortInUse $BackendPort) {
        $proc = Get-ProcessByPort $BackendPort
        Write-Label "  Backend already running on port $BackendPort (PID $($proc.Id))" "Yellow"
    } else {
        if (-not (Test-Path $backendDir)) {
            Write-Label "  Backend dir not found: $backendDir" "Red"
            return
        }

        Write-Label "  Starting backend on port $BackendPort..." "White"
        $backendCmd = "uv run uvicorn scarp.api.main:app --port $BackendPort --reload >> '$BackendLog' 2>> '$BackendErrLog'"
        $proc = Start-Process -FilePath "pwsh" `
            -ArgumentList "-NoProfile", "-Command", $backendCmd `
            -WorkingDirectory $backendDir `
            -WindowStyle Hidden `
            -PassThru

        Save-Pid $proc.Id $BackendPidFile

        # Wait for port
        $attempts = 0
        while ($attempts -lt 30) {
            Start-Sleep -Milliseconds 500
            if (Test-PortInUse $BackendPort) { break }
            $attempts++
        }

        if (Test-PortInUse $BackendPort) {
            $actual = Get-ProcessByPort $BackendPort
            Write-Label "  Backend started (PID $($actual.Id))" "Green"
        } else {
            Write-Label "  Backend may still be starting... (PID $($proc.Id))" "Yellow"
        }
    }

    # --- Frontend ---
    if (Test-PortInUse $FrontendPort) {
        $proc = Get-ProcessByPort $FrontendPort
        Write-Label "  Frontend already running on port $FrontendPort (PID $($proc.Id))" "Yellow"
    } else {
        if (-not (Test-Path $frontendDir)) {
            Write-Label "  Frontend dir not found: $frontendDir" "Red"
            return
        }

        Write-Label "  Starting frontend on port $FrontendPort..." "White"
        $frontendCmd = "pnpm dev >> '$FrontendLog' 2>> '$FrontendErrLog'"
        $proc = Start-Process -FilePath "pwsh" `
            -ArgumentList "-NoProfile", "-Command", $frontendCmd `
            -WorkingDirectory $frontendDir `
            -WindowStyle Hidden `
            -PassThru

        Save-Pid $proc.Id $FrontendPidFile

        # Wait for port
        $attempts = 0
        while ($attempts -lt 30) {
            Start-Sleep -Milliseconds 500
            if (Test-PortInUse $FrontendPort) { break }
            $attempts++
        }

        if (Test-PortInUse $FrontendPort) {
            $actual = Get-ProcessByPort $FrontendPort
            Write-Label "  Frontend started (PID $($actual.Id))" "Green"
        } else {
            Write-Label "  Frontend may still be starting... (PID $($proc.Id))" "Yellow"
        }
    }

    Write-Label ""
    Write-Label "  Backend:  http://localhost:$BackendPort" "White"
    Write-Label "  Frontend: http://localhost:$FrontendPort" "White"
    Write-Label "  API docs: http://localhost:$BackendPort/docs" "DarkGray"
    Write-Label ""
}

function Stop-Services {
    Write-Label "`nStopping dev environment..." "Cyan"

    # Stop backend
    $backendPid = Get-SavedPid $BackendPidFile
    $backendProc = Get-ProcessByPort $BackendPort

    if ($backendProc) {
        Write-Label "  Stopping backend (PID $($backendProc.Id))..." "White"
        Stop-ProcessTree $backendProc.Id
    } elseif ($backendPid) {
        $check = Get-Process -Id $backendPid -ErrorAction SilentlyContinue
        if ($check) {
            Write-Label "  Stopping backend (PID $backendPid)..." "White"
            Stop-ProcessTree $backendPid
        }
    }

    # Stop frontend
    $frontendPid = Get-SavedPid $FrontendPidFile
    $frontendProc = Get-ProcessByPort $FrontendPort

    if ($frontendProc) {
        Write-Label "  Stopping frontend (PID $($frontendProc.Id))..." "White"
        Stop-ProcessTree $frontendProc.Id
    } elseif ($frontendPid) {
        $check = Get-Process -Id $frontendPid -ErrorAction SilentlyContinue
        if ($check) {
            Write-Label "  Stopping frontend (PID $frontendPid)..." "White"
            Stop-ProcessTree $frontendPid
        }
    }

    # Cleanup PID files
    if (Test-Path $BackendPidFile) { Remove-Item $BackendPidFile -Force }
    if (Test-Path $FrontendPidFile) { Remove-Item $FrontendPidFile -Force }

    # Verify ports are free
    Start-Sleep -Seconds 2
    $bFree = -not (Test-PortInUse $BackendPort)
    $fFree = -not (Test-PortInUse $FrontendPort)

    if ($bFree -and $fFree) {
        Write-Label "  Stopped." "Green"
    } else {
        if (-not $bFree) { Write-Label "  WARNING: port $BackendPort still in use" "Yellow" }
        if (-not $fFree) { Write-Label "  WARNING: port $FrontendPort still in use" "Yellow" }
    }
    Write-Label ""
}

function Show-Status {
    Write-Label "`nDev environment status:" "Cyan"
    Write-Label ""

    $backendProc = Get-ProcessByPort $BackendPort
    $frontendProc = Get-ProcessByPort $FrontendPort

    if ($backendProc) {
        Write-Label "  Backend:  RUNNING on port $BackendPort (PID $($backendProc.Id))" "Green"
        # Health check
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$BackendPort/health" -TimeoutSec 3
            Write-Label "  Health:   $($response.status)" "DarkGray"
        } catch {
            Write-Label "  Health:   no response (may still be starting)" "Yellow"
        }
    } else {
        Write-Label "  Backend:  STOPPED (port $BackendPort free)" "Red"
    }

    if ($frontendProc) {
        Write-Label "  Frontend: RUNNING on port $FrontendPort (PID $($frontendProc.Id))" "Green"
    } else {
        Write-Label "  Frontend: STOPPED (port $FrontendPort free)" "Red"
    }

    # Check stale PID files
    $backendPid = Get-SavedPid $BackendPidFile
    $frontendPid = Get-SavedPid $FrontendPidFile
    if ($backendPid -and -not $backendProc) {
        $dead = Get-Process -Id $backendPid -ErrorAction SilentlyContinue
        if (-not $dead) {
            Write-Label "  (stale backend PID file, cleaning up)" "DarkGray"
            Remove-Item $BackendPidFile -Force
        }
    }
    if ($frontendPid -and -not $frontendProc) {
        $dead = Get-Process -Id $frontendPid -ErrorAction SilentlyContinue
        if (-not $dead) {
            Write-Label "  (stale frontend PID file, cleaning up)" "DarkGray"
            Remove-Item $FrontendPidFile -Force
        }
    }

    Write-Label ""
}

function Show-Logs {
    Write-Label "`nDev logs (last 20 lines each):" "Cyan"
    Write-Label ""

    if (Test-Path $BackendLog) {
        Write-Label "  --- backend stdout ---" "DarkGray"
        Get-Content $BackendLog -Tail 20 | ForEach-Object { Write-Host "  $_" }
    }
    if (Test-Path $BackendErrLog) {
        $errLines = Get-Content $BackendErrLog -Tail 20
        if ($errLines) {
            Write-Label "  --- backend stderr ---" "DarkGray"
            $errLines | ForEach-Object { Write-Host "  $_" }
        }
    }
    if (Test-Path $FrontendLog) {
        Write-Label "  --- frontend stdout ---" "DarkGray"
        Get-Content $FrontendLog -Tail 20 | ForEach-Object { Write-Host "  $_" }
    }
    if (Test-Path $FrontendErrLog) {
        $errLines = Get-Content $FrontendErrLog -Tail 20
        if ($errLines) {
            Write-Label "  --- frontend stderr ---" "DarkGray"
            $errLines | ForEach-Object { Write-Host "  $_" }
        }
    }

    if (-not (Test-Path $BackendLog) -and -not (Test-Path $FrontendLog)) {
        Write-Label "  No log files found. Run '.\dev.ps1 start' first." "Yellow"
    }

    Write-Label ""
}

# --- Deploy actions ---

function Deploy-Frontend {
    Write-Label "`nDeploying frontend to Azure Static Web Apps ($AzStaticWebApp)..." "Cyan"

    $frontendDir = Join-Path $PSScriptRoot $FrontendDir
    $buildDir = Join-Path $frontendDir "build"
    $swaConfigSrc = Join-Path $PSScriptRoot "staticwebapp.config.json"

    if (-not (Test-Path $frontendDir)) {
        Write-Label "  Frontend dir not found: $frontendDir" "Red"
        return $false
    }

    # 1. Build (PUBLIC_API_URL empty -> SWA proxies /api/* to linked backend)
    Write-Label "  Building (pnpm build)..." "White"
    $env:PUBLIC_API_URL = ""
    Push-Location $frontendDir
    try {
        pnpm install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { Write-Label "  pnpm install failed" "Red"; return $false }
        pnpm build
        if ($LASTEXITCODE -ne 0) { Write-Label "  pnpm build failed" "Red"; return $false }
    } finally {
        Pop-Location
    }

    if (-not (Test-Path $buildDir)) {
        Write-Label "  Build output not found: $buildDir" "Red"
        return $false
    }

    # 2. Stage SWA config into build output (navigationFallback + headers + CSP)
    if (Test-Path $swaConfigSrc) {
        Copy-Item $swaConfigSrc (Join-Path $buildDir "staticwebapp.config.json") -Force
        Write-Label "  Staged staticwebapp.config.json into build/" "DarkGray"
    }

    # 3. Fetch deployment token from Azure (keeps secret out of the repo)
    Write-Label "  Fetching SWA deployment token..." "White"
    $token = (& az staticwebapp secrets list `
        --name $AzStaticWebApp `
        --resource-group $AzResourceGroup `
        --query "properties.apiKey" -o tsv)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
        Write-Label "  Could not retrieve SWA deployment token (is 'az' logged in?)" "Red"
        return $false
    }

    # 4. Deploy pre-built output via the SWA CLI (no global install needed)
    Write-Label "  Uploading to Static Web App..." "White"
    & npx -y "@azure/static-web-apps-cli" deploy $buildDir `
        --deployment-token $token `
        --env production
    if ($LASTEXITCODE -ne 0) {
        Write-Label "  SWA deploy failed" "Red"
        return $false
    }

    Write-Label "  Frontend deployed." "Green"
    return $true
}

function Deploy-Backend {
    Write-Label "`nDeploying backend to Azure App Service ($AzAppService)..." "Cyan"

    $backendDir = Join-Path $PSScriptRoot $BackendDir
    $dataDir = Join-Path $PSScriptRoot "data\processed"
    $stageDir = Join-Path $LogDir "deploy_pkg"
    $zipPath = Join-Path $LogDir "backend-deploy.zip"

    if (-not (Test-Path (Join-Path $backendDir "src\scarp"))) {
        Write-Label "  Backend package not found under $backendDir\src\scarp" "Red"
        return $false
    }

    # 1. Clean staging dir
    if (Test-Path $stageDir) { Remove-Item $stageDir -Recurse -Force }
    New-Item -ItemType Directory -Path $stageDir -Force | Out-Null

    # 2. Pre-install deps flat into the package (WEBSITE_RUN_FROM_PACKAGE=1
    #    mounts the zip as-is; no server-side pip install runs). Install from
    #    backend/pyproject.toml so the dependency list never drifts from the
    #    declared deps (slowapi, gunicorn, etc.).
    Write-Label "  Installing dependencies into package..." "White"
    $pipArgs = @(
        "pip", "install", "--target", $stageDir, "--no-cache-dir",
        "--python-version", "3.12", "--python-platform", "linux",
        $backendDir
    )
    & uv @pipArgs
    if ($LASTEXITCODE -ne 0) { Write-Label "  uv pip install failed" "Red"; return $false }

    # 3. Copy app source + processed data into the package
    Copy-Item (Join-Path $backendDir "src\scarp") (Join-Path $stageDir "scarp") -Recurse -Force
    if (Test-Path $dataDir) {
        $dataDest = Join-Path $stageDir "data\processed"
        New-Item -ItemType Directory -Path $dataDest -Force | Out-Null
        Copy-Item (Join-Path $dataDir "*") $dataDest -Recurse -Force
    }

    # 4. Zip the package
    Write-Label "  Building deployment zip..." "White"
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    Compress-Archive -Path (Join-Path $stageDir "*") -DestinationPath $zipPath -Force
    $sizeMb = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
    Write-Label "  Package size: $sizeMb MB" "DarkGray"

    # 5. Deploy via az webapp deploy (zip, run-from-package)
    Write-Label "  Uploading to App Service..." "White"
    $deployArgs = @(
        "webapp", "deploy",
        "--resource-group", $AzResourceGroup,
        "--name", $AzAppService,
        "--src-path", $zipPath,
        "--type", "zip",
        "--async", "false"
    )
    & az @deployArgs
    if ($LASTEXITCODE -ne 0) { Write-Label "  App Service deploy failed" "Red"; return $false }

    Write-Label "  Backend deployed." "Green"
    return $true
}

function Invoke-Deploy {
    param([switch]$FrontendOnly, [switch]$BackendOnly)

    $ok = $true
    if (-not $BackendOnly)  { if (-not (Deploy-Frontend)) { $ok = $false } }
    if (-not $FrontendOnly) { if (-not (Deploy-Backend))  { $ok = $false } }

    Write-Label ""
    if ($ok) {
        Write-Label "  Deploy complete." "Green"
        Write-Label "  Live: https://scarp.dsoft.services" "White"
    } else {
        Write-Label "  Deploy finished with errors (see above)." "Red"
    }
    Write-Label ""
}

# --- Main ---

switch ($Action) {
    "start"     { Start-Services }
    "stop"      { Stop-Services }
    "status"    { Show-Status }
    "logs"      { Show-Logs }
    "restart"   { Stop-Services; Start-Sleep -Seconds 2; Start-Services }
    "deploy"    { Invoke-Deploy }
    "deploy-fe" { Invoke-Deploy -FrontendOnly }
    "deploy-be" { Invoke-Deploy -BackendOnly }
}

Write-Host ""
