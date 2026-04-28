# Tushare 数据缺失问题诊断与新方案

## 背景

当前报告已经生成了多版，但核心财务数据长期显示缺失。问题集中在后台分析流程的数据采集阶段：

```python
skill = await get_tushare_skill(token=tushare_token)
company_data = await skill.collect_all(stock_code=stock_code, company_name=company_name)
```

报告生成、Agent 分析和结构化报告都依赖 `company_data`。如果 `collect_all` 返回的 `revenue`、`net_profit`、`roe`、`market_cap` 等字段为空，下游只能继续生成缺数报告。

## 当前结论

数据缺失不是单一问题，而是两类问题叠加造成的。

### 1. 当前 Tushare Token 权限不足

本地真实诊断中，当前 token 只有 `daily` 行情接口返回了字段：

```text
daily:
ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
```

以下接口返回无权限或频率限制：

```text
stock_basic: 触发频率限制
daily_basic: 无权限
fina_indicator: 无权限
balancesheet_vip: 无权限
balancesheet: 无权限
income_vip: 无权限
income: 无权限
cashflow_vip: 无权限
cashflow: 无权限
```

这意味着仅依赖当前 Tushare token，无法稳定获得财务三表、财务指标和估值指标。

### 2. 原 `collect_all` 实现存在字段和日期映射问题

即使 token 权限满足，原实现也容易返回空数据或旧数据：

```text
问题一：行情和估值按当天精确查询
影响：周末、节假日、停牌日会返回空表。

问题二：多处用 iloc[-1] 取最新一期
影响：Tushare 返回通常按日期倒序排列，iloc[-1] 可能取到最旧一期。

问题三：字段名和 Tushare 实际字段不一致
影响：接口有数据，但映射成 None。
```

典型字段映射问题如下：

| 目标字段 | 原期望字段 | Tushare 常见实际字段 |
| --- | --- | --- |
| `gross_margin` | `gross_profit_rate` | `grossprofit_margin` |
| `net_margin` | `net_profit_ratio` | `netprofit_margin` |
| `net_profit` | `n_income` | `n_income_attr_p` |
| `equity` | `total_eq` | `total_hldr_eqy_exc_min_int` |
| `financing_cash_flow` | `n_cashflow_fin_act` | `n_cash_flows_fnc_act` |

## 已完成的临时修复

已对 `backend/skills/tushare_skill.py` 做了第一阶段修复：

```text
1. 行情和估值改为查询最近日期窗口，不再只查当天。
2. 财务数据按日期字段排序取最新一期。
3. 适配 Tushare 常见字段别名。
4. VIP 财报接口失败时尝试普通接口。
5. collect_all 返回 source_fields，用于查看每个接口实际给了哪些字段。
6. collect_all 返回 missing_fields，用于明确最终还缺哪些报告字段。
```

新增离线回归测试：

```text
backend/tests/unit/skills/test_tushare_skill.py
```

测试覆盖：

```text
1. collect_all 能把 Tushare 实际列名映射到报告字段。
2. 行情和估值使用日期窗口，不再只用当天 trade_date。
3. VIP 财报接口失败时能回退到普通财报接口。
```

当前针对 Tushare 的单测结果：

```text
python -m pytest tests/unit/skills/test_tushare_skill.py -q
3 passed
```

## 仍然存在的问题

临时修复只能解决代码映射和查询方式问题，不能绕过 Tushare 权限。

如果继续只依赖当前 token，报告仍会缺少这些字段：

```text
revenue
net_profit
net_margin
roe
roa
asset_liability_ratio
current_assets
current_liabilities
current_ratio
quick_ratio
operating_cash_flow
investing_cash_flow
financing_cash_flow
operating_cash_flow_to_net_profit
market_cap
pe_ratio
pb_ratio
ps_ratio
```

因此，下一版不能继续把 Tushare 作为唯一主数据源。

## 新方案：多数据源财务快照层

推荐新建一个统一的财务快照采集层，不再让分析流程直接绑定 Tushare 的接口形态。

### 目标

构建一个稳定输出 `CompanyFinancialSnapshot` 的采集层：

```text
输入：company_name、stock_code
输出：统一字段结构、字段来源、数据日期、缺失字段、错误信息
```

分析服务只消费统一结构，不关心数据来自 Tushare、东方财富还是其他来源。

### 推荐数据源分工

| 数据类型 | 首选来源 | 备选来源 | 原因 |
| --- | --- | --- | --- |
| 股票身份识别 | 东方财富搜索 | Tushare `stock_basic` | 当前 Tushare `stock_basic` 频率限制明显 |
| 最新行情 | Tushare `daily` | 东方财富行情 API | 当前 token 可用 `daily` |
| 估值指标 | 东方财富行情/估值接口 | Tushare `daily_basic` | 当前 token 无 `daily_basic` 权限 |
| 财务三表 | 东方财富 F10 财务接口 | Tushare 财报接口 | 当前 token 无 Tushare 财报权限 |
| 财务比率 | 本地计算 + 东方财富指标 | Tushare `fina_indicator` | 当前 token 无 `fina_indicator` 权限 |

## 新架构设计

### 1. 定义统一输出模型

建议新增后端内部模型，例如：

```python
class CompanyFinancialSnapshot(TypedDict):
    company_name: str | None
    stock_code: str | None
    ts_code: str | None
    exchange: str | None
    industry: str | None
    revenue: float | None
    net_profit: float | None
    gross_margin: float | None
    net_margin: float | None
    roe: float | None
    roa: float | None
    total_assets: float | None
    total_liabilities: float | None
    equity: float | None
    asset_liability_ratio: float | None
    current_ratio: float | None
    quick_ratio: float | None
    operating_cash_flow: float | None
    market_cap: float | None
    pe_ratio: float | None
    pb_ratio: float | None
    data_source: str
    data_date: str | None
    field_sources: dict[str, str]
    source_fields: dict[str, list[str]]
    missing_fields: list[str]
    errors: list[dict]
```

关键点：

```text
field_sources 表示每个字段来自哪个源。
source_fields 表示每个接口实际返回了哪些字段。
missing_fields 表示最终还缺什么。
errors 表示哪些接口失败、失败原因是什么。
```

### 2. 建立数据源 Provider 接口

建议拆成可替换的数据源 Provider：

```text
FinancialDataProvider
- resolve_stock()
- get_market_snapshot()
- get_valuation_snapshot()
- get_financial_statement_snapshot()
- get_financial_indicator_snapshot()
```

第一批 Provider：

```text
TushareProvider
EastMoneyProvider
```

后续可以增加：

```text
AkShareProvider
ManualUploadProvider
CachedSnapshotProvider
```

### 3. 建立合并策略

新增一个 `FinancialSnapshotCollector` 负责合并多个数据源。

推荐合并顺序：

```text
1. 先解析股票身份：优先东方财富，Tushare 作为补充。
2. 并行请求可用数据源。
3. 每个字段按优先级填充。
4. 记录字段来源。
5. 输出缺失字段和数据质量说明。
```

字段优先级示例：

| 字段 | 优先级 |
| --- | --- |
| `stock_code/company_name/exchange` | 东方财富 > Tushare |
| `close_price` | Tushare daily > 东方财富 |
| `market_cap/pe_ratio/pb_ratio` | 东方财富 > Tushare daily_basic |
| `revenue/net_profit/total_assets` | 东方财富 F10 > Tushare 财报 |
| `roe/gross_margin/current_ratio` | 本地计算 > 东方财富指标 > Tushare fina_indicator |

### 4. 增加数据质量门禁

当前流程会在字段大量缺失时继续生成报告，导致用户看到“像报告但没有数据”的结果。

建议增加门禁：

```text
核心字段不足时，不直接生成正式报告。
改为生成“数据不足报告”或提示用户补充数据源配置。
```

建议核心字段：

```text
company_name
stock_code
revenue
net_profit
operating_cash_flow
roe
market_cap
pe_ratio
```

门禁规则：

```text
如果核心字段缺失超过 40%，标记 insufficient_data=True。
如果 revenue、net_profit、total_assets 三者全缺，停止正式分析。
如果只有估值缺失，可以继续生成报告，但明确标注估值数据不足。
```

### 5. 增加本地缓存

Tushare 和东方财富都可能限频或临时失败。

建议新增本地缓存表或 JSON 快照：

```text
financial_snapshots
- id
- stock_code
- company_name
- data_date
- snapshot_json
- data_quality_json
- created_at
```

缓存策略：

```text
1. 同一股票当天优先复用缓存。
2. 采集失败时允许使用最近 7 天缓存，但报告必须标注数据日期。
3. 手动刷新时绕过缓存。
```

## 实施计划

### Phase 1：止血

目标：让系统不再静默生成大面积缺数报告。

任务：

```text
1. 在 _collect_company_data 后检查 missing_fields。
2. 如果核心字段缺失过多，写入 data_quality.insufficient_data。
3. 报告顶部展示数据不足原因。
4. 保留 Tushare 的 source_fields/missing_fields 诊断输出。
```

验收标准：

```text
用户能清楚看到是数据源权限不足，而不是报告生成失败。
```

### Phase 2：接入东方财富财务数据作为主财务源

目标：在不依赖 Tushare 高级权限的情况下补齐财务三表和估值字段。

任务：

```text
1. 重构现有 DataCollector，拆出 EastMoneyProvider。
2. 明确东方财富 F10 接口返回字段和单位。
3. 映射 revenue、net_profit、total_assets、total_liabilities、equity、cash_flow。
4. 增加字段级单元测试。
```

验收标准：

```text
以 600089 特变电工为样例，核心字段缺失率低于 30%。
```

### Phase 3：统一采集编排层

目标：让分析流程只调用统一采集器。

任务：

```text
1. 新增 FinancialSnapshotCollector。
2. 接入 TushareProvider 和 EastMoneyProvider。
3. 增加字段级来源记录 field_sources。
4. 替换 AnalysisService._collect_company_data 的直接 Tushare 调用。
```

验收标准：

```text
AnalysisService 不再直接调用 get_tushare_skill().collect_all() 作为唯一数据源。
```

### Phase 4：缓存和可观测性

目标：稳定生产体验，降低接口限频影响。

任务：

```text
1. 增加财务快照缓存。
2. 记录每次采集的接口成功率、缺失字段和错误原因。
3. 在日志中输出数据质量摘要。
4. 后续前端报告页展示数据来源和缺失字段。
```

验收标准：

```text
同一股票重复生成报告时，不会反复打外部接口导致限频。
```

## 不推荐的方案

### 继续只依赖 Tushare

不推荐。

原因：

```text
当前 token 权限不足，升级权限不可控。
即使升级，stock_basic 仍有频率限制。
一旦 Tushare 单点失败，报告继续缺数。
```

### 在报告模板中隐藏缺失字段

不推荐。

原因：

```text
隐藏缺数不能解决数据问题，会让用户误以为分析完整。
投资报告必须明确展示数据质量。
```

### 让 LLM 补全财务数据

不推荐。

原因：

```text
LLM 可能编造数值。
财务数据必须来自可追踪数据源。
```

## 推荐决策

推荐采用“多数据源财务快照层”方案。

短期用 `missing_fields` 和 `source_fields` 止血，让缺数原因透明化。

中期把东方财富财务数据作为主财务源，Tushare 作为行情和可用字段补充。

长期建立统一的 `FinancialSnapshotCollector`、缓存和数据质量门禁，让报告生成只依赖稳定的内部财务快照结构。

## 下一步

建议下一次开发直接从 Phase 1 和 Phase 2 开始：

```text
1. 给 AnalysisService 增加数据质量门禁。
2. 把东方财富财务接口整理成 EastMoneyProvider。
3. 用 600089 特变电工做端到端验收样例。
4. 确认核心字段是否能被真实填充。
```
