# AI 功能配置指南

Stock Screener GUI 支持多种大语言模型（LLM）提供商，您可以根据需求选择不同的 AI 服务。

---

## 🤖 支持的 LLM 提供商

| 提供商 | 说明 | 默认模型 | 官网 |
|-------|------|---------|------|
| **Claude** | Anthropic 的 Claude 系列 | claude-3-5-sonnet-20241022 | https://anthropic.com |
| **OpenAI** | GPT-4、GPT-3.5 等 | gpt-4 | https://openai.com |
| **通义千问** | 阿里云通义千问 | qwen-turbo | https://dashscope.aliyun.com |
| **DeepSeek** | DeepSeek 系列 | deepseek-chat | https://deepseek.com |
| **Generic** | 任何兼容 OpenAI API 的服务 | 自定义 | - |

---

## ⚙️ 配置方法

### 1. 创建环境变量文件

```bash
cd ~/.agents/skills/stock-screener/api
cp .env.example .env
```

### 2. 编辑 `.env` 文件

根据您选择的提供商，设置相应的环境变量：

---

## 📋 提供商配置示例

### 选项 1: Claude (Anthropic)

```bash
# .env
LLM_PROVIDER=claude
LLM_API_KEY=sk-ant-api03-xxx
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

**获取 API Key**:
1. 访问 https://console.anthropic.com
2. 注册/登录账号
3. 在 API Keys 页面生成密钥

**可用模型**:
- `claude-3-5-sonnet-20241022` - 最新版本，推荐
- `claude-3-opus-20240229` - 最强性能
- `claude-3-sonnet-20240229` - 平衡性能
- `claude-3-haiku-20240307` - 快速响应

---

### 选项 2: OpenAI (GPT)

```bash
# .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-xxx
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

**获取 API Key**:
1. 访问 https://platform.openai.com
2. 注册/登录账号
3. 在 API keys 页面生成密钥

**可用模型**:
- `gpt-4` - GPT-4（推荐）
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - 经济实惠

---

### 选项 3: 通义千问 (Qwen)

```bash
# .env
LLM_PROVIDER=qwen
LLM_API_KEY=sk-xxx
LLM_MODEL=qwen-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

**获取 API Key**:
1. 访问 https://dashscope.aliyun.com
2. 注册/登录阿里云账号
3. 在 API-KEY 管理页面创建密钥

**可用模型**:
- `qwen-turbo` - 快速响应
- `qwen-plus` - 平衡性能
- `qwen-max` - 最强性能

---

### 选项 4: DeepSeek

```bash
# .env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

**获取 API Key**:
1. 访问 https://platform.deepseek.com
2. 注册/登录账号
3. 在 API Keys 页面生成密钥

**可用模型**:
- `deepseek-chat` - 通用对话
- `deepseek-coder` - 代码专用

---

### 选项 5: 自定义 OpenAI 兼容 API

如果您使用的是兼容 OpenAI API 格式的服务（如 OneAPI、LocalAI 等），可以使用 Generic 提供商：

```bash
# .env
LLM_PROVIDER=generic
LLM_API_KEY=your-api-key
LLM_MODEL=your-model-name
LLM_BASE_URL=https://your-api-endpoint.com/v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

**适用场景**:
- 自建模型服务
- OneAPI 中转
- LocalAI 本地部署
- 其他兼容 OpenAI 格式的 API

---

## 🧪 测试配置

配置完成后，可以通过以下方式测试：

### 方法 1: 使用 API 端点

```bash
curl -X POST http://localhost:8000/api/ai/market-analysis \
  -H "Content-Type: application/json" \
  -d '{"index":"SSE","period":"1M"}'
```

### 方法 2: 在前端界面测试

1. 启动后端服务
2. 打开前端 UI
3. 访问 AI 助手页面
4. 尝试市场分析功能

---

## 🔧 高级配置

### 温度参数 (Temperature)

控制输出的随机性：
- `0.0` - 最确定、最一致的输出
- `0.3-0.5` - 适合需要准确性的任务（如数据分析）
- `0.7-0.9` - 适合需要创造性的任务（如文本生成）
- `1.0+` - 最随机、最多样化

```bash
LLM_TEMPERATURE=0.3  # 用于市场分析
```

### 最大 Token 数 (Max Tokens)

控制输出长度：
- `500-1000` - 简短回复
- `2000-4000` - 中等长度（推荐）
- `4000+` - 详细分析

```bash
LLM_MAX_TOKENS=3000
```

---

## 💰 成本对比

| 提供商 | 模型 | 输入价格 | 输出价格 | 性价比 |
|-------|------|---------|---------|--------|
| Claude | 3.5 Sonnet | $3/MTok | $15/MTok | ⭐⭐⭐⭐⭐ |
| OpenAI | GPT-4 | $30/MTok | $60/MTok | ⭐⭐⭐ |
| OpenAI | GPT-3.5 | $0.5/MTok | $1.5/MTok | ⭐⭐⭐⭐⭐ |
| Qwen | Turbo | ¥0.3/MTok | ¥0.6/MTok | ⭐⭐⭐⭐⭐ |
| DeepSeek | Chat | ¥0.1/MTok | ¥0.2/MTok | ⭐⭐⭐⭐⭐ |

*价格仅供参考，以官方最新为准*

---

## 🛡️ 安全建议

1. **不要提交 API Key 到代码库**
   - `.env` 文件已在 `.gitignore` 中
   - 使用 `.env.example` 作为模板

2. **限制 API 使用量**
   - 在提供商控制台设置每月额度
   - 监控 API 调用量

3. **使用环境变量**
   ```bash
   export LLM_API_KEY=your-key
   ```

4. **密钥轮换**
   - 定期更换 API Key
   - 删除不使用的旧密钥

---

## 🔄 切换提供商

如果需要切换 LLM 提供商，只需修改 `.env` 文件并重启后端服务：

```bash
# 修改 .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-xxx
LLM_MODEL=gpt-4

# 重启服务
# Ctrl+C 停止当前服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

无需修改代码，服务会自动使用新的配置。

---

## 📝 示例：完整的 .env 文件

```bash
# 使用 Claude
LLM_PROVIDER=claude
LLM_API_KEY=sk-ant-api03-xxxxxxxxxx
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# 数据库路径
DATABASE_URL=sqlite:////Users/yinchang/.vntrader/database.db
FUNDAMENTAL_DB_URL=sqlite:////Users/yinchang/.vntrader/fundamental.db

# 存储路径
STOCK_POOL_DIR=/Users/yinchang/.vntrader/stock_pools
SCREEN_RESULTS_DIR=/Users/yinchang/.vntrader/screen_results
CHARTS_DIR=/Users/yinchang/.vntrader/charts
```

---

## ❓ 常见问题

### Q: 如何选择合适的 LLM？

**A**: 根据您的需求：
- **预算充足**：Claude 3.5 Sonnet 或 GPT-4（质量最高）
- **预算有限**：通义千问、DeepSeek（性价比高）
- **快速响应**：GPT-3.5 Turbo、Qwen Turbo
- **中文场景**：通义千问、DeepSeek（中文优化好）

### Q: API Key 存储在哪里？

**A**: API Key 存储在 `.env` 文件中，该文件在 `.gitignore` 中被忽略，不会被提交到代码库。

### Q: 可以同时使用多个提供商吗？

**A**: 目前一次只能使用一个提供商。如需切换，修改 `.env` 文件并重启服务即可。

### Q: 如何减少 API 成本？

**A**:
1. 使用更便宜的模型（如 GPT-3.5、Qwen Turbo）
2. 降低 `LLM_MAX_TOKENS` 限制输出长度
3. 缓存常见查询结果
4. 使用本地部署的开源模型

---

## 📚 相关文档

- [Claude API 文档](https://docs.anthropic.com/claude/reference)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [通义千问文档](https://help.aliyun.com/zh/dashscope)
- [DeepSeek API 文档](https://api-docs.deepseek.com)

---

*最后更新：2026-04-03*
