"""
重启服务器并启用调试模式
这个脚本会：
1. 自动查找并停止现有的 uvicorn 进程
2. 启动带调试模式的服务器
"""
import os
import sys
import signal

print("=" * 60)
print("调试服务器启动脚本")
print("=" * 60)

# 查找并提示停止现有进程
import subprocess

try:
    # 查找占用 8000 端口的进程
    result = subprocess.run(
        ["netstat", "-ano", "|", "findstr", ":8000"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    if result.stdout:
        print("\n检测到占用 8000 端口的进程:")
        print(result.stdout)
        print("\n请先手动停止现有的服务器 (Ctrl+C)")
        print("然后重新运行这个脚本\n")
    else:
        print("\n8000 端口未被占用，可以直接启动\n")
        
except Exception as e:
    print(f"检查端口时出错：{e}")

print("=" * 60)
print("启动调试服务器...")
print("=" * 60)

import debugpy

# 配置调试器监听
debugpy.listen(("0.0.0.0", 5678))
print("✓ 调试器已启动，监听端口：5678")
print("✓ VS Code 可以连接到这个端口")
print("\n按 Ctrl+C 停止服务器\n")

import uvicorn

# 启动 FastAPI 应用
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info"
)
