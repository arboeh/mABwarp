# scripts/test-local.ps1

$venv = ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"

if ((Test-Path $venv) -and -not (Test-Path $venvPython)) {
    Write-Host "Invalid .venv detected, removing..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venv -ErrorAction SilentlyContinue
}

uv sync --extra dev
if ($LASTEXITCODE -ne 0) {
    Write-Error "UV sync failed!"
    exit 1
}

uv run pytest tests/ -v --cov=custom_components.mabwarp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

uv run ruff check custom_components/mabwarp/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

uv run ruff format --check custom_components/mabwarp/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "All checks passed!" -ForegroundColor Green
