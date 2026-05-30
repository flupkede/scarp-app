# SvelteKit 5 + FastAPI Dev Environment Script
# Usage: .\dev.ps1 [start|stop|status|logs|restart]
# Manages backend (uvicorn) and frontend (pnpm dev) with PID tracking and logs.
#
# Customize these variables for your project:

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "logs", "restart")]
    [string]$Action = "status",

    [Parameter(Mandatory = $false)]
    [int]$BackendPort = 8000,

    [Parameter(Mandatory = $false)]
    [int]$FrontendPort = 5173,

    [Parameter(Mandatory = $false)]
    [string]$BackendDir = "backend",

    [Parameter(Mandatory = $false)]
    [string]$FrontendDir = "frontend"
)

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
        $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
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
        $frontendCmd = "pnpm dev --port $FrontendPort >> '$FrontendLog' 2>> '$FrontendErrLog'"
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

# --- Main ---

switch ($Action) {
    "start"   { Start-Services }
    "stop"    { Stop-Services }
    "status"  { Show-Status }
    "logs"    { Show-Logs }
    "restart" { Stop-Services; Start-Sleep -Seconds 2; Start-Services }
}

Write-Host ""
