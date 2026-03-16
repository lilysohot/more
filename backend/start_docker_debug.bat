@echo off
echo ========================================
echo Docker 调试模式启动脚本
echo ========================================
echo.

echo [1/4] 停止现有容器...
docker stop moremoney_backend 2>nul
docker rm moremoney_backend 2>nul

echo.
echo [2/4] 使用调试配置启动容器...
docker-compose -f docker-compose.debug.yml up -d --build

echo.
echo [3/4] 等待容器启动...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] 检查容器状态...
docker ps | findstr moremoney

echo.
echo ========================================
echo 完成！
echo ========================================
echo.
echo 下一步：
echo 1. 在 VS Code 中打开项目
echo 2. 在 app/api/deps.py 第 17 行设置断点
echo 3. 按 F5，选择 "Docker: Attach to Container"
echo 4. 发送请求到 http://localhost:8000/api/v1/auth/me
echo.
echo 查看日志：docker logs -f moremoney_backend
echo 停止容器：docker-compose -f docker-compose.debug.yml down
echo ========================================
