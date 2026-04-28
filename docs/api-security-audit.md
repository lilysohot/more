# API 安全测试与优化建议清单

生成日期：2026-04-27

## 1. 测试范围

本次按生产最高安全原则，对项目内所有主要 API 对接面做了安全检查。

内部 API 范围：

| 模块 | 路径 | 说明 |
| --- | --- | --- |
| 认证 | `/api/v1/auth/*` | 注册、登录、当前用户、登出 |
| 用户 | `/api/v1/users/*` | 个人资料、历史记录、统计 |
| API 配置 | `/api/v1/api-configs/*` | 用户模型配置、API Key 存储、连接测试 |
| 分析 | `/api/v1/analyses/*` | 创建分析、进度、报告、删除、活跃任务 |

外部 API 对接范围：

| 对接方 | 位置 | 说明 |
| --- | --- | --- |
| Tushare | `backend/skills/tushare_skill.py` | 股票信息、行情、财务数据 |
| EastMoney | `backend/app/services/data_collector.py` | 股票识别、行情、财务摘要 |
| DashScope/OpenAI/Claude | `backend/app/services/llm_service.py` | LLM 调用 |
| 用户自定义 LLM Base URL | `backend/app/api/api_configs.py`、`backend/app/services/llm_service.py` | 用户配置模型地址和连通性测试 |

## 2. 测试方式

执行方式包括：

| 类型 | 内容 |
| --- | --- |
| 代码审查 | 鉴权、授权、输入验证、密钥存储、外部请求、错误处理、前端渲染 |
| 真实接口探测 | 未授权访问、无效 token、弱密码、重复注册、暴力登录、越权访问、SSRF、CORS、安全响应头 |
| 配置检查 | Docker 端口暴露、`.env` 忽略状态、生产默认值、调试配置 |
| 依赖检查 | 前端 `pnpm audit`、后端 `pip check` |

## 3. 实测结果摘要

| 测试项 | 结果 | 结论 |
| --- | --- | --- |
| 未登录访问 `/users/profile` | `403` | 受保护接口有认证保护 |
| 无效 token 访问 `/users/profile` | `401` | token 校验有效 |
| 弱密码注册 | `422` | 密码最小长度校验有效 |
| 重复注册 | `400` | 邮箱唯一性校验有效 |
| 连续错误登录 8 次 | 全部 `401` | 未发现速率限制 |
| API Key 创建后返回 | 只返回掩码 | 明文 API Key 未回显 |
| 跨用户修改 API 配置 | `404` | API 配置越权防护有效 |
| 自定义 `base_url=http://127.0.0.1:8000` | 后端发起请求并返回 `HTTP 404` | SSRF 可触发 |
| 非法 CORS Origin | `400` | CORS 拒绝非法 Origin |
| 安全响应头 | 多项缺失 | 需补强 |
| `/docs` | `200` | OpenAPI 文档公开 |
| 前端依赖审计 | `18 vulnerabilities` | 存在高危依赖漏洞 |
| 后端依赖一致性 | `pip check` 通过 | 未发现依赖冲突 |

## 4. 主要风险发现

### P0 高危：自定义 LLM `base_url` 存在 SSRF 风险

位置：

| 文件 | 行为 |
| --- | --- |
| `backend/app/api/api_configs.py` | `/api-configs/test` 接受用户传入 `base_url` 并由后端请求 |
| `backend/app/services/llm_service.py` | 后台分析时会使用用户配置的 `base_url` 调用 LLM |

实测证据：

| 输入 | 结果 |
| --- | --- |
| `base_url=http://127.0.0.1:8000` | 返回 `连接失败: HTTP 404`，证明后端访问了内部地址 |
| `base_url=http://more_backend:8000` | 返回 `连接失败: HTTP 404`，证明容器内服务名可被探测 |

风险：

| 风险点 | 说明 |
| --- | --- |
| 内网探测 | 攻击者可探测容器网络、内网服务、端口开放情况 |
| 云元数据攻击 | 若部署在云环境，可能探测 metadata endpoint |
| API Key 外发 | 用户配置恶意域名后，后端可能把 API Key 发送到攻击者服务器 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P0 | 禁止任意 `base_url`，改为 provider 白名单域名 |
| P0 | 如必须允许自定义 URL，仅允许 HTTPS |
| P0 | 拒绝 localhost、127.0.0.0/8、10.0.0.0/8、172.16.0.0/12、192.168.0.0/16、169.254.0.0/16、IPv6 loopback/link-local/private 地址 |
| P0 | 解析域名后校验 IP，防 DNS rebinding |
| P0 | `/api-configs/test` 返回通用失败信息，不暴露内部 HTTP 状态和网络错误 |

### P0 高危：调试、数据库、Redis 端口对外暴露

位置：`docker-compose.yml`

实测：

| 服务 | 暴露端口 | 当前绑定 |
| --- | --- | --- |
| backend | `8123` | `0.0.0.0` |
| debugpy | `5678` | `0.0.0.0` |
| Postgres | `5433` | `0.0.0.0` |
| Redis | `6379` | `0.0.0.0` |

风险：

| 风险点 | 说明 |
| --- | --- |
| debugpy RCE | 调试端口暴露可能导致远程代码执行 |
| 数据库暴露 | Postgres 被公网扫描或弱口令攻击 |
| Redis 暴露 | Redis 默认无认证时风险极高 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P0 | 生产环境移除 `5678` 调试端口 |
| P0 | Postgres、Redis 不映射到宿主机，或仅绑定 `127.0.0.1` |
| P0 | Docker Compose 分成 `dev` 和 `prod` profile |
| P1 | Redis 开启密码或仅内网访问 |

### P0 高危：登录和注册缺少速率限制

位置：`backend/app/api/auth.py`

实测：连续 8 次错误登录全部返回 `401`，未触发限流或锁定。

风险：

| 风险点 | 说明 |
| --- | --- |
| 暴力破解 | 可持续尝试密码 |
| 撞库 | 可批量验证泄露凭据 |
| 注册滥用 | 可批量创建账号消耗资源 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P0 | 对 `/auth/login` 增加 IP + 邮箱维度限流 |
| P0 | 对 `/auth/register` 增加 IP 维度限流 |
| P1 | 多次失败后增加指数退避或短期锁定 |
| P1 | 登录失败统一返回相同错误，不暴露账号状态差异 |

### P1 中高危：报告 HTML 渲染存在 XSS 风险

位置：

| 文件 | 行为 |
| --- | --- |
| `frontend/src/pages/Report.tsx` | 使用 `dangerouslySetInnerHTML` 渲染 `report.content_html` |
| `backend/app/services/report_generator.py` | 生成完整 HTML 报告并包含外部 Chart.js 脚本 |

风险：

| 风险点 | 说明 |
| --- | --- |
| LLM 输出污染 | LLM 或外部数据若进入 HTML，可能形成脚本注入 |
| token 窃取 | 当前 token 存在 `localStorage`，XSS 可直接读取 |
| 外部脚本供应链 | HTML 报告引用 CDN 脚本，受第三方供应链影响 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P1 | 前端禁用 `dangerouslySetInnerHTML`，默认只渲染 Markdown |
| P1 | 如果必须预览 HTML，使用 DOMPurify 严格白名单清洗 |
| P1 | HTML 预览放入 sandbox iframe，禁用脚本执行 |
| P1 | 下载版 HTML 不应包含未受控外部脚本 |

### P1 中高危：缺少安全响应头

实测缺失：

| Header | 当前状态 |
| --- | --- |
| `Strict-Transport-Security` | 缺失 |
| `Content-Security-Policy` | 缺失 |
| `X-Content-Type-Options` | 缺失 |
| `X-Frame-Options` | 缺失 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P1 | 增加 CSP，至少限制 `default-src 'self'` |
| P1 | 增加 `X-Content-Type-Options: nosniff` |
| P1 | 增加 `X-Frame-Options: DENY` 或 CSP `frame-ancestors 'none'` |
| P1 | 生产 HTTPS 下增加 HSTS |
| P2 | 增加 `Referrer-Policy` 和 `Permissions-Policy` |

### P1 中高危：Bearer Token 存在 `localStorage`

位置：`frontend/src/utils/request.ts`

风险：

| 风险点 | 说明 |
| --- | --- |
| XSS 放大 | 一旦页面有 XSS，攻击者可直接读取 token |
| 长期有效 | `remember_me` 可延长 token 生命周期到 30 天 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P1 | 改用 `httpOnly + Secure + SameSite` Cookie 存放会话 |
| P1 | 配套 CSRF 防护 |
| P2 | 缩短 access token 生命周期，引入 refresh token 轮换 |
| P2 | 支持服务端 token revoke/黑名单 |

### P1 中高危：生产配置默认值偏开发模式

位置：`docker-compose.yml`、`backend/app/core/config.py`

风险：

| 风险点 | 说明 |
| --- | --- |
| 默认密钥 | Docker Compose 中有默认 `SECRET_KEY` 和 `ENCRYPTION_KEY` 兜底 |
| DEBUG | Docker Compose 默认 `DEBUG=true` |
| 文档公开 | FastAPI `/docs` 默认开放 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P1 | 生产 compose 不提供默认密钥，缺失则启动失败 |
| P1 | 生产 `DEBUG=false` |
| P1 | 生产关闭 `/docs`、`/redoc`、`/openapi.json`，或加管理员鉴权 |

### P2 中危：LLM 请求日志记录完整 Payload

位置：`backend/app/services/llm_service.py`

风险：日志可能包含完整 prompt、公司数据、用户输入、未来可能加入的敏感信息。

建议：

| 优先级 | 建议 |
| --- | --- |
| P2 | 移除完整 payload 日志 |
| P2 | 如需调试，仅记录 provider、model、请求 ID、token 数估计 |
| P2 | 日志中禁止记录 API Key、Authorization header、完整 prompt |

### P2 中危：错误响应暴露内部连接细节

位置：`backend/app/api/api_configs.py`

实测：`/api-configs/test` 会返回 `HTTP 404`、`All connection attempts failed`。

建议：

| 优先级 | 建议 |
| --- | --- |
| P2 | 对用户返回通用错误：`连接失败，请检查服务地址或 API Key` |
| P2 | 内部详细错误只写入安全日志，且脱敏 |

### P2 中危：输入校验边界仍需收紧

位置：`backend/app/schemas/api_config.py`、`backend/app/schemas/analysis.py`

建议：

| 字段 | 建议 |
| --- | --- |
| `provider` | 改成枚举：`dashscope`、`openai`、`claude` |
| `base_url` | 改成受限 HTTPS URL，并做 SSRF 防护 |
| `company_name` | 增加长度上限和字符白名单 |
| `stock_code` | 增加格式校验 |
| `username` | 增加长度和字符限制 |

### P2 中危：依赖存在漏洞

前端审计命令：

```bash
pnpm audit --registry=https://registry.npmjs.org --audit-level high
```

结果：

| 严重程度 | 数量 |
| --- | --- |
| high | 7 |
| moderate | 11 |

涉及包：

| 包 | 风险 |
| --- | --- |
| `shelljs` | Improper Privilege Management |
| `minimatch` | ReDoS |
| `flatted` | Prototype Pollution |
| `picomatch` | ReDoS |

建议：

| 优先级 | 建议 |
| --- | --- |
| P2 | 升级或替换 `updata`，修复 `shelljs` 传递依赖 |
| P2 | 升级 `@typescript-eslint`、`eslint`、`tailwindcss` 相关依赖链 |
| P2 | CI 中固定使用官方 npm registry 做 audit 或配置支持 audit 的私有 registry |

后端检查：

| 命令 | 结果 |
| --- | --- |
| `pip check` | 通过 |
| `pip-audit` | 受 PyPI 连接失败影响未完成 |

建议：

| 优先级 | 建议 |
| --- | --- |
| P2 | 在 CI 中加入 `pip-audit -r requirements.txt` |
| P2 | 为 Python 依赖配置可靠镜像或离线漏洞库 |

## 5. 推荐整改路线

### 第一阶段：上线前必须完成

| 状态 | 项目 |
| --- | --- |
| [ ] | 禁止任意 LLM `base_url`，完成 SSRF 防护 |
| [ ] | 移除生产 debugpy 端口 |
| [ ] | Postgres/Redis 不暴露公网 |
| [ ] | 登录/注册/API 测试接口加限流 |
| [ ] | 关闭生产 `/docs`、`/redoc`、`/openapi.json` |
| [ ] | 生产环境强制 `DEBUG=false` |
| [ ] | 生产环境强制显式设置强随机密钥 |

### 第二阶段：高优先级安全加固

| 状态 | 项目 |
| --- | --- |
| [ ] | 报告 HTML 预览改为安全渲染或 sandbox iframe |
| [ ] | 增加安全响应头 |
| [ ] | token 从 `localStorage` 迁移到 httpOnly Cookie |
| [ ] | 移除 LLM 完整 payload 日志 |
| [ ] | API 错误响应脱敏 |
| [ ] | 修复前端高危依赖 |

### 第三阶段：长期治理

| 状态 | 项目 |
| --- | --- |
| [ ] | 增加安全回归测试：未授权、越权、SSRF、XSS、限流、密钥不回显 |
| [ ] | CI 增加 `pnpm audit`、`pip-audit`、secret scan |
| [ ] | 对外部 API 请求增加出站代理或 egress allowlist |
| [ ] | 增加服务端审计日志，记录安全事件但不记录敏感数据 |
| [ ] | 增加 token revoke、刷新令牌轮换和异常登录检测 |

## 6. 参考测试命令

前端依赖审计：

```bash
pnpm audit --registry=https://registry.npmjs.org --audit-level high
```

后端依赖一致性：

```bash
docker exec more_backend python -m pip check
```

容器端口检查：

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

环境文件是否被 git 忽略：

```bash
git check-ignore -v ".env" "backend/.env"
git ls-files ".env" "backend/.env"
```

## 7. 备注

本文件不包含任何真实 token、API Key 或数据库密码。

当前 `.env` 和 `backend/.env` 已被 `.gitignore` 忽略；仍建议将生产密钥迁移到平台级 Secret Manager 或系统环境变量，避免长期落盘保存。
