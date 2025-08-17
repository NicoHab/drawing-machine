# start-dev-environment.ps1
Write-Host "🎨 Starting Drawing Machine Development Environment..." -ForegroundColor Cyan

# Navigate to project directory
Set-Location "C:\development\drawing-machine"
Write-Host "📁 Working directory: C:\development\drawing-machine" -ForegroundColor Green

# Start Docker services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services
Write-Host "⏳ Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Show containers
Write-Host "🔍 Running containers:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}"

# Show URLs
Write-Host "🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "   📊 Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "   📈 Prometheus: http://localhost:9090" -ForegroundColor White

# Open VS Code
Write-Host "💻 Opening VS Code..." -ForegroundColor Yellow
code drawing-machine.code-workspace

Write-Host "🎉 Development environment ready!" -ForegroundColor Green
Read-Host "Press Enter to close"
