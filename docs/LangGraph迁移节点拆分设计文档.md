# LangGraph 迁移节点拆分设计文档

**文档版本**：v1.0  
**编写日期**：2026-04-23  
**适用范围**：公司分析研报助手 / 小财大用（MoreMoney）多 Agent 分析流程未来演进

---

## 一、文档目标

本文档用于回答一个具体问题：

当前系统如果未来从“手写 orchestrator”迁移到 `LangGraph`，工作流节点应该如何拆分，状态应该如何流转，哪些步骤适合做成节点，哪些步骤仍应保留在普通服务层。

本文档不建议当前立刻引入 `LangGraph`，而是提供一份未来可落地的迁移蓝图，避免后续重构时推倒重来。

---

## 二、迁移前提

只有在以下条件逐步出现后，才建议正式迁移到 `LangGraph`：

1. Agent 数量超过 4 个，并且后续还会继续增加
2. 分析流程出现条件分支，而不再是单纯线性流程
3. 需要多轮辩论、复核、追问和回退
4. 需要节点级别的重试、恢复和持久化
5. 需要清晰表达“谁依赖谁、哪一步失败后怎么走”

在此之前，建议继续使用普通 `orchestrator.py`。

---

## 三、迁移目标

迁移到 `LangGraph` 后，目标不是“为了用图而用图”，而是解决以下工程问题：

1. 把多 Agent 流程从线性代码提升为显式工作流
2. 支持条件分支和节点级决策
3. 支持中间结果持久化和断点恢复
4. 支持失败节点重试和降级路径
5. 支持未来新增更多 Agent 节点而不让编排逻辑失控

---

## 四、建议的图级拆分原则

### 4.1 适合拆成 LangGraph 节点的步骤

适合做节点的步骤应满足以下特点：

1. 输入和输出边界清晰
2. 可独立失败和重试
3. 对后续流程有明确状态影响
4. 结果可以结构化保存

### 4.2 不适合直接做图节点的步骤

以下能力更适合作为普通服务函数，被节点内部调用：

1. 数字格式化
2. Prompt 模板渲染
3. Markdown 渲染小工具
4. HTML 模板拼接细节
5. 数据清洗中的细粒度工具函数

结论：

`LangGraph` 负责“编排”，普通 service 负责“实现细节”。

---

## 五、推荐的一期节点拆分

针对你当前规划的 3 个角色 Agent + 1 个汇总 Agent，推荐未来迁移时按如下粒度拆分。

### 5.1 主流程节点

```text
START
  ↓
load_analysis_input
  ↓
collect_company_data
  ↓
calculate_financial_ratios
  ↓
build_analysis_context
  ↓
run_munger_agent
  ↓
run_industry_agent
  ↓
run_audit_agent
  ↓
aggregate_agent_outputs
  ↓
run_synthesis_agent
  ↓
generate_markdown_report
  ↓
generate_html_report
  ↓
persist_report
  ↓
END
```

这是一版最容易从现有线性流程迁移过去的图结构。

---

## 六、推荐的增强版节点拆分

如果未来加入条件路由、失败降级和多轮复核，建议升级为下面这种结构。

```text
START
  ↓
load_analysis_input
  ↓
collect_company_data
  ↓
validate_collected_data
  ↓
route_data_quality
   ├─ 数据足够 → calculate_financial_ratios
   └─ 数据不足 → enrich_missing_data
                         ↓
                   calculate_financial_ratios
  ↓
build_analysis_context
  ↓
fanout_agents
   ├─ run_munger_agent
   ├─ run_industry_agent
   └─ run_audit_agent
  ↓
aggregate_agent_outputs
  ↓
route_conflict_level
   ├─ 分歧低 → run_synthesis_agent
   └─ 分歧高 → run_conflict_review_agent
                         ↓
                   run_synthesis_agent
  ↓
generate_markdown_report
  ↓
generate_html_report
  ↓
persist_report
  ↓
END
```

如果后面要加“数据验证 Agent”“复核 Agent”“估值 Agent”，这套结构也能自然扩展。

---

## 七、节点逐一设计

以下是建议的节点职责拆解。

### 7.1 `load_analysis_input`

职责：

1. 读取任务基础输入
2. 加载 `analysis_id`、`user_id`、公司名称、股票代码、配置模型信息
3. 初始化 graph state

输入：

1. `analysis_id`
2. `user_id`
3. 请求参数

输出：

1. `company_name`
2. `stock_code`
3. `api_config`
4. 初始化后的 `GraphState`

适合做节点的原因：

1. 是整个图的统一入口
2. 如果任务不存在或参数异常，可在最早阶段失败

### 7.2 `collect_company_data`

职责：

1. 调用数据采集模块
2. 获取公司基础资料、财务数据、行业数据
3. 将原始数据放入 state

输出建议：

1. `company_data_raw`
2. `industry_data_raw`
3. `data_sources`
4. `data_collection_errors`

说明：

当前仓库这里还是 mock 逻辑，因此这一步未来会是关键节点。

### 7.3 `validate_collected_data`

职责：

1. 验证关键字段是否齐全
2. 判断是否满足最小分析要求
3. 产出数据质量标签

输出建议：

1. `data_quality_score`
2. `missing_fields`
3. `is_data_sufficient`

为什么建议单独拆节点：

1. 这样才能在图里做清晰路由
2. 便于未来插入“补采数据”路径

### 7.4 `route_data_quality`

职责：

1. 根据 `is_data_sufficient` 决定下一步走向

路由逻辑：

1. 数据足够：进入 `calculate_financial_ratios`
2. 数据不足：进入 `enrich_missing_data`

这是典型的 LangGraph 路由节点。

### 7.5 `enrich_missing_data`

职责：

1. 针对缺失项做二次补采
2. 可调用补充搜索、附加数据源或用户默认模型进行信息补全

输出建议：

1. `enriched_fields`
2. `remaining_missing_fields`

### 7.6 `calculate_financial_ratios`

职责：

1. 基于财务数据计算财务比率
2. 形成结构化财务分析输入

输出建议：

1. `financial_ratios`
2. `ratio_calculation_status`

### 7.7 `build_analysis_context`

职责：

1. 整合公司信息、财务数据、行业数据、比率和来源
2. 生成统一分析上下文
3. 为所有角色 Agent 提供一致输入

输出建议：

1. `agent_context`

设计重点：

1. 这是未来图里的核心共享状态节点
2. 后续所有 Agent 尽量只依赖 `agent_context`

### 7.8 `fanout_agents`

职责：

1. 将统一上下文分发给三个角色 Agent
2. 在图语义上表达“并发扇出”

说明：

这一步本身可以是一个逻辑节点，也可以由 LangGraph 的边直接表示并发展开。

### 7.9 `run_munger_agent`

职责：

1. 生成芒格视角结论
2. 输出结构化评分、观点、风险和证据

输出建议：

1. `munger_result`
2. `munger_status`
3. `munger_latency_ms`

### 7.10 `run_industry_agent`

职责：

1. 生成产业专家视角结论
2. 输出产业格局、供需、周期、成本曲线判断

输出建议：

1. `industry_result`
2. `industry_status`
3. `industry_latency_ms`

### 7.11 `run_audit_agent`

职责：

1. 生成审计视角结论
2. 输出现金流、资产质量、红旗信号和财务质检结果

输出建议：

1. `audit_result`
2. `audit_status`
3. `audit_latency_ms`

### 7.12 `aggregate_agent_outputs`

职责：

1. 聚合三个角色 Agent 的结构化输出
2. 计算角色是否齐全
3. 形成汇总 Agent 的输入对象
4. 评估分歧程度

输出建议：

1. `agent_bundle`
2. `completed_roles`
3. `failed_roles`
4. `conflict_level`

为什么值得单独成节点：

1. 聚合和汇总不是一回事
2. 这里可以做统一降级逻辑
3. 这里适合引出“高分歧复核”的条件分支

### 7.13 `route_conflict_level`

职责：

1. 判断是否需要复核

路由建议：

1. `low` / `medium`：直接去 `run_synthesis_agent`
2. `high`：先去 `run_conflict_review_agent`

### 7.14 `run_conflict_review_agent`

职责：

1. 对三方分歧较大的主题做一次补充分析
2. 可以要求模型输出“冲突原因”和“哪一方更可信”

这是未来的增强节点，MVP 不一定需要。

### 7.15 `run_synthesis_agent`

职责：

1. 汇总共识点
2. 汇总分歧点
3. 给出最终评分
4. 给出投资决定
5. 生成最终报告结构素材

输出建议：

1. `synthesis_result`
2. `final_score`
3. `investment_decision`

### 7.16 `generate_markdown_report`

职责：

1. 根据 `synthesis_result` 和三角色结果生成 Markdown 内容

输出建议：

1. `report_markdown`

### 7.17 `generate_html_report`

职责：

1. 根据 Markdown 或结构化数据生成 HTML 报告
2. 编排图表和报告布局

输出建议：

1. `report_html`

### 7.18 `persist_report`

职责：

1. 保存最终报告
2. 保存中间 Agent 输出
3. 更新分析任务状态

输出建议：

1. `persisted_report_id`
2. `analysis_status = completed`

---

## 八、Graph State 设计建议

未来迁移到 LangGraph 时，建议统一使用一个 `GraphState`，避免节点之间传零散变量。

建议状态结构如下：

```python
class GraphState(TypedDict, total=False):
    analysis_id: str
    user_id: str
    company_name: str
    stock_code: str
    include_charts: bool
    api_config: dict

    company_data_raw: dict
    industry_data_raw: dict
    financial_ratios: dict
    data_sources: list
    missing_fields: list[str]
    data_quality_score: float
    is_data_sufficient: bool

    agent_context: dict

    munger_result: dict
    industry_result: dict
    audit_result: dict
    agent_bundle: dict
    conflict_level: str

    synthesis_result: dict
    final_score: float
    investment_decision: str

    report_markdown: str
    report_html: str

    current_step: str
    errors: list[dict]
```
```

设计原则：

1. 共享状态尽量扁平
2. 节点只读自己所需，写自己负责的字段
3. 中间错误和缺失信息也进入 state，便于追踪

---

## 九、建议的第一版 LangGraph 路由规则

### 9.1 数据质量路由

```text
if is_data_sufficient:
    -> calculate_financial_ratios
else:
    -> enrich_missing_data
```

### 9.2 Agent 结果完整性路由

```text
if failed_roles is empty:
    -> run_synthesis_agent
else:
    -> run_synthesis_agent with degraded mode
```

说明：

即使有某个角色失败，也不一定要整个任务失败，可以带着降级标记继续出报告。

### 9.3 分歧程度路由

```text
if conflict_level == "high":
    -> run_conflict_review_agent
else:
    -> run_synthesis_agent
```

---

## 十、失败与恢复设计

这是未来 LangGraph 可能真正产生价值的部分。

### 10.1 节点失败后的建议策略

1. `collect_company_data` 失败
   - 可重试一次
   - 仍失败则进入 `failed`
2. 单个角色 Agent 失败
   - 记录错误
   - 允许继续聚合与汇总
3. `run_synthesis_agent` 失败
   - 可以回退到模板化汇总报告
4. `generate_html_report` 失败
   - 至少保留 Markdown 报告

### 10.2 可恢复点建议

建议将以下节点结果持久化，便于断点恢复：

1. `build_analysis_context`
2. `run_munger_agent`
3. `run_industry_agent`
4. `run_audit_agent`
5. `run_synthesis_agent`

因为这些节点往往最耗时、最贵。

---

## 十一、与当前代码结构的映射建议

当前仓库中已有：

1. `backend/app/services/analysis.py`
2. `backend/app/services/llm_service.py`
3. `backend/app/services/report_generator.py`

未来迁移到 LangGraph 时，建议映射为：

### 保留为普通服务层

1. `llm_service.py`
   - 继续作为底层模型调用封装
2. `report_generator.py`
   - 继续负责 Markdown / HTML 真正生成细节
3. `data_collector.py`
   - 继续负责数据采集细节

### 迁移为图节点入口层

1. `analysis.py`
   - 从“大而全流程函数”改为：
   - 初始化图状态
   - 调用 graph 执行
   - 接收图结果并入库

### 新增目录建议

```text
backend/app/services/graph/
├── state.py
├── nodes/
│   ├── load_input.py
│   ├── collect_data.py
│   ├── validate_data.py
│   ├── calculate_ratios.py
│   ├── build_context.py
│   ├── run_munger.py
│   ├── run_industry.py
│   ├── run_audit.py
│   ├── aggregate_outputs.py
│   ├── run_synthesis.py
│   ├── generate_markdown.py
│   ├── generate_html.py
│   └── persist_report.py
├── routers.py
└── workflow.py
```

说明：

1. `workflow.py` 负责定义 graph
2. `routers.py` 负责条件分支
3. `state.py` 统一定义状态对象
4. `nodes/` 每个文件只做一个节点职责

---

## 十二、迁移顺序建议

为了避免一次性重构过大，建议分三步迁移。

### 第一步：先做“LangGraph-ready”代码结构

即使还不上 LangGraph，也先做到：

1. 每个 Agent 都有独立 `run()` 接口
2. 上下文统一为 `AgentContext`
3. 中间结果统一结构化
4. 状态字段统一命名

### 第二步：将线性 orchestrator 映射为 graph 节点

先只迁移最简单线性图：

1. 不做复杂条件路由
2. 不做复核节点
3. 不做多轮辩论

### 第三步：逐步启用高级能力

后续再增加：

1. 数据质量路由
2. 高分歧复核节点
3. 降级与恢复逻辑
4. 多轮辩论节点

---

## 十三、最终建议

### 建议结论

如果未来迁移到 LangGraph，节点拆分应遵循：

1. 数据准备节点
2. 数据校验与路由节点
3. 角色 Agent 节点
4. 聚合与冲突判断节点
5. 汇总裁决节点
6. 报告生成节点
7. 持久化节点

其中最关键的设计不是“节点越细越好”，而是：

1. 节点边界清晰
2. 状态对象统一
3. 条件路由明确
4. 失败后能恢复或降级

### 对当前项目的实际建议

当前建议先不要立刻落 LangGraph，但从现在开始就按“将来可迁移”的方式设计多 Agent 模块。这样以后真正切图编排时，只需要替换编排层，而不需要重写 Agent 本身。
