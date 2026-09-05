# FlowPulse Local Development Launcher (PowerShell)
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Starting FlowPulse SaaS Platform       " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

if (-not (Test-Path .env)) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker found. Launching via Docker Compose..." -ForegroundColor Green
    docker compose up --build
} else {
    Write-Host "Docker not found in PATH. You can run backend-django and engine-dotnet directly." -ForegroundColor Yellow
}
