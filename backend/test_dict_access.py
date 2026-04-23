"""
测试字典访问方式
"""

# 模拟数据
data = {
    "QuotationCodeTable": {
        "Data": [
            {"Code": "603067", "Name": "振华股份"},
            {"Code": "831757", "Name": "振华股份"}
        ],
        "Status": 0,
        "Message": "成功",
        "TotalCount": 2,
        "BizCode": "",
        "BizMsg": ""
    }
}

print("=" * 60)
print("测试字典访问")
print("=" * 60)

print("\n[测试 1] data.get('QuotationCodeTable', {}).get('Data')")
result1 = data.get("QuotationCodeTable", {}).get("Data")
print(f"  结果: {result1}")
print(f"  类型: {type(result1)}")

print("\n[测试 2] data['QuotationCodeTable']")
try:
    result2 = data["QuotationCodeTable"]
    print(f"  结果: {result2}")
    print(f"  类型: {type(result2)}")
    print(f"  键: {list(result2.keys())}")
    
    result2_data = result2.get("Data")
    print(f"  .get('Data'): {result2_data}")
except Exception as e:
    print(f"  异常: {e}")

print("\n[测试 3] 检查键是否完全匹配")
print(f"  'QuotationCodeTable' in data: {'QuotationCodeTable' in data}")
print(f"  所有键: {list(data.keys())}")
print(f"  键的长度: {[len(k) for k in data.keys()]}")

print("\n" + "=" * 60)
print("结论")
print("=" * 60)
if result1 == result2.get("Data"):
    print("✓ 两种方式结果一致")
else:
    print("✗ 两种方式结果不一致")
