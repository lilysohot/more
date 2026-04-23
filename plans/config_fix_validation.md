# 配置安全修复验证测试计划

## 修改内容

### 1. 移除硬编码敏感信息
**文件**: `backend/app/core/config.py`

修改内容:
- `DATABASE_URL`: 默认值从完整连接字符串改为空字符串
- `SECRET_KEY`: 默认值从 "your-secret-key-change-in-production" 改为空字符串
- `ENCRYPTION_KEY`: 默认值从 "your-32-byte-encryption-key-here!!!" 改为空字符串
- `DEFAULT_LLM_API_KEY`: 默认值从实际key改为空字符串

### 2. 添加配置校验
新增方法 `_validate_required_secrets()`:
- **DEBUG=true**: 使用不安全默认值时仅输出警告日志
- **DEBUG=false**: 使用不安全默认值时抛出 `ValueError` 拒绝启动

### 3. 更新 .env.example
- 添加详细注释说明哪些是必需配置
- 提供安全密钥生成方法
- 说明生产环境要求

## 测试验证

### 测试用例

#### 测试1: DEBUG=true 模式
```
输入:
  DEBUG=true
  SECRET_KEY=your-secret-key-change-in-production
  ENCRYPTION_KEY=your-32-byte-encryption-key-here!!!
  DATABASE_URL=(空)

预期:
  配置加载成功，仅输出警告日志
  使用 DEBUG 模式下的 fallback DATABASE_URL
```

#### 测试2: DEBUG=false 模式 - 不安全配置
```
输入:
  DEBUG=false
  SECRET_KEY=your-secret-key-change-in-production
  ENCRYPTION_KEY=your-32-byte-encryption-key-here!!!
  DATABASE_URL=(空)

预期:
  抛出 ValueError 异常
  错误信息包含 "配置验证失败"
```

#### 测试3: DEBUG=false 模式 - 安全配置
```
输入:
  DEBUG=false
  SECRET_KEY=<安全的随机密钥(32字节+)>
  ENCRYPTION_KEY=<安全的随机密钥(32字节+)>
  DATABASE_URL=postgresql://user:pass@host:5432/db

预期:
  配置加载成功
```

## 运行测试

```bash
cd backend

# 运行配置验证测试
python test_config_validation.py

# 如果测试通过，可以启动应用测试
uvicorn app.main:app --reload
```

## 验证清单

- [ ] 测试1通过：DEBUG=true 接受不安全默认值
- [ ] 测试2通过：DEBUG=false 拒绝不安全默认值
- [ ] 测试3通过：DEBUG=false 接受安全配置
- [ ] .env.example 已更新，包含详细注释
- [ ] 原有的 .env 文件仍可正常工作
