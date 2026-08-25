# agent-crew setup (Windows) - builds a Python venv and installs the labs.
# crewai does NOT install on Python 3.14 (tiktoken/regex have no 3.14 wheels yet),
# so this script finds a 3.10-3.13 interpreter and uses THAT for the venv.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Find-Python {
    foreach ($v in "3.13", "3.12", "3.11", "3.10") {
        & py "-$v" --version *> $null 2>&1
        if ($LASTEXITCODE -eq 0) { return "py -$v" }
    }
    # fall back to whatever `python` is, only if it's 3.10-3.13
    try {
        $ver = & python -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
        if ($ver -match '^3\.(10|11|12|13)$') { return "python" }
    } catch {}
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Host "ERROR: no compatible Python found (need 3.10-3.13)." -ForegroundColor Red
    Write-Host "crewai does NOT build on Python 3.14. Install 3.13 and re-run:" -ForegroundColor Yellow
    Write-Host "    winget install Python.Python.3.13" -ForegroundColor Yellow
    exit 1
}
Write-Host "Using $py to build the venv..." -ForegroundColor Green
Invoke-Expression "$py -m venv .venv"
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete. Next:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host "    python m8_0_verify.py        # all 4 gates should PASS (connect WireGuard first)"
Write-Host "    python m8_1_bankbot.py"
