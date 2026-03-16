@echo off
echo ========================================
echo Docker 调试配置安装脚本
echo ========================================
echo.

set COMPOSE_PATH=C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml
set BACKUP_PATH=C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml.backup

echo 找到文件：%COMPOSE_PATH%
echo.

echo [1/3] 创建备份...
copy "%COMPOSE_PATH%" "%BACKUP_PATH%"
echo 备份已创建
echo.

echo [2/3] 请手动修改 docker-compose.yml
echo.
echo 在 backend 服务的 ports 部分添加一行:
echo   ports:
echo     - "8000:8000"
echo     - "5678:5678"  # 添加这行
echo.

echo [3/3] 重启容器...
echo.
cd /d "C:\Users\admin\Desktop\智能投资分析师\more"
docker-compose down
docker-compose up -d --build

echo.
echo ========================================
echo 完成！
echo ========================================
echo.
echo 下一步:
echo 1. 在 VS Code 中按 F5
echo 2. 选择 "Docker: Attach to Container"
echo 3. 在 app/api/deps.py 第 17 行设置断点
echo 4. 发送请求测试
echo.
echo 查看日志：docker logs -f more_backend
echo ========================================
