$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root 'backend'
$VenvPython = Join-Path $Backend '.venv\Scripts\python.exe'
$VenvPip = Join-Path $Backend '.venv\Scripts\pip.exe'

function Test-Python {
    param(
        [string]$Command,
        [string[]]$Arguments = @()
    )

    try {
        $output = & $Command @Arguments --version 2>&1
        if ($LASTEXITCODE -eq 0 -and "$output" -match 'Python 3\.') {
            return $true
        }
    }
    catch {
        return $false
    }

    return $false
}

function Test-BackendDependencies {
    if (-not (Test-Path $VenvPython)) {
        return $false
    }

    & $VenvPython -c "import fastapi, uvicorn, sqlalchemy, alembic" 2>$null
    return $LASTEXITCODE -eq 0
}

function Find-Python {
    if (Test-Python -Command 'python') {
        return @{ Command = 'python'; Arguments = @() }
    }

    if (Test-Python -Command 'py' -Arguments @('-3')) {
        return @{ Command = 'py'; Arguments = @('-3') }
    }

    if (Test-Python -Command 'py') {
        return @{ Command = 'py'; Arguments = @() }
    }

    throw 'Python was not found or cannot be started. Install Python 3.11+ from python.org and run this script again.'
}

function New-BackendVenv {
    $Python = Find-Python
    Write-Host 'Creating backend virtual environment...'
    & $Python.Command @($Python.Arguments) -m venv (Join-Path $Backend '.venv')
}

function Test-PortAvailable {
    param([int]$Port)

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

function Find-AvailablePort {
    param(
        [int]$StartPort,
        [int]$EndPort
    )

    for ($Port = $StartPort; $Port -le $EndPort; $Port++) {
        if (Test-PortAvailable -Port $Port) {
            return $Port
        }
    }

    throw "No free port found between $StartPort and $EndPort."
}

Write-Host ''
Write-Host '=== Support project launcher ===' -ForegroundColor Cyan
Write-Host ''

if (-not (Test-Path (Join-Path $Root '.env'))) {
    Copy-Item (Join-Path $Root '.env.example') (Join-Path $Root '.env')
    Write-Host 'Created .env from .env.example.'
}

if (-not (Test-Path (Join-Path $Backend '.env'))) {
    Copy-Item (Join-Path $Backend '.env.example') (Join-Path $Backend '.env')
    Write-Host 'Created backend .env from backend .env.example.'
}

if ((Test-Path $VenvPython) -and -not (Test-Python -Command $VenvPython)) {
    $BackupName = '.venv_broken_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
    Write-Host "Existing backend virtual environment is broken. Renaming it to $BackupName."
    Rename-Item -LiteralPath (Join-Path $Backend '.venv') -NewName $BackupName
}

if (-not (Test-Path $VenvPython)) {
    New-BackendVenv
}

if (Test-BackendDependencies) {
    Write-Host 'Backend dependencies are already installed.'
}
else {
    Write-Host 'Installing backend dependencies...'
    & $VenvPython -m pip install --upgrade pip
    & $VenvPip install -r (Join-Path $Backend 'requirements.txt')
}

Push-Location $Backend
try {
    Write-Host 'Applying database migrations...'
    & $VenvPython -m alembic upgrade head

    Write-Host 'Checking demo data...'
    & $VenvPython -m scripts.seed
}
finally {
    Pop-Location
}

$BackendPort = Find-AvailablePort -StartPort 8000 -EndPort 8009
$FrontendPort = Find-AvailablePort -StartPort 5500 -EndPort 5509
$BackendUrl = "http://localhost:$BackendPort"
$FrontendUrl = "http://localhost:$FrontendPort"

Write-Host ''
Write-Host "Backend:       $BackendUrl" -ForegroundColor Green
Write-Host "Docs:          $BackendUrl/docs" -ForegroundColor Green
Write-Host "Admin panel:   $FrontendUrl/frontend/panel.html" -ForegroundColor Green
Write-Host "Request page:  $FrontendUrl/frontend/embed-widget-snippet.html" -ForegroundColor Green
Write-Host ''
Write-Host 'Admin login: admin / admin12345'
Write-Host 'Specialist login: spec1 / spec12345'
Write-Host 'Press Ctrl+C or close this window to stop.'
Write-Host ''

$frontendJob = Start-Job -ScriptBlock {
    param($RootPath, $PythonPath, $Port)
    Set-Location $RootPath
    & $PythonPath -m http.server $Port --bind 127.0.0.1
} -ArgumentList $Root, $VenvPython, $FrontendPort

try {
    Push-Location $Backend
    & $VenvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port $BackendPort
}
finally {
    Pop-Location
    Stop-Job $frontendJob -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $frontendJob -ErrorAction SilentlyContinue | Out-Null
}
