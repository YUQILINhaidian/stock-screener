# Stock Screener - 量化选股策略工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

专业的量化选股策略工具，提供多种经过验证的选股策略。

---

## 策略列表

| 策略 | 适用场景 | 推荐度 |
|------|---------|--------|
| 月线反转策略 | 中长期投资、趋势反转 | ⭐⭐⭐⭐⭐ |
| 口袋支点策略 | 中短期投资、突破买点 | ⭐⭐⭐⭐⭐ |
| 第二阶段策略 | 中长期投资、主升浪 | ⭐⭐⭐⭐⭐ |
| 接近一年新高 | 中长期投资、突破机会 | ⭐⭐⭐⭐⭐ |
| 火车头策略 | 中长期投资、波段交易 | ⭐⭐⭐⭐ |
| 顺向火车轨3.0 | 中长期投资、趋势跟踪 | ⭐⭐⭐⭐ |
| 中期调整后选股 | 中长期投资、调整后买入 | ⭐⭐⭐⭐ |
| 三线红策略 | 中长期投资、持续强势 | ⭐⭐⭐ |
| 蓝色钻石策略 | 中期波段、调整买入 | ⭐⭐⭐ |
| 圆弧底策略 | 中长期投资、底部反转 | ⭐⭐⭐ |
| 首次涨停策略 | 短线追涨、涨停突破 | ⭐⭐⭐ |

---

## 快速开始

### 1. 选择策略

```bash
# 月线反转策略
python3 ~/.agents/skills/stock-screener/python/screen_monthly_reversal.py

# 口袋支点策略
python3 ~/.agents/skills/stock-screener/python/screen_pocket_pivot.py

# 第二阶段策略
python3 ~/.agents/skills/stock-screener/python/screen_stage2.py
```

### 2. 检查数据新鲜度

```bash
python3 ~/.agents/skills/stock-screener/python/check_db_freshness.py
```

### 3. 更新数据（如需要）

```bash
python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py
python3 ~/.agents/skills/stock-screener/python/update_daily_data.py
```

---

## 目录结构

```
stock-screener/
├── SKILL.md                    # 入口文档（AI调用）
├── README.md                   # 本文档
│
├── references/strategies/     # 策略详解
│   ├── monthly-reversal.md     # 月线反转策略
│   ├── pocket-pivot.md         # 口袋支点策略
│   ├── stage2.md               # 第二阶段策略
│   └── ...
│
├── examples/                   # 使用示例
│   ├── quick-start.md          # 快速开始
│   └── daily-workflow.md       # 日常工作流
│
├── scripts/                    # 执行脚本
├── python/                     # Python源码
├── api/                        # REST API
├── ui/                         # Web前端
└── archive/                    # 历史文档
```

---

## 策略来源

| 策略 | 来源 |
|------|------|
| 月线反转 | 陶博士2006改进版月线反转6.5 |
| 口袋支点 | 《像欧奈尔信徒一样交易》|
| 第二阶段 | 《股票魔法师》Mark Minervini |
| 接近一年新高 | William O'Neil CANSLIM 系统 |

---

## 使用方式

### 作为 CodeFlicker Skill 使用

在 CodeFlicker 中直接说：
- "选股"
- "运行月线反转策略"
- "帮我筛选强势股"

AI 会自动调用本 skill 执行选股流程。

### 命令行使用

```bash
# 直接执行任意策略
cd ~/.agents/skills/stock-screener/python
python3 screen_<策略名>.py
```

---

## 风险提示

- 历史表现不代表未来收益
- 建议设置止损位（-5%到-10%）
- 分散投资，单只股票仓位 ≤ 10%
- 关注市场整体环境

---

## License

MIT License
