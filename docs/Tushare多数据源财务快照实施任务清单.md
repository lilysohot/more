# Tushare 多数据源财务快照实施任务清单

来源文档：`docs/Tushare数据缺失问题诊断与新方案.md`

## 1. 文档目的

本文档将“多数据源财务快照层”方案拆解为可直接执行的开发任务。每个任务都包含：

1. 明确目标
2. 具体改动文件
3. 逐步执行步骤
4. 验收标准
5. 验证命令
6. 下一任务进入条件

本文档不讨论方案优劣，只用于落地执行。

## 2. 执行原则

1. 每个任务完成后，系统必须保持可运行。
2. 每个任务都要有聚焦测试，不依赖真实外网作为默认验证方式。
3. 数据缺失不能再静默吞掉，必须进入 `data_quality`、`missing_fields` 或错误日志。
4. 先完成后端契约和数据质量门禁，再做多数据源合并和缓存。
5. 不允许“先写完再统一联调”，必须按检查点逐段闭环。

## 3. 目标范围

本次实施必须完成：

1. 统一的 `CompanyFinancialSnapshot` 契约
2. `EastMoneyProvider` 和 `TushareProvider`
3. `FinancialSnapshotCollector` 多源合并逻辑
4. `AnalysisService` 的数据质量门禁
5. 报告接口和报告页对数据质量的可见化
6. 财务快照缓存和手动绕过缓存能力
7. 基于 `600089` 特变电工样例的端到端验收

本次实施不包含：

1. 新增第三个数据源如 AkShare
2. 用 LLM 推断缺失财务数据
3. 大规模历史快照回填脚本

## 4. 依赖图

```text
基线样例和字段清单
    ↓
统一快照契约
    ↓
数据质量规则
    ↓
Provider 接口
    ↓
EastMoneyProvider / TushareProvider
    ↓
FinancialSnapshotCollector
    ↓
AnalysisService 接入
    ↓
报告结构化输出扩展
    ↓
缓存层
    ↓
前端报告页显示
    ↓
端到端验收
```

## 5. 任务清单

### 任务 0：冻结基线样例和字段缺失现状

**目标**

固定一个可复现样例，避免开发过程中“问题是否真的改善”无法比较。

**依赖**

1. 无

**涉及文件**

1. `docs/Tushare数据缺失问题诊断与新方案.md`
2. 新增 `backend/tests/fixtures/financial_snapshot/600089_baseline_summary.json`

**执行步骤**

1. 用当前诊断脚本对 `600089` 执行一次真实采集，保留 `source_fields`、`missing_fields`、`non_null_fields`。
2. 将脱敏后的采集摘要保存到 `backend/tests/fixtures/financial_snapshot/600089_baseline_summary.json`。
3. 在诊断文档中补充该基线文件路径，作为后续验收对照源。

**交付物**

1. 一个固定的 `600089` 基线摘要文件
2. 文档中明确写明“后续验收统一对照此基线”

**验收标准**

1. 基线文件中包含 `company_name`、`stock_code`、`source_fields`、`missing_fields`。
2. 文件中不包含 token、请求头、Cookie 等敏感信息。

**验证命令**

1. `python -m pytest tests/unit/skills/test_tushare_skill.py -q`
2. 人工检查 `backend/tests/fixtures/financial_snapshot/600089_baseline_summary.json`

**下一任务进入条件**

1. 基线文件已提交到仓库。

---

### 任务 1：定义统一财务快照契约和常量

**目标**

让所有后续 Provider、Collector、AnalysisService、报告层都围绕同一份字段契约开发。

**依赖**

1. 任务 0

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/__init__.py`
2. 新增 `backend/app/services/financial_snapshot/types.py`
3. 新增 `backend/app/services/financial_snapshot/constants.py`
4. 新增 `backend/tests/unit/services/financial_snapshot/test_types_and_constants.py`

**执行步骤**

1. 在 `types.py` 中定义 `CompanyFinancialSnapshot`、`ProviderErrorInfo`、`ProviderResult`。
2. 在 `constants.py` 中定义：全部输出字段、核心字段、字段优先级分组、默认缺失字段规则。
3. 约定 `field_sources`、`source_fields`、`missing_fields`、`errors` 的结构。
4. 为字段常量和核心字段门禁写单测，避免后续拼写漂移。

**交付物**

1. 统一契约文件
2. 字段常量文件
3. 契约单测

**验收标准**

1. 核心字段至少覆盖：`company_name`、`stock_code`、`revenue`、`net_profit`、`operating_cash_flow`、`roe`、`market_cap`、`pe_ratio`。
2. `errors` 结构至少包含 `provider`、`stage`、`message`。
3. 单测能验证核心字段集合不会被误删。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_types_and_constants.py -q`

**下一任务进入条件**

1. 契约文件与文档字段保持一致。

---

### 任务 2：实现数据质量评估器

**目标**

把“字段缺失是否足以阻止正式报告”从业务代码中抽离成可测试规则。

**依赖**

1. 任务 1

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/quality.py`
2. 新增 `backend/tests/unit/services/financial_snapshot/test_quality.py`

**执行步骤**

1. 在 `quality.py` 中实现 `evaluate_snapshot_quality(snapshot)`。
2. 输出至少包含：`insufficient_data`、`missing_core_fields`、`missing_ratio`、`quality_note`。
3. 编码以下规则：核心字段缺失率大于 40% 时，`insufficient_data=True`。
4. 编码以下规则：当 `revenue`、`net_profit`、`total_assets` 全缺时，直接标记不可进入正式分析。
5. 编码以下规则：当仅估值字段缺失时，允许继续分析，但 `quality_note` 明确写出估值不足。
6. 用纯快照假数据编写单测，覆盖 4 种场景：数据完整、仅估值缺失、财务核心缺失、全量缺失。

**交付物**

1. 质量评估器
2. 四类场景单测

**验收标准**

1. 任何一类缺失场景都能产生稳定的 `quality_note`。
2. 规则变更只需要调整 `quality.py` 和测试，不需要改多个业务文件。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_quality.py -q`

**下一任务进入条件**

1. 数据质量逻辑已可单独调用。

---

### 任务 3：在 AnalysisService 中接入止血门禁

**目标**

在多数据源 Collector 完成前，先阻止系统继续静默产出大面积缺数报告。

**依赖**

1. 任务 2

**涉及文件**

1. `backend/app/services/analysis.py`
2. `backend/app/services/structured_report.py`
3. 新增 `backend/tests/unit/services/test_analysis_service_data_quality.py`
4. 更新 `backend/tests/unit/services/test_structured_report.py`

**执行步骤**

1. 在 `_collect_company_data` 返回后调用 `evaluate_snapshot_quality()`。
2. 将 `insufficient_data`、`quality_note`、`missing_core_fields` 写入 `company_data` 或单独的数据质量结构。
3. 在 `build_structured_report_payload()` 中把这些字段写入 `data_quality`。
4. 当不可进入正式分析时，不中断任务，但报告正文必须插入“数据不足说明”。
5. 增加单测验证：当财务核心字段缺失时，结构化报告包含 `insufficient_data=True`。

**交付物**

1. AnalysisService 止血门禁
2. 结构化报告中的数据质量字段扩展
3. 聚焦回归测试

**验收标准**

1. 报告不再只显示空指标，而能明确说明“数据源权限不足或字段缺失”。
2. `GET /analyses/{id}/report` 返回的 `data_quality` 可被前端直接消费。

**验证命令**

1. `python -m pytest tests/unit/services/test_analysis_service_data_quality.py -q`
2. `python -m pytest tests/unit/services/test_structured_report.py -q`

**下一任务进入条件**

1. 后端已能明确表达“数据不足”，即使还没补齐数据源。

---

### 检查点 A：止血闭环

必须同时满足：

1. `collect_all` 仍可运行。
2. 数据不足不再静默。
3. `tests/unit/skills/test_tushare_skill.py` 通过。
4. 新增的 `AnalysisService` 数据质量测试通过。

未通过时，不进入 Provider 重构阶段。

---

### 任务 4：创建 Provider 包和抽象接口

**目标**

把“一个类直连一个外部源”的逻辑抽象成统一接口，为 EastMoney 和 Tushare 并行接入做准备。

**依赖**

1. 检查点 A

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/providers/__init__.py`
2. 新增 `backend/app/services/financial_snapshot/providers/base.py`
3. 新增 `backend/tests/unit/services/financial_snapshot/test_provider_base.py`

**执行步骤**

1. 定义 `FinancialDataProvider` 抽象接口。
2. 接口必须包含：`resolve_stock()`、`get_market_snapshot()`、`get_valuation_snapshot()`、`get_financial_statement_snapshot()`、`get_financial_indicator_snapshot()`。
3. 统一规定每个方法返回 `ProviderResult`，而不是原始第三方 payload。
4. 用 fake provider 写一组单测，验证返回结构统一。

**交付物**

1. Provider 抽象接口
2. ProviderResult 约束测试

**验收标准**

1. 后续 Provider 不允许直接向 Collector 暴露东方财富或 Tushare 的原始字段名。
2. 任何 Provider 方法失败时，都能返回结构化错误信息。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_provider_base.py -q`

**下一任务进入条件**

1. 抽象接口稳定，不再变更方法名。

---

### 任务 5：实现 EastMoneyProvider 的股票识别、行情和估值接口

**目标**

先把最稳定、最关键的“股票身份识别”和“估值字段”从现有 `DataCollector` 中抽离出来。

**依赖**

1. 任务 4

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/providers/eastmoney.py`
2. `backend/app/services/data_collector.py`
3. 新增 `backend/tests/unit/services/financial_snapshot/test_eastmoney_provider_identity_and_market.py`
4. 新增 `backend/tests/fixtures/eastmoney/`

**执行步骤**

1. 提取现有 `resolve_stock()` 逻辑到 `EastMoneyProvider.resolve_stock()`。
2. 提取东方财富行情接口到 `get_market_snapshot()`。
3. 提取东方财富估值字段到 `get_valuation_snapshot()`。
4. 将单位标准化：金额统一为元，百分比统一为数值百分比，不转字符串。
5. 为股票搜索、行情、估值分别准备 fixture JSON。
6. 用 fixture 驱动 provider 单测，不允许测试直接打外网。

**交付物**

1. EastMoneyProvider 初版
2. 身份识别和估值映射测试
3. 脱网 fixture 文件

**验收标准**

1. `resolve_stock()` 对 `600089` 返回公司名、股票代码、交易所。
2. `get_valuation_snapshot()` 至少返回 `market_cap`、`pe_ratio`、`pb_ratio` 的标准字段。
3. provider 层不再返回 `f116`、`f162` 这种第三方原始字段名。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_eastmoney_provider_identity_and_market.py -q`

**下一任务进入条件**

1. 东方财富基础 Provider 已可独立验证。

---

### 任务 6：实现 EastMoneyProvider 的财务三表映射

**目标**

把东方财富 F10 财务接口真正转成统一财务快照字段，补齐当前最缺的财务核心字段。

**依赖**

1. 任务 5

**涉及文件**

1. `backend/app/services/financial_snapshot/providers/eastmoney.py`
2. 新增 `backend/tests/unit/services/financial_snapshot/test_eastmoney_provider_financials.py`
3. 新增 `backend/tests/fixtures/eastmoney/600089_financial_summary.json`
4. 新增 `backend/tests/fixtures/eastmoney/600089_solvency.json`
5. 如需要，新增更多 F10 fixture

**执行步骤**

1. 明确当前东方财富已使用接口和返回字段单位。
2. 把以下字段映射到统一快照：`revenue`、`net_profit`、`total_assets`、`total_liabilities`、`equity`、`asset_liability_ratio`、`current_ratio`、`quick_ratio`。
3. 如果一个接口只能给部分字段，保留 `field_sources` 和 `source_fields` 记录。
4. 在 provider 内部计算必要衍生字段，如 `debt_to_equity`。
5. 用 fixture 写字段级断言，逐个校验金额和百分比单位。

**交付物**

1. EastMoneyProvider 财务字段映射
2. 金额和比例字段单测

**验收标准**

1. `600089` 样例下至少能返回：`revenue`、`net_profit`、`total_assets`、`total_liabilities`、`equity`。
2. 所有金额字段单位一致。
3. `asset_liability_ratio` 不允许同时返回原始字符串和数值两套格式。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_eastmoney_provider_financials.py -q`

**下一任务进入条件**

1. 东方财富已具备“主财务源”能力。

---

### 任务 7：实现 TushareProvider 适配层

**目标**

保留现有 Tushare 行情能力，但不再让上层直接依赖 `TushareSkill` 的输出结构。

**依赖**

1. 任务 4
2. 现有 `backend/skills/tushare_skill.py` 已完成第一阶段修复

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/providers/tushare.py`
2. `backend/skills/tushare_skill.py`
3. 新增 `backend/tests/unit/services/financial_snapshot/test_tushare_provider.py`

**执行步骤**

1. 在 `tushare.py` 中封装对 `get_tushare_skill()` 的调用。
2. 将 `resolve_stock()`、`get_daily_price()`、`get_valuation_data()`、`get_financial_data()` 的结果转换成 `ProviderResult`。
3. 对权限不足场景统一写入 `errors`，不能只打日志。
4. 保留 `source_fields` 和 `missing_fields`，供 Collector 合并时使用。
5. 用 fake skill 编写单测，覆盖“有行情、无财务权限”的场景。

**交付物**

1. TushareProvider
2. 权限受限场景单测

**验收标准**

1. TushareProvider 至少能稳定输出 `close_price`、`trade_date` 和权限错误信息。
2. 上层不再直接感知 `TushareSkill.collect_all()` 的返回结构。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_tushare_provider.py -q`
2. `python -m pytest tests/unit/skills/test_tushare_skill.py -q`

**下一任务进入条件**

1. 两个 Provider 都已能独立跑通单测。

---

### 检查点 B：Provider 闭环

必须同时满足：

1. EastMoneyProvider 聚焦测试通过。
2. TushareProvider 聚焦测试通过。
3. Tushare 原单测仍通过。
4. 现有 `DataCollector` 未被破坏。

未通过时，不进入 Collector 开发。

---

### 任务 8：实现 FinancialSnapshotCollector 多源合并逻辑

**目标**

把两个 Provider 的结果合并成最终统一快照，并记录字段级来源。

**依赖**

1. 检查点 B

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/collector.py`
2. 新增 `backend/tests/unit/services/financial_snapshot/test_collector_merge.py`

**执行步骤**

1. 在 Collector 构造函数中接收 `EastMoneyProvider` 和 `TushareProvider`。
2. 先调用股票身份识别，优先东方财富，失败再回退 Tushare。
3. 并行获取行情、估值、财务三表、财务指标。
4. 按字段优先级填充最终快照。
5. 同时维护 `field_sources`、`source_fields`、`missing_fields`、`errors`。
6. 调用 `evaluate_snapshot_quality()`，把质量结果写回快照。
7. 用 fake provider 编写合并测试，至少覆盖以下 4 类场景：东方财富主财务源成功、Tushare 仅行情成功、两源部分成功、两源同时失败。

**交付物**

1. Collector 实现
2. 四类合并场景单测

**验收标准**

1. 合并后的 `field_sources` 能准确说明每个字段来自哪个 Provider。
2. 当两个源都失败时，`errors` 里必须保留两边错误。
3. `missing_fields` 只基于最终合并结果计算，不基于单个 Provider 的中间结果。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_collector_merge.py -q`

**下一任务进入条件**

1. Collector 可脱网完成全部合并逻辑验证。

---

### 任务 9：替换 AnalysisService 的单源采集流程

**目标**

让分析主流程不再把 Tushare 当唯一主数据源，而是改为只依赖 Collector 输出。

**依赖**

1. 任务 8

**涉及文件**

1. `backend/app/services/analysis.py`
2. 新增 `backend/tests/unit/services/test_analysis_service_snapshot_integration.py`

**执行步骤**

1. 在 `AnalysisService._collect_company_data()` 中实例化 `FinancialSnapshotCollector`。
2. 移除“先 Tushare 再 EastMoney fallback”的硬编码顺序。
3. 保持原有返回字段兼容，避免破坏 `ReportGenerator` 和 Agent 上下文。
4. 将 Collector 输出的 `field_sources`、`missing_fields`、`errors` 一并保留到 `company_data`。
5. 用 fake collector 写集成单测，验证 `AnalysisService` 消费统一快照。

**交付物**

1. AnalysisService 改造完成
2. 集成单测

**验收标准**

1. `AnalysisService` 不再直接调用 `get_tushare_skill().collect_all()` 作为唯一数据采集入口。
2. `company_data` 仍能被后续财务比率和报告流程消费。

**验证命令**

1. `python -m pytest tests/unit/services/test_analysis_service_snapshot_integration.py -q`
2. `python -m pytest tests/unit/services/test_analysis_service_multi_agent.py -q`

**下一任务进入条件**

1. 主分析流程已切到 Collector。

---

### 任务 10：扩展报告结构化输出和 API 契约

**目标**

让前端能够拿到 `field_sources`、`missing_fields`、`errors`、`insufficient_data` 等完整信息。

**依赖**

1. 任务 9

**涉及文件**

1. `backend/app/services/structured_report.py`
2. `backend/app/schemas/analysis.py`
3. `backend/app/api/analyses.py`
4. `backend/tests/unit/api/test_report_endpoint_contract.py`
5. `backend/tests/unit/services/test_structured_report.py`

**执行步骤**

1. 扩展 `StructuredReportDataQuality`，补充 `insufficient_data`、`missing_core_fields`、`field_sources`、`errors`。
2. 更新报告组装逻辑，使新增字段进入 API 响应。
3. 更新 API 契约测试，确保旧字段仍兼容，新字段可选返回。
4. 验证前端不读取这些字段时也不受影响。

**交付物**

1. 更新后的报告 Schema
2. 报告响应契约测试

**验收标准**

1. `GET /analyses/{id}/report` 返回的数据质量信息足以解释缺数原因。
2. `content_md/content_html` 兼容不变。

**验证命令**

1. `python -m pytest tests/unit/api/test_report_endpoint_contract.py -q`
2. `python -m pytest tests/unit/services/test_structured_report.py -q`

**下一任务进入条件**

1. 报告 API 已完整暴露新数据质量字段。

---

### 检查点 C：后端主链路闭环

必须同时满足：

1. AnalysisService 已切到 Collector。
2. 报告 API 暴露完整数据质量信息。
3. `600089` 样例在假数据测试下缺失率低于原基线。
4. 新增后端测试全部通过。

未通过时，不进入缓存和前端阶段。

---

### 任务 11：新增财务快照缓存表和 Alembic 迁移

**目标**

为重复报告生成提供稳定缓存，降低外部源限频影响。

**依赖**

1. 检查点 C

**涉及文件**

1. `backend/app/models/user.py`
2. 新增 `backend/alembic/versions/00x_financial_snapshots.py`
3. 如需要，更新 `backend/app/models/__init__.py`
4. 新增 `backend/tests/unit/services/financial_snapshot/test_cache_model_payload.py`

**执行步骤**

1. 在模型层新增 `financial_snapshots` 表。
2. 字段至少包含：`id`、`stock_code`、`company_name`、`data_date`、`snapshot_json`、`data_quality_json`、`created_at`。
3. 补充 Alembic migration，包含 `upgrade()` 和 `downgrade()`。
4. 为 `stock_code + data_date` 建索引，支持快速查当天快照。
5. 为 JSON 结构写模型层单测或最小序列化测试。

**交付物**

1. 新模型
2. 新 migration
3. 序列化测试

**验收标准**

1. 模型和 migration 同步存在。
2. JSON 字段能存储快照和数据质量信息。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_cache_model_payload.py -q`
2. `alembic upgrade head`

**下一任务进入条件**

1. 本地迁移可成功执行。

---

### 任务 12：实现缓存读写和手动绕过缓存能力

**目标**

让 Collector 在默认情况下优先复用当天缓存，并允许显式强制刷新。

**依赖**

1. 任务 11

**涉及文件**

1. 新增 `backend/app/services/financial_snapshot/cache.py`
2. `backend/app/services/financial_snapshot/collector.py`
3. `backend/app/services/analysis.py`
4. `backend/app/schemas/analysis.py`
5. `backend/app/api/analyses.py`
6. 新增 `backend/tests/unit/services/financial_snapshot/test_cache_service.py`
7. 新增 `backend/tests/unit/api/test_analysis_force_refresh_contract.py`

**执行步骤**

1. 在 `cache.py` 中实现读取当天快照、写入快照、读取最近 7 天可用快照的方法。
2. 在 Collector 中加入缓存读取顺序：当天缓存 -> 实时采集 -> 最近 7 天降级缓存。
3. 当使用历史缓存时，在 `quality_note` 中注明“使用历史缓存”。
4. 在创建分析请求或相关入口增加 `force_refresh` 布尔参数。
5. 当 `force_refresh=True` 时，Collector 必须跳过读缓存，直接实时采集。
6. 增加缓存服务和 API 契约测试。

**交付物**

1. 缓存服务
2. `force_refresh` API 参数
3. 缓存命中和绕过缓存测试

**验收标准**

1. 同一股票当天重复生成报告时，默认不重复打外部接口。
2. `force_refresh=True` 时，缓存不会被读取。
3. 采集失败但近 7 天有缓存时，可返回降级快照。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_cache_service.py -q`
2. `python -m pytest tests/unit/api/test_analysis_force_refresh_contract.py -q`

**下一任务进入条件**

1. 缓存路径和强制刷新路径都可单独验证。

---

### 任务 13：增加后端可观测性日志

**目标**

让每次采集结果都可追溯，便于后续排查“为什么该股票还是缺数”。

**依赖**

1. 任务 12

**涉及文件**

1. `backend/app/services/financial_snapshot/collector.py`
2. `backend/app/services/analysis.py`
3. 新增 `backend/tests/unit/services/financial_snapshot/test_collector_logging_summary.py`

**执行步骤**

1. 在 Collector 完成后输出一条结构化摘要日志。
2. 日志最少包含：`stock_code`、`providers_used`、`missing_fields_count`、`missing_core_fields`、`insufficient_data`、`data_date`。
3. 对 provider 失败保留精简错误，不输出敏感凭据。
4. 用 `caplog` 写日志单测，验证关键字段出现在日志中。

**交付物**

1. 结构化采集摘要日志
2. 日志单测

**验收标准**

1. 单条日志即可帮助定位是“权限不足”“限频”“缓存回退”还是“字段缺失”。
2. 日志中不出现 token 或第三方响应全文。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot/test_collector_logging_summary.py -q`

**下一任务进入条件**

1. 后端已经可观测。

---

### 任务 14：在前端报告页展示数据质量与字段缺失

**目标**

把后端已经提供的数据质量信息展示给用户，避免用户只看到空白或空指标。

**依赖**

1. 任务 10
2. 任务 13

**涉及文件**

1. `frontend/src/types/index.ts`
2. `frontend/src/api/analysis.ts`
3. `frontend/src/store/analysisStore.ts`
4. `frontend/src/utils/reportViewModel.ts`
5. `frontend/src/pages/Report.tsx`
6. 如需要，新增 `frontend/src/components/report/DataQualityBanner.tsx`

**执行步骤**

1. 扩展前端报告类型，接收 `insufficient_data`、`missing_fields`、`missing_core_fields`、`quality_note`、`field_sources`。
2. 在 `reportViewModel` 中统一格式化缺失字段和质量提示文案。
3. 在报告页顶部增加 `DataQualityBanner`。
4. 当 `insufficient_data=True` 时，顶部展示明显告警，不隐藏原文报告。
5. 在合适位置展示 `data_source`、`data_date` 和缺失字段数量。

**交付物**

1. 前端数据质量展示组件
2. 报告页接入逻辑

**验收标准**

1. 用户能直接看到“数据不足”的原因。
2. 缺失字段不会导致页面崩溃。
3. 旧报告页面仍可展示原文内容。

**验证命令**

1. `pnpm lint`
2. `pnpm build`

**下一任务进入条件**

1. 前后端字段完成联动。

---

### 任务 15：完成 `600089` 端到端验收和回归基线更新

**目标**

用统一样例验证整个链路已从“静默缺数”升级为“可解释、可补齐、可回退”的新链路。

**依赖**

1. 任务 14

**涉及文件**

1. 更新 `docs/Tushare数据缺失问题诊断与新方案.md`
2. 更新 `backend/tests/fixtures/financial_snapshot/600089_baseline_summary.json`
3. 如需要，新增 `backend/tests/unit/services/test_financial_snapshot_e2e_summary.py`

**执行步骤**

1. 对 `600089` 运行一次完整流程，记录最终快照和报告数据质量。
2. 对比任务 0 中的基线摘要。
3. 统计核心字段缺失率是否低于 30%。
4. 确认缓存命中、强制刷新、历史缓存降级三种路径都可用。
5. 更新基线摘要文件和诊断文档中的“当前状态”说明。

**交付物**

1. 更新后的基线摘要
2. 端到端验收记录
3. 文档中明确写出实施前后变化

**验收标准**

1. `600089` 样例核心字段缺失率低于 30%。
2. 当字段仍缺失时，报告能清楚解释原因。
3. 缓存和强制刷新路径均验证通过。

**验证命令**

1. `python -m pytest tests/unit/services/financial_snapshot -q`
2. `python -m pytest tests/unit/services/test_analysis_service_snapshot_integration.py -q`
3. `python -m pytest tests/unit/api/test_report_endpoint_contract.py -q`
4. `pnpm lint`
5. `pnpm build`

**下一任务进入条件**

1. 无。此任务完成即本项目闭环完成。

## 6. 最终闭环检查表

所有任务完成后，必须逐项确认：

1. `AnalysisService` 已不再单点依赖 Tushare。
2. `EastMoneyProvider` 已成为主财务源。
3. `TushareProvider` 仅承担可用行情与补充字段角色。
4. `FinancialSnapshotCollector` 已统一产出快照、来源、缺失字段和错误列表。
5. 数据质量门禁已经阻止静默缺数报告。
6. 报告 API 已暴露数据质量信息。
7. 前端报告页已展示数据不足原因。
8. 缓存、历史回退和强制刷新路径已验证。
9. `600089` 样例已完成前后对比验收。

只要上述 9 项有任意 1 项未满足，本次改造不算完成。

## 7. 建议执行顺序

建议严格按以下顺序推进：

1. 任务 0 到 3
2. 检查点 A
3. 任务 4 到 7
4. 检查点 B
5. 任务 8 到 10
6. 检查点 C
7. 任务 11 到 15

不要跳过检查点，不要并行推进尚未冻结契约的任务。
