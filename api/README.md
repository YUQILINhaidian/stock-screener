# Stock Screener GUI - FastAPI Backend

这是选股 Skill 的 Web API 后端，提供 RESTful API 和 WebSocket 实时推送。

## 项目结构

```
api/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── db.py                # 数据库连接
│   ├── api/                 # API 路由
│   │   ├── screener.py      # 选股 API
│   │   ├── backtest.py      # 回测 API
│   │   ├── portfolio.py     # 股票池 API
│   │   └── ai.py            # AI 助手 API
│   ├── services/            # 业务逻辑层
│   │   ├── screener_engine.py
│   │   ├── backtest_engine.py
│   │   ├── portfolio_manager.py
│   │   └── ai_service.py
│   └── models/              # Pydantic 数据模型
│       ├── screener.py
│       ├── backtest.py
│       └── portfolio.py
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd api
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 选股 (Screener)

- `GET /api/strategies` - 获取可用策略列表
- `POST /api/screen/run` - 执行选股
- `GET /api/screen/result/{task_id}` - 获取选股结果
- `WS /ws/screen/{task_id}` - WebSocket 实时进度推送

### 回测 (Backtest)

- `POST /api/backtest/create` - 创建回测任务
- `GET /api/backtest/result/{task_id}` - 获取回测结果

### 股票池 (Portfolio)

- `POST /api/portfolio/create` - 创建股票池
- `GET /api/portfolio/{id}` - 获取股票池详情
- `POST /api/portfolio/{id}/update` - 更新持仓价格
- `GET /api/portfolio/summary` - 获取所有股票池汇总

### AI 助手 (AI)

- `POST /api/ai/market-analysis` - 市场环境分析
- `POST /api/ai/stock-analysis` - 个股 AI 解读
- `POST /api/ai/nl-screen` - 自然语言选股

## 开发

### 添加新策略

1. 在 `services/screener_engine.py` 中注册策略
2. 在 `api/screener.py` 中添加路由

### 运行测试

```bash
pytest tests/
```

## 部署

### Docker

```bash
docker build -t stock-screener-api .
docker run -p 8000:8000 stock-screener-api
```

### 生产环境

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 配置

环境变量：

```bash
# .env 文件
DATABASE_URL=sqlite:////Users/yinchang/.vntrader/stock_data.db
CLAUDE_API_KEY=your_api_key_here
REDIS_URL=redis://localhost:6379
```
