# test-local.ps1

$venv = ".venv"
$pyproject_hash = (Get-FileHash pyproject.toml).Hash

if (!(Test-Path "$venv/pyproject.hash") -or
    (Get-Content "$venv/pyproject.hash") -ne $pyproject_hash) {

    Write-Host "pyproject.toml changed → fresh UV sync" -ForegroundColor Yellow

    if (Test-Path $venv) {
        Remove-Item -Recurse -Force $venv -ErrorAction SilentlyContinue
    }
    Remove-Item uv.lock -ErrorAction SilentlyContinue

    uv sync --dev

    if ($LASTEXITCODE -ne 0) {
        Write-Error "UV sync failed!"
        exit 1
    }

    Set-Content "$venv/pyproject.hash" $pyproject_hash
    Write-Host "Fresh UV sync complete (.venv + uv.lock)" -ForegroundColor Green
}
else {
    Write-Host "Using cached .venv (pyproject.toml unchanged)" -ForegroundColor Green
}

$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

uv run pytest tests/ -v -p pytest_asyncio -p pytest_cov --cov=custom_components.mabwarp --cov-report=term-missing
