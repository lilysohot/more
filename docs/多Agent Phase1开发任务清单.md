# 多 Agent Phase 1 开发任务清单

**文档版本**：v1.0  
**编写日期**：2026-04-23  
**适用阶段**：Phase 1 / 工作流 MVP

---

## 一、目标

本清单用于把 `docs/多Agent实施清单.md` 中的 `Phase 1` 进一步拆成可执行的开发任务。

本阶段目标：

1. 跑通 `3 个角色 Agent + 1 个汇总 Agent` 的完整后端链路
2. 让 Agent 输出进入稳定的结构化解析流程
3. 基于结构化结果生成 Markdown / HTML 报告
4. 让每个 Agent 的运行状态、原始输出和错误信息可追踪

本阶段不追求：

1. 高准确率投资结论
2. 多轮互相反驳
3. 并发执行优化
4. 复杂工作流引擎

---

## 二、实施顺序

建议按以下顺序推进：

1. 先定义结构和约束
2. 再实现 Agent 基类和编排器
3. 再把编排器接入现有分析主流程
4. 再落运行记录和降级策略
5. 最后改造报告生成器

依赖关系：

```text
Schema 定义
    ↓
BaseAgent
    ↓
角色 Agent / 汇总 Agent
    ↓
Orchestrator
    ↓
AnalysisService 接入
    ↓
agent_runs 持久化
    ↓
ReportGenerator 结构化编排
```

---

## 三、开发任务列表

### 任务 1：定义多 Agent 核心 Schema

**目标**

定义 `AgentContext`、`AgentResult`、`SynthesisResult` 以及配套枚举或校验规则，作为全链路的统一契约。

**交付物**

1. `backend/app/services/agents/schemas.py`
2. 如需要，可补充 `backend/app/schemas/agent.py`

**建议内容**

1. `AgentContext`
2. `AgentResult`
3. `SynthesisResult`
4. `AgentRole` 枚举
5. `AgentRunStatus` 枚举
6. `progress_stage` 枚举或常量

**验收标准**

1. 三类核心结构字段与文档保持一致
2. `score`、`insufficient_data`、`evidence` 等关键字段有明确约束
3. 汇总结果能容纳共识、分歧、裁决和报告片段

**验证方式**

1. 代码审查确认结构与文档一致
2. 能用样例数据成功实例化结构模型

**依赖**

1. 无

**预估范围**

1. Small

---

### 任务 2：实现 `BaseAgent` 和统一解析流程

**目标**

建立所有 Agent 共用的最小执行框架，统一处理 Prompt 构建、LLM 调用、JSON 解析、schema 校验和有限重试。

**交付物**

1. `backend/app/services/agents/base.py`
2. 如需要，可增加 `backend/app/services/agents/parser.py`

**建议内容**

1. `build_prompt()` 抽象方法
2. `parse_response()` 抽象方法
3. `run()` 统一执行流程
4. 解析失败时的一次修复型重试
5. 返回统一的结构化结果或抛出可识别异常

**验收标准**

1. `BaseAgent` 可被角色 Agent 继承
2. 原始响应和解析错误可被捕获
3. 解析失败有明确异常类型，不是静默失败

**验证方式**

1. 使用 mock LLM 输出测试 JSON 解析成功路径
2. 使用非法输出测试解析失败和重试路径

**依赖**

1. 任务 1

**预估范围**

1. Medium

---

### 任务 3：拆分 3 个角色 Agent

**目标**

把现有单次三维分析 Prompt 拆成三个单职责角色 Agent。

**交付物**

1. `backend/app/services/agents/munger_agent.py`
2. `backend/app/services/agents/industry_agent.py`
3. `backend/app/services/agents/audit_agent.py`

**建议内容**

1. 每个 Agent 拥有独立 Prompt 模板
2. 每个 Agent 明确边界和输出字段
3. 每个 Agent 都输出 `questions`、`red_flags`、`insufficient_data`

**验收标准**

1. 三个 Agent 都能基于同一 `AgentContext` 运行
2. 三个 Agent 都能输出符合 Schema 的结构化结果
3. 三个 Agent 的 Prompt 职责边界清晰

**验证方式**

1. 用同一组样例上下文分别执行三个 Agent
2. 检查输出结构是否都能通过 schema 校验

**依赖**

1. 任务 1
2. 任务 2

**预估范围**

1. Medium

---

### 任务 4：实现 `synthesis_agent`

**目标**

让汇总 Agent 基于三个角色的结构化结果，输出共识、分歧、最终评分和报告素材。

**交付物**

1. `backend/app/services/agents/synthesis_agent.py`

**建议内容**

1. 输入为角色 Agent 的结构化结果集合
2. 输出 `SynthesisResult`
3. 处理角色缺失、解析失败和数据不足场景
4. 明确 `insufficient_data` 透传逻辑

**验收标准**

1. 汇总 Agent 不直接依赖长文本拼接
2. 若单个角色缺失，仍能输出降级版汇总结论
3. 输出字段可直接被报告生成器消费

**验证方式**

1. 使用完整三角色输入测试正常路径
2. 使用缺少一个角色的输入测试降级路径

**依赖**

1. 任务 1
2. 任务 2
3. 任务 3

**预估范围**

1. Medium

---

### 任务 5：实现 `AgentOrchestrator`

**目标**

统一调度三个角色 Agent 和一个汇总 Agent，形成标准执行链路。

**交付物**

1. `backend/app/services/agents/orchestrator.py`

**建议内容**

1. 串行执行三个角色 Agent
2. 汇总角色结果
3. 调用 `synthesis_agent`
4. 返回统一结果对象
5. 标准化阶段状态推进

**验收标准**

1. 编排器能跑通完整链路
2. 能处理角色失败并继续降级执行
3. 返回结果可直接交给报告生成器

**验证方式**

1. 使用 mock Agent 或 stub 输出跑通编排器
2. 模拟单角色异常，验证降级逻辑

**依赖**

1. 任务 3
2. 任务 4

**预估范围**

1. Medium

---

### 任务 6：改造 `LLMService` 以支持多 Agent 调用

**目标**

让现有 `LLMService` 从“单次三维合一分析入口”变成可复用的底层 LLM 调用组件。

**交付物**

1. `backend/app/services/llm_service.py`

**建议内容**

1. 提供更通用的 `prompt -> text` 调用能力
2. 去掉强耦合单一投资分析模板的职责
3. 保留不同 provider 的统一调用封装

**验收标准**

1. Agent 层可直接复用 `LLMService`
2. `LLMService` 不再内置唯一的三维合一业务模板
3. 不影响现有 provider 配置读取逻辑

**验证方式**

1. 用简单 prompt 调用各 provider 适配路径
2. 代码审查确认业务 Prompt 已迁移到 Agent 层

**依赖**

1. 任务 2

**预估范围**

1. Small

---

### 任务 7：在 `AnalysisService` 中接入多 Agent 主流程

**目标**

把现有 `run_analysis()` 从“单次 LLM 分析”改为“构建上下文 -> 编排多 Agent -> 生成报告”。

**交付物**

1. `backend/app/services/analysis.py`

**建议内容**

1. 组装 `AgentContext`
2. 调用 `AgentOrchestrator`
3. 更新 `progress_stage`
4. 接收汇总结果并进入报告生成
5. 统一处理异常和失败状态

**验收标准**

1. `run_analysis()` 不再直接依赖单次三维分析返回长文本
2. 状态推进覆盖 `building_context`、角色执行、汇总、报告生成
3. 失败时仍能留下足够错误信息

**验证方式**

1. 发起一次本地分析任务，确认链路可执行
2. 检查状态变化是否符合文档设计

**依赖**

1. 任务 5
2. 任务 6

**预估范围**

1. Medium

---

### 任务 8：补充 `agent_runs` 持久化记录

**目标**

为每个 Agent 的运行结果建立独立记录，支撑调试、审计和后续产品化展示。

**交付物**

1. `backend/app/models/` 中新增模型
2. 如需要，同步更新 Alembic migration
3. `analysis.py` 或 `orchestrator.py` 中接入写入逻辑

**建议字段**

1. `analysis_id`
2. `role`
3. `status`
4. `prompt_version`
5. `schema_version`
6. `model_provider`
7. `model_name`
8. `raw_output`
9. `structured_output_json`
10. `error_message`
11. `latency_ms`
12. `started_at`
13. `completed_at`

**验收标准**

1. 每个 Agent 执行后都有独立记录
2. 成功和失败路径都能落记录
3. 原始输出与结构化输出都能追溯

**验证方式**

1. 执行一次完整分析，检查 4 条运行记录
2. 制造一次失败，检查失败记录是否完整

**依赖**

1. 任务 5
2. 任务 7

**预估范围**

1. Medium

---

### 任务 9：改造 `ReportGenerator` 以消费结构化结果

**目标**

把报告生成器从“嵌入单次分析文本”改成“基于三角色和汇总结果编排报告”。

**交付物**

1. `backend/app/services/report_generator.py`

**建议内容**

1. 输入改为结构化结果集合
2. Markdown 报告展示三角色摘要和汇总结论
3. HTML 报告展示关键块位
4. 展示数据不足提示和角色缺失提示

**验收标准**

1. 报告不再只是插入整段原始文本
2. Markdown / HTML 都包含三角色和汇总部分
3. 缺失角色时报告仍可生成

**验证方式**

1. 用完整结构化结果生成 Markdown / HTML
2. 用缺失一个角色的结构化结果测试降级报告

**依赖**

1. 任务 4
2. 任务 7

**预估范围**

1. Medium

---

### 任务 10：补充最小接口和进度兼容改造

**目标**

在不进入完整 Phase 2 的前提下，让 Phase 1 至少具备可用的进度和结果读取能力。

**交付物**

1. `backend/app/api/analyses.py`
2. 如需要，同步修改 `backend/app/schemas/analysis.py`

**建议内容**

1. 在 progress 响应中增加 `progress_stage`
2. 调整进度百分比映射以覆盖多 Agent 阶段
3. 保持现有 `report` 接口兼容

**验收标准**

1. 前端轮询不会因新增阶段而失效
2. 用户能看到更细粒度的分析阶段
3. 现有报告读取接口保持可用

**验证方式**

1. 手动轮询 progress 接口查看阶段变化
2. 完成任务后确认报告接口仍返回正常内容

**依赖**

1. 任务 7
2. 任务 9

**预估范围**

1. Small

---

## 四、建议检查点

### 检查点 A：完成任务 1-3 后

应确认：

1. Schema 稳定
2. `BaseAgent` 执行框架可复用
3. 三个角色 Agent 都能输出可解析 JSON

### 检查点 B：完成任务 4-7 后

应确认：

1. 多 Agent 编排链路已打通
2. `AnalysisService` 已接入新流程
3. 进度状态推进正常

### 检查点 C：完成任务 8-10 后

应确认：

1. 每个 Agent 的运行记录可追踪
2. 报告已基于结构化结果生成
3. 现有接口和前端轮询未被破坏

---

## 五、建议文件触点

Phase 1 高概率涉及以下文件：

1. `backend/app/services/analysis.py`
2. `backend/app/services/llm_service.py`
3. `backend/app/services/report_generator.py`
4. `backend/app/api/analyses.py`
5. `backend/app/schemas/analysis.py`
6. `backend/app/models/user.py` 或新增独立模型文件
7. `backend/app/services/agents/base.py`
8. `backend/app/services/agents/schemas.py`
9. `backend/app/services/agents/munger_agent.py`
10. `backend/app/services/agents/industry_agent.py`
11. `backend/app/services/agents/audit_agent.py`
12. `backend/app/services/agents/synthesis_agent.py`
13. `backend/app/services/agents/orchestrator.py`

---

## 六、Phase 1 完成定义

满足以下条件，可视为 Phase 1 完成：

1. 用户发起分析任务后，后端按多 Agent 流程执行
2. 三个角色和汇总 Agent 至少在主路径下能产出结构化结果
3. 报告生成基于结构化结果，而非单次分析长文本
4. 单个角色失败时系统能降级生成结果
5. 每个 Agent 的原始输出、结构化结果、错误信息可追溯
6. 前端现有分析流程和报告查看不被破坏

---

## 七、建议排期方式

如果按 1 人主开发推进，建议拆成 3 个工作包：

1. 工作包 A：任务 1-3
2. 工作包 B：任务 4-7
3. 工作包 C：任务 8-10

如果按多人并行推进，建议：

1. 一人负责 Schema + BaseAgent
2. 一人负责三个角色 Agent + synthesis Agent
3. 一人负责 `AnalysisService`、持久化和 `ReportGenerator`

前提是先冻结 Schema 契约，再并行开发。
