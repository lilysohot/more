"""
使用 debugpy 启动 FastAPI 的脚本
可以直接运行这个脚本来启动带调试的服务器
"""
import debugpy

# 配置调试器
debugpy.listen(("0.0.0.0", 5678))
print("调试器已启动，监听端口 5678")
print("VS Code 可以连接到这个端口进行调试")

import uvicorn

# 启动 FastAPI 应用
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=False
)
