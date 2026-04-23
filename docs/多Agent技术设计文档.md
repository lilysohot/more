# 多 Agent 技术设计文档

**文档版本**：v1.1  
**编写日期**：2026-04-23  
**最近审定日期**：2026-04-23

---

## 一、设计目标

本文档定义“三 Agent 深度辩论 + 汇总 Agent”方案的技术落地方式，重点覆盖：

1. 模块拆分
2. 数据结构
3. 接口设计
4. 状态机设计
5. 存储设计
6. 错误处理
7. 演进路线

新增说明：

1. 本文档用于指导 MVP 到产品化阶段的工程落地
2. 本文档默认“结构化输出稳定性”优先于“自由生成表现力”
3. 本文档默认“任务可恢复、可观测、可降级”优先于“复杂多轮协作”

---

## 二、推荐目录结构

```text
backend/app/services/
├── analysis.py
├── llm_service.py
├── report_generator.py
└── agents/
    ├── __init__.py
    ├── base.py
    ├── schemas.py
    ├── munger_agent.py
    ├── industry_agent.py
    ├── audit_agent.py
    ├── synthesis_agent.py
    └── orchestrator.py
```

如进入产品化阶段，可进一步补充：

```text
backend/app/
├── models/
│   └── agent_run.py
├── services/
│   └── agents/
│       ├── prompt_templates/
│       └── parser.py
└── schemas/
    └── agent.py
```

说明：

1. `orchestrator.py` 负责统一编排四个 Agent
2. `schemas.py` 负责输入输出数据模型
3. 各角色 Agent 专注于单一角色逻辑
4. `analysis.py` 只保留任务入口、状态更新和数据库持久化职责
5. 如后续引入更多 Agent，保持“一角色一职责”，不要让单个 Agent 再次演化成多角色混合 Prompt

---

## 三、模块职责设计

### 3.1 `analysis.py`

职责：

1. 接收分析任务参数
2. 拉取或生成基础数据上下文
3. 调用 `AgentOrchestrator`
4. 接收最终结果并调用报告生成器
5. 写入数据库和任务状态

新增要求：

1. 不再直接承载复杂 Prompt 拼装逻辑
2. 不再直接解析多 Agent 输出
3. 只负责流程推进、状态更新和异常兜底

### 3.2 `base.py`

职责：

1. 定义 Agent 基类
2. 封装统一的 LLM 调用入口
3. 定义 prompt 渲染与输出解析协议
4. 提供日志、耗时、异常包装能力
5. 提供结构化解析校验与有限重试能力

建议接口：

```python
class BaseAgent:
    role_name: str
    prompt_version: str
    schema_version: str

    async def run(self, context: AgentContext) -> AgentResult:
        ...

    def build_prompt(self, context: AgentContext) -> str:
        ...

    def parse_response(self, raw_text: str) -> AgentResult:
        ...
```

建议 `run()` 的标准流程：

1. 构建 Prompt
2. 调用 LLM
3. 记录原始输出
4. 执行 JSON 解析和 schema 校验
5. 失败时执行一次有限修复重试
6. 返回结构化结果或抛出可识别异常

### 3.3 三个角色 Agent

#### `munger_agent.py`

关注：

1. 企业本质
2. 护城河
3. 管理层质量
4. 资本配置
5. 估值安全边际

#### `industry_agent.py`

关注：

1. 产业链位置
2. 行业周期
3. 供需格局
4. 成本曲线
5. 竞争结构

#### `audit_agent.py`

关注：

1. 收入与利润真实性
2. 现金流质量
3. 资产质量
4. 会计异常
5. 关联交易与红旗信号

角色边界要求：

1. 各角色可以引用同一份数据，但不能无限跨界分析
2. 角色必须输出自己的 `questions` 和 `red_flags`
3. 角色必须显示标注“不足以判断”的场景

### 3.4 `synthesis_agent.py`

职责：

1. 汇总三方结论
2. 抽取共识点
3. 标注分歧点
4. 形成统一结论
5. 产出最终报告结构素材

新增要求：

1. 不应只做拼接，应做归纳和裁决
2. 必须识别角色失败或数据不足场景
3. 必须给出 `insufficient_data` 标记
4. 必须遵守既定裁决规则，而不是完全自由生成

### 3.5 `orchestrator.py`

职责：

1. 调度三个角色 Agent
2. 处理串行或并发执行
3. 整理中间结果
4. 调用汇总 Agent
5. 返回统一最终结果

建议接口：

```python
class AgentOrchestrator:
    async def run(self, context: AgentContext) -> SynthesisResult:
        ...
```

建议增加以下能力：

1. 记录每个 Agent 的开始时间、结束时间、耗时和状态
2. 保存结构化结果和原始输出
3. 支持角色失败后的降级策略
4. 支持仅重跑 `synthesis_agent`

---

## 四、数据模型设计

### 4.1 基础上下文 `AgentContext`

```json
{
  "analysis_id": "uuid",
  "company_name": "特变电工",
  "stock_code": "600089",
  "basic_profile": {
    "industry": "电力设备",
    "exchange": "SH"
  },
  "financial_data": {
    "revenue": 0,
    "net_profit": 0,
    "gross_margin": 0.0,
    "roe": 0.0,
    "asset_liability_ratio": 0.0,
    "operating_cash_flow": 0
  },
  "financial_ratios": {
    "gross_margin": 0.0,
    "net_margin": 0.0,
    "roe": 0.0,
    "roa": 0.0,
    "current_ratio": 0.0
  },
  "industry_data": {
    "market_size": "",
    "competition": "",
    "trend": ""
  },
  "sources": [
    {
      "name": "2025 年报",
      "type": "official",
      "date": "2025-12-31"
    }
  ],
  "data_quality": {
    "is_mock": false,
    "missing_fields": [],
    "quality_note": ""
  }
}
```

建议补充字段：

1. `data_quality.is_mock` 用于标识是否仍基于 mock 数据
2. `missing_fields` 用于帮助 Agent 明确哪些信息缺失
3. `sources` 应尽量附带日期和类型，便于回溯

### 4.2 角色输出 `AgentResult`

```json
{
  "role": "audit",
  "summary": "一句话总结",
  "score": 6.8,
  "thesis": ["观点1", "观点2"],
  "positives": ["优势1"],
  "risks": ["风险1"],
  "evidence": [
    {
      "item": "经营现金流与净利润背离",
      "source": "2025 年报",
      "source_type": "official",
      "source_date": "2025-12-31",
      "excerpt": "经营活动现金流净额明显低于净利润",
      "confidence": 0.9
    }
  ],
  "red_flags": ["存货增速异常"],
  "questions": ["应收账款增长是否来自渠道压货"],
  "insufficient_data": false
}
```

建议约束：

1. `score` 范围统一为 `0-10`
2. `evidence` 至少 1 条，若无足够证据则必须设置 `insufficient_data=true`
3. `questions` 在数据不足场景下必须非空

### 4.3 汇总输出 `SynthesisResult`

```json
{
  "company_profile": "披着成长外衣的强周期制造公司",
  "consensus": ["公司具备规模优势"],
  "disagreements": [
    {
      "topic": "盈利持续性",
      "munger": "中性",
      "industry": "乐观",
      "audit": "谨慎"
    }
  ],
  "final_score": 7.1,
  "investment_decision": "持有",
  "insufficient_data": false,
  "core_reasons": ["具备产业链地位", "财务质量仍需观察"],
  "major_risks": ["周期反转", "现金流承压"],
  "report_sections": {
    "intro": "...",
    "munger_view": "...",
    "industry_view": "...",
    "audit_view": "...",
    "synthesis": "..."
  }
}
```

### 4.4 汇总裁决规则建议

建议不要把最终裁决完全交给自由生成，至少定义半结构化规则：

1. `final_score` 可由三角色分数按权重计算后，再允许汇总 Agent 做有限修正
2. 如 `audit_agent.red_flags` 达到阈值，则 `investment_decision` 不得高于预设上限
3. 如超过一个角色 `insufficient_data=true`，则汇总结果也必须标记 `insufficient_data=true`
4. 如只有两个角色成功，汇总 Agent 允许继续输出，但需在报告中声明视角缺失

### 4.5 版本化要求

所有结构化结果建议携带以下运行元信息：

1. `prompt_version`
2. `schema_version`
3. `model_provider`
4. `model_name`
5. `generated_at`

---

## 五、状态机设计

### 5.1 状态分层建议

建议区分两层状态，而不是把所有阶段都直接塞进 `Analysis.status`：

1. 业务状态 `status`
   - `pending`
   - `running`
   - `completed`
   - `failed`
2. 细粒度阶段 `progress_stage`
   - `collecting_data`
   - `calculating_ratios`
   - `building_context`
   - `running_munger_agent`
   - `running_industry_agent`
   - `running_audit_agent`
   - `running_synthesis_agent`
   - `generating_report`
   - `saving_report`

这样做的原因：

1. 历史列表页只需关注粗状态
2. 进度页才需要细粒度阶段
3. 后续扩展阶段时，对现有前端兼容性更好

### 5.2 前端进度提示文案

建议前端进度提示文案：

1. 正在采集财务与行业数据
2. 正在计算财务比率
3. 正在构建分析上下文
4. 芒格视角正在评估
5. 产业专家正在评估
6. 审计专家正在评估
7. 正在汇总三方观点
8. 正在生成最终报告
9. 正在保存分析结果

### 5.3 阶段进度映射建议

建议将进度条映射改为基于 `progress_stage`，而不是完全依赖 `status`：

1. `pending`: 0
2. `collecting_data`: 10
3. `calculating_ratios`: 20
4. `building_context`: 30
5. `running_munger_agent`: 45
6. `running_industry_agent`: 55
7. `running_audit_agent`: 65
8. `running_synthesis_agent`: 80
9. `generating_report`: 90
10. `saving_report`: 95
11. `completed`: 100

---

## 六、数据库与持久化建议

### 6.1 最小持久化方案

当前最小方案无需立刻重构现有报告表，可先：

1. 将最终 Markdown/HTML 继续写入现有 `reports` 表
2. 将三角色和汇总结果序列化为 JSON 存入新增字段或单独表

### 6.2 推荐新增表：`agent_runs`

字段建议：

1. `id`
2. `analysis_id`
3. `role`
4. `status`
5. `prompt_version`
6. `schema_version`
7. `model_provider`
8. `model_name`
9. `score`
10. `input_context_json`
11. `raw_output`
12. `structured_output_json`
13. `parse_status`
14. `token_usage_input`
15. `token_usage_output`
16. `latency_ms`
17. `error_message`
18. `started_at`
19. `completed_at`

用途：

1. 便于排查某个角色失败原因
2. 便于后续前端展示原始分角色结果
3. 便于监控耗时、Token 使用和质量
4. 便于比较 Prompt 或模型变更前后的效果

### 6.3 JSON 字段建议

若底层数据库支持 JSONB，建议优先使用 JSONB 存储：

1. `input_context_json`
2. `structured_output_json`

理由：

1. 便于后续查询字段
2. 便于统计错误类型和输出质量
3. 便于内部审阅和调试工具接入

---

## 七、接口设计建议

### 7.1 现有接口可保持不变

继续使用：

1. `POST /api/v1/analyses`
2. `GET /api/v1/analyses/{analysis_id}/progress`
3. `GET /api/v1/analyses/{analysis_id}/report`

### 7.2 现有接口建议扩展字段

`GET /api/v1/analyses/{analysis_id}/progress` 建议返回：

```json
{
  "analysis_id": "uuid",
  "status": "running",
  "progress_stage": "running_industry_agent",
  "progress": 55,
  "message": "产业专家正在评估"
}
```

### 7.3 可新增接口

#### 查询分角色结果

`GET /api/v1/analyses/{analysis_id}/agents`

响应示例：

```json
{
  "munger": { "score": 7.6, "summary": "...", "status": "completed" },
  "industry": { "score": 8.0, "summary": "...", "status": "completed" },
  "audit": { "score": 6.5, "summary": "...", "status": "completed" },
  "synthesis": { "final_score": 7.2, "investment_decision": "持有", "status": "completed" }
}
```

#### 查询原始中间结果

`GET /api/v1/analyses/{analysis_id}/agents/{role}`

说明：用于调试或内部审阅，不一定对普通用户开放。

#### 重试汇总阶段

`POST /api/v1/analyses/{analysis_id}/agents/synthesis/retry`

说明：用于在角色输出已完成时单独重跑汇总阶段，避免整单重跑。

---

## 八、错误处理与降级策略

### 8.1 单个角色失败

策略：

1. 标记该角色为失败
2. 汇总 Agent 使用剩余结果继续生成
3. 在最终报告中标注该视角缺失
4. 保留失败原因、原始响应和阶段耗时

### 8.2 汇总 Agent 失败

策略：

1. 将三角色结果直接模板化输出为临时报告
2. 标记结果为“未完成高级汇总”
3. 支持重试汇总阶段

### 8.3 数据不足

策略：

1. 允许 Agent 输出“不足以判断”
2. 强制填充 `questions` 字段
3. 在最终报告中加入“数据不足提示”
4. 将 `insufficient_data` 标记向上透传到汇总结果

### 8.4 结构化解析失败

策略：

1. 首次解析失败后，执行一次修复型重试
2. 若仍失败，则将该角色标记为 `parse_failed`
3. 原始文本必须保留，供后续排查
4. 汇总 Agent 仅消费成功解析的结果

---

## 九、性能与成本建议

### 9.1 调用策略

MVP 建议：

1. 三角色串行
2. 汇总最后执行

增强版建议：

1. 三角色并发
2. 汇总串行

### 9.2 成本控制

1. 统一裁剪上下文长度
2. 限制每个 Agent 返回字段长度
3. 将长文本转为结构化要点
4. 对中间结果做缓存
5. 汇总 Agent 仅消费摘要化结构数据，不重复灌入整段长文

### 9.3 观测指标建议

建议至少记录以下指标：

1. 每个 Agent 的耗时
2. 每个 Agent 的解析成功率
3. 每个 Agent 的失败率
4. 单次分析总耗时
5. 各模型 Token 使用量

---

## 十、前端呈现建议

报告页可新增：

1. 三角色评分卡片
2. 共识点区域
3. 分歧点区域
4. 最终裁决区
5. 风险提示区
6. 数据质量提示区

推荐结构：

```text
报告概览
├── 一句话公司本质
├── 最终评分与投资决定
├── 三角色评分对比
├── 三维深度辩论
│   ├── 芒格视角
│   ├── 产业专家视角
│   └── 审计专家视角
├── 共识点
├── 分歧点
├── 风险提示
├── 数据质量提示
└── 数据来源汇总
```

新增建议：

1. 若存在角色失败，应明确展示“该视角缺失”
2. 若存在 `insufficient_data=true`，应展示显式提示，不要只隐藏在正文里

---

## 十一、实施建议

建议按以下顺序推进：

1. 先做结构化 Schema 和解析约束
2. 再做 Agent 基类和编排器
3. 再补 `agent_runs` 级别的持久化记录
4. 再接到现有 `AnalysisService`
5. 再升级 `ReportGenerator`
6. 最后升级前端报告页展示

不建议的顺序：

1. 先堆叠更多 Agent
2. 先做复杂多轮辩论
3. 先做花哨前端展示，再补后端可靠性

---

## 十二、验收标准

1. 用户提交分析任务后，可成功生成四阶段结果
2. 三个角色输出可被结构化解析
3. 汇总 Agent 可生成统一结论
4. 最终 Markdown 和 HTML 报告包含分角色内容
5. 失败时有清晰状态和错误信息
6. 可在历史记录中查看最终报告
7. 能查看每个 Agent 的独立执行结果和失败信息
8. 汇总阶段可单独重试
9. 数据不足时系统能显式降级，而不是静默生成强结论
