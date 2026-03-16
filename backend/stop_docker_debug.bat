@echo off
echo ========================================
echo 停止 Docker 调试容器
echo ========================================
echo.

docker-compose -f docker-compose.debug.yml down

echo.
echo ========================================
echo 容器已停止
echo ========================================
echo.
echo 如需重新启动：start_docker_debug.bat
echo ========================================
