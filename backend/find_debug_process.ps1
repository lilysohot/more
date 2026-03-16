# Find Python process using port 8000
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Find process on port 8000" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$processInfo = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess |
    ForEach-Object {
        Get-Process -Id $_ -ErrorAction SilentlyContinue
    }

if ($processInfo) {
    Write-Host "Found process:" -ForegroundColor Green
    Write-Host ""
    $processInfo | Format-Table Id, ProcessName, Path -AutoSize
    
    Write-Host "Process ID: $($processInfo.Id)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Press F5 in VS Code" -ForegroundColor White
    Write-Host "2. Select 'Python: Attach by Process ID'" -ForegroundColor White
    Write-Host "3. Choose process ID: $($processInfo.Id)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "No process found on port 8000" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "1. Server is not running" -ForegroundColor White
    Write-Host "2. Server is running on different port" -ForegroundColor White
    Write-Host "3. Insufficient permissions" -ForegroundColor White
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
