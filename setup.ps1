# agent-crew setup (Windows) - builds a Python venv and installs the labs.
# crewai does NOT install on Python 3.14 (tiktoken/regex have no 3.14 wheels yet),
# so this script finds a 3.10-3.13 interpreter and uses THAT for the venv.
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Get-CompatiblePython {
    # Prefer the py launcher: read its installed list and pick a 3.10-3.13.
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $list = (& py -0p 2>$null)
        foreach ($v in "3.13", "3.12", "3.11", "3.10") {
            if ($list -match [regex]::Escape("-V:$v")) {
                return [pscustomobject]@{ Exe = "py"; Pre = @("-$v"); Label = "py -$v" }
            }
        }
    }
    # Fall back to `python` only if it is itself 3.10-3.13.
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $ver = (& python -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null)
        if ($ver -match '^3\.(10|11|12|13)$') {
            return [pscustomobject]@{ Exe = "python"; Pre = @(); Label = "python ($ver)" }
        }
    }
    return $null
}

$py = Get-CompatiblePython
if (-not $py) {
    Write-Host "ERROR: no compatible Python found (need 3.10-3.13)." -ForegroundColor Red
    Write-Host "crewai does NOT build on Python 3.14. Install 3.13 and re-run:" -ForegroundColor Yellow
    Write-Host "    winget install Python.Python.3.13" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using $($py.Label) to build the venv..." -ForegroundColor Green
& $py.Exe @($py.Pre) -m venv .venv
if ($LASTEXITCODE -ne 0 -or -not (Test-Path .\.venv\Scripts\python.exe)) {
    Write-Host "ERROR: venv creation failed." -ForegroundColor Red; exit 1
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: dependency install failed." -ForegroundColor Red; exit 1
}

Write-Host ""
Write-Host "Setup complete. Next:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host "    python m8_0_verify.py   # all 4 gates should PASS (connect WireGuard first)"
Write-Host "    python m8_1_bankbot.py"
