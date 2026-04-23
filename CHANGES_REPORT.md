# 更改报告

**项目**: 智能投资分析师  
**分支**: master  
**日期**: 2026-03-23  
**更改类型**: Bug 修复 + 配置更新

---

## 变更概览

| 文件 | 变更类型 | 描述 |
|------|----------|------|
| `.gitignore` | 优化 | 添加 config 文件忽略规则 |
| `backend/.env.example` | 新功能 | 添加默认 LLM 配置示例 |
| `backend/app/core/config.py` | 优化 | 添加 LLM Provider URL 配置，更新默认模型 |
| `backend/app/services/data_collector.py` | Bug 修复 | 修正东方财富 API 字段映射错误 |

---

## 详细变更说明

### 1. `.gitignore` - 配置文件忽略规则

**变更内容**:
```diff
 # Build
 dist/
-
+# config files
+config/
+config.json
+config.py
```

**更改原因**:
- 防止本地配置文件（如 `config.json`、`config.py`）被意外提交到版本库
- 避免不同开发环境的配置冲突

---

### 2. `backend/.env.example` - 默认 LLM 配置示例

**变更内容**:
```diff
 # 调试模式
 DEBUG=false
+
+# 默认 LLM 配置
+DEFAULT_LLM_PROVIDER=dashscope
+DEFAULT_LLM_MODEL=qwen-turbo
+DEFAULT_LLM_API_KEY=your-llm-api-key
```

**更改原因**:
- 为新开发者提供更清晰的默认 LLM 配置示例
- 明确默认值，便于快速启动项目

---

### 3. `backend/app/core/config.py` - LLM 配置优化

**变更内容**:

1. **导入类型扩展**:
```diff
-from typing import List
+from typing import List, Dict
```

2. **默认模型更新**:
```diff
-DEFAULT_LLM_MODEL: str = "qwen3.5-plus"
+DEFAULT_LLM_MODEL: str = "qwen-turbo"
```

3. **新增 LLM Provider URLs 配置**:
```python
# LLM Provider 默认 Base URLs
LLM_PROVIDER_URLS: Dict[str, str] = {
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai": "https://api.openai.com/v1",
    "claude": "https://api.anthropic.com/v1",
}
```

**更改原因**:

| 变更 | 技术原因 |
|------|----------|
| 添加 `Dict` 类型导入 | 支持 `LLM_PROVIDER_URLS` 字典类型定义 |
| 默认模型改为 `qwen-turbo` | `qwen-turbo` 是阿里云 DashScope 的稳定版本，响应更快，适合生产环境使用 |
| 添加 `LLM_PROVIDER_URLS` | 为未来支持多个 LLM Provider（OpenAI、Claude）做准备，统一管理 API 端点 |

**技术细节**:
- `qwen-turbo` vs `qwen3.5-plus`: 前者是轻量级模型，延迟更低，适合需要快速响应的场景
- Base URL 使用兼容模式（`compatible-mode/v1`），确保 API 调用的稳定性

---

### 4. `backend/app/services/data_collector.py` - 东方财富 API 字段映射修复

**变更内容**:
```diff
                 if data.get("data"):
                     d = data["data"]
                     info["exchange"] = "SH" if stock_code.startswith(("6", "9")) else "SZ"
-                    info["industry"] = d.get("f84")  # 所属行业
+                    # 注意：东方财富行情API (push2.eastmoney.com) 中没有行业字段
+                    # f84/f85 是数值字段（总资产等），不是行业信息
+                    # 行业信息需要通过其他API获取，暂时设为 None
+                    info["industry"] = None
                     # 估值指标
                     info["market_cap"] = d.get("f116")  # 总市值（元）
                     info["pe_ratio"] = d.get("f162")    # 市盈率
                     info["pb_ratio"] = d.get("f167")    # 市净率
-                    # 财务数据（如果API返回）
-                    info["total_assets"] = d.get("f84")   # 总资产（部分API）
-                    info["total_liabilities"] = d.get("f85")  # 总负债
-                    info["roe"] = d.get("f162")          # 净资产收益率（需要确认字段）
-                    info["gross_margin"] = d.get("f234") if d.get("f234") else None  # 毛利率
-                    info["net_profit"] = d.get("f116") if d.get("f116") else None  # 净利润
+                    # 注意：f84/f85/f162 在东方财富行情API中不是财务数据
+                    # 财务数据将通过 _get_financial_summary 和 _get_solvency_data 获取
```

**问题分析**:

原始代码错误地映射了东方财富行情 API 的字段：

| 原代码映射 | 实际问题 |
|------------|----------|
| `f84` → 行业 | f84 实际是总资产数值，不是行业信息 |
| `f84` → 总资产 | 重复映射，且字段含义错误 |
| `f85` → 总负债 | f85 实际是总负债数值，但不应从行情API获取 |
| `f162` → ROE | f162 实际是市盈率，不是净资产收益率 |
| `f116` → 净利润 | f116 实际是总市值，不是净利润 |

**修复方案**:

1. **移除错误映射**: 删除对 `f84`、`f85`、`f162` 的错误财务字段映射
2. **正确字段保留**: `f116`（总市值）、`f162`（市盈率）、`f167`（市净率）映射正确，予以保留
3. **行业字段处理**: 将 `industry` 设为 `None`，因为行情 API 确实不提供行业信息
4. **明确注释**: 添加详细注释说明各字段的实际含义，避免未来混淆

**技术说明**:

东方财富 `push2.eastmoney.com` 行情 API 的字段说明：
- `f57/f58`: 股票代码/名称
- `f116`: 总市值（元）
- `f162`: 市盈率（PE）
- `f167`: 市净率（PB）
- `f84/f85`: 总资产/总负债（这是数值字段，但行情API中数据不完整）

财务数据（总资产、总负债、资产负债率、流动比率等）应通过专门的财务 API 获取：
- `_get_financial_summary()`: 获取财务摘要（总资产、总负债、股东权益、资产负债率）
- `_get_solvency_data()`: 获取偿债能力数据（流动比率、速动比率）

---

## 影响范围

| 模块 | 影响 | 说明 |
|------|------|------|
| 配置模块 | 低 | 默认值变更，但可通过 `.env` 覆盖 |
| 数据采集 | 中 | 修复了数据准确性问题，避免错误数据进入分析流程 |
| LLM 调用 | 低 | Base URL 变化，但 `dashscope` 模式行为不变 |

---

## 依赖变更

**本次更改未引入新的依赖包。**

代码变更中使用的模块：

| 模块/包 | 类型 | 说明 |
|---------|------|------|
| `typing.Dict` | Python 标准库 | 无需安装 |
| `logging` | Python 标准库 | 无需安装 |
| `datetime` | Python 标准库 | 无需安装 |
| `re` | Python 标准库 | 无需安装 |
| `httpx` | 第三方包 | 已在 `requirements.txt` 中定义 |

---

## 测试建议

1. **数据采集测试**: 使用已知股票代码（如 `600089` 特变电工）验证数据采集准确性
2. **配置加载测试**: 验证 `LLM_PROVIDER_URLS` 能正确加载
3. **集成测试**: 通过前端发起一次完整的公司分析流程，验证数据正确性

---

## 回滚方案

如需回滚，执行以下命令：

```bash
git checkout HEAD~1 -- .gitignore backend/.env.example backend/app/core/config.py backend/app/services/data_collector.py
```

**注意**: 回滚将恢复错误的字段映射，可能导致财务数据不准确。
