@echo off
echo ========================================
echo   小财大用 - 本地开发环境快速启动
echo ========================================
echo.

REM 检查 Python
echo [1/6] 检查 Python 安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.11+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python 已安装

REM 检查 Node.js
echo [2/6] 检查 Node.js 安装...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Node.js，请先安装 Node.js 18+
    echo 下载地址：https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js 已安装

REM 检查 pnpm
echo [3/6] 检查 pnpm 安装...
pnpm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未检测到 pnpm，正在安装...
    npm install -g pnpm
)
echo ✅ pnpm 已安装

REM 检查 PostgreSQL
echo [4/6] 检查 PostgreSQL 安装...
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 PostgreSQL，请先安装 PostgreSQL 15+
    echo 下载地址：https://www.postgresql.org/download/windows/
    pause
    exit /b 1
)
echo ✅ PostgreSQL 已安装

REM 检查 Redis
echo [5/6] 检查 Redis 安装...
redis-cli --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未检测到 Redis，请手动启动 Redis 服务
    echo 如果使用 WSL，请运行：wsl redis-server
    echo 如果使用 Windows 版本，请确保 redis-server.exe 正在运行
)
echo ✅ Redis 已安装或跳过

REM 配置后端
echo [6/6] 配置后端环境...
cd backend
if not exist .env (
    echo 创建 .env 文件...
    copy .env.example .env
    echo 请编辑 backend\.env 文件配置数据库连接
    echo DATABASE_URL=postgresql://moremoney:moremoney123@localhost:5432/moremoney_db
)
cd ..

echo.
echo ========================================
echo   环境检查完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 确保 PostgreSQL 服务已启动
echo 2. 确保 Redis 服务已启动
echo 3. 编辑 backend\.env 文件配置数据库
echo 4. 运行以下命令启动后端：
echo    cd backend
echo    python -m venv venv
echo    venv\Scripts\activate
echo    pip install -r requirements.txt
echo    uvicorn app.main:app --reload
echo.
echo 5. 在另一个终端启动前端：
echo    cd frontend
echo    pnpm install
echo    pnpm dev
echo.
echo 访问地址：
echo   前端：http://localhost:5173
echo   后端：http://localhost:8000
echo   API 文档：http://localhost:8000/docs
echo.
pause
