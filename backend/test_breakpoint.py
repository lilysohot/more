"""
测试调试器是否正常工作
使用方法：
1. 在 test_breakpoint() 函数内设置断点
2. 使用 "Python: Current File" 配置运行
3. 检查断点是否暂停
"""
import debugpy

def test_breakpoint():
    """测试断点函数"""
    print("调试器版本:", debugpy.__version__)
    
    # 在这里设置断点 1
    message = "断点测试开始"
    print(message)
    
    # 在这里设置断点 2
    test_value = 42
    print(f"测试值：{test_value}")
    
    # 在这里设置断点 3
    another_value = "调试成功"
    print(f"结果：{another_value}")
    
    return another_value

if __name__ == "__main__":
    print("=== 开始调试测试 ===")
    result = test_breakpoint()
    print("测试完成:", result)
    print("=== 测试结束 ===")
