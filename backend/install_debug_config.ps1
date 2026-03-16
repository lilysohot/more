# PowerShell 脚本：为 docker-compose.yml 添加调试端口

$dockerComposePath = "C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml"
$backupPath = "C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml.backup"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker 调试配置安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查文件是否存在
if (-not (Test-Path $dockerComposePath)) {
    Write-Host "错误：找不到 docker-compose.yml" -ForegroundColor Red
    Write-Host "路径：$dockerComposePath" -ForegroundColor Yellow
    exit 1
}

Write-Host "找到文件：$dockerComposePath" -ForegroundColor Green
Write-Host ""

# 创建备份
Write-Host "[1/4] 创建备份..." -ForegroundColor Cyan
Copy-Item $dockerComposePath $backupPath
Write-Host "备份已创建：$backupPath" -ForegroundColor Green
Write-Host ""

# 读取文件内容
Write-Host "[2/4] 修改配置文件..." -ForegroundColor Cyan
$content = Get-Content $dockerComposePath -Raw

# 检查是否已经添加了调试端口
if ($content -match '-\s*"5678:5678"') {
    Write-Host "调试端口已经存在，跳过添加" -ForegroundColor Yellow
} else {
    # 在 ports: - "8000:8000" 后面添加调试端口
    $newContent = $content -replace '(^\s*-\s*"8000:8000"\r?\n)', '$1      - "5678:5678"  # 调试端口`n'
    
    if ($newContent -eq $content) {
        Write-Host "警告：无法自动添加调试端口，请手动修改" -ForegroundColor Yellow
    } else {
        $content = $newContent
        Write-Host "已添加调试端口：5678" -ForegroundColor Green
    }
}

# 检查是否已经添加了 command
if ($content -match 'debugpy') {
    Write-Host "调试器命令已经存在，跳过添加" -ForegroundColor Yellow
} else {
    # 在 backend 服务中添加 command
    $commandText = @"
    command: >
      python -m debugpy --listen 0.0.0.0:5678 --wait-for-client 
      -m uvicorn app.main:app --host 0.0.0.0 --port 8000
"@
    
    # 在 restart: unless-stopped 前面插入 command
    $newContent = $content -replace '(^\s+restart:\s*unless-stopped\r?\n)', "    $commandText`n$1"
    
    if ($newContent -eq $content) {
        Write-Host "警告：无法自动添加 command，请手动修改" -ForegroundColor Yellow
    } else {
        $content = $newContent
        Write-Host "已添加调试器启动命令" -ForegroundColor Green
    }
}

# 保存修改
Write-Host "[3/4] 保存配置..." -ForegroundColor Cyan
Set-Content $dockerComposePath $content -NoNewline
Write-Host "配置已保存" -ForegroundColor Green
Write-Host ""

# 重启容器
Write-Host "[4/4] 重启 Docker 容器..." -ForegroundColor Cyan
Write-Host ""

$composeDir = Split-Path $dockerComposePath -Parent

Write-Host "停止现有容器..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "使用新配置启动..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host ""
Write-Host "等待容器启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "检查容器状态..." -ForegroundColor Cyan
docker ps | Select-String "more_backend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host "1. 在 VS Code 中打开项目" -ForegroundColor White
Write-Host "2. 在 app/api/deps.py 第 17 行设置断点" -ForegroundColor White
Write-Host "3. 按 F5，选择 'Docker: Attach to Container'" -ForegroundColor White
Write-Host "4. 发送请求到 http://localhost:8000/api/v1/auth/me" -ForegroundColor White
Write-Host ""
Write-Host "如果出现问题，可以恢复备份：" -ForegroundColor Yellow
Write-Host "Copy-Item $backupPath $dockerComposePath" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
