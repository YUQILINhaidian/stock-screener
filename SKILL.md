---
name: stock-screener
description: This skill should be used when the user asks about "stock screening", "选股", "筛选股票", "火车头策略", "顺向火车轨", "蓝色钻石", "三线红", "圆弧底", "首次涨停", "一线红", "RPS strategy", "股票池", "回测", "策略验证", "backtest", "月线反转", "口袋支点", "第二阶段", "老鸭头", "老鸭头形态", or needs help with screening strong stocks, analyzing RPS values, executing quantitative stock selection strategies, or backtesting strategy signals.
version: 2.0.0
---

# Stock Screener - 量化选股策略工具

Stock Screener 提供多种经过验证的量化选股策略，帮助用户快速筛选强势股票。

---

## 何时使用

**触发关键词**：

| 类别 | 关键词 |
|------|--------|
| 通用 | 选股、筛选股票、找出强势股、股票池 |
| 策略名 | 火车头、MRGC、SXHCG、顺向火车轨、月线反转、口袋支点、第二阶段、老鸭头 |
| 技术指标 | 三线红、一线红、RPS、相对强度 |
| 形态 | 圆弧底、蓝色钻石、底部反转、趋势反转、老鸭头形态 |
| 功能 | 回测、策略验证、数据更新 |

---

## 核心工作流程

```
用户请求 → 选择策略 → 检查数据 → 执行筛选 → 生成报告
```

### 步骤 1：选择策略

当用户触发选股时，使用 `preview_ask` 工具询问：

**问题**："请选择要执行的选股策略："

| 选项 | 策略名 | 推荐度 | 特点 |
|------|--------|--------|------|
| 1 | 月线反转策略 | ⭐⭐⭐⭐⭐ | 陶博士三大买点之一,趋势反转 |
| 2 | 口袋支点策略 | ⭐⭐⭐⭐⭐ | 陶博士三大买点之一,成交量突破 |
| 3 | 第二阶段策略 | ⭐⭐⭐⭐⭐ | 《股票魔法师》经典,主升浪 |
| 4 | 火车头策略 | ⭐⭐⭐⭐ | MRGC + SXHCG 双策略组合 |
| 5 | 老鸭头形态 | ⭐⭐⭐⭐ | 唐能通经典形态,突破前洗盘 |
| 6 | 接近一年新高 | ⭐⭐⭐⭐ | 最简单有效,突破机会 |
| 7 | 顺向火车轨3.0 | ⭐⭐⭐⭐ | RPS120+250>185,均线多头 |
| 8 | 中期调整后选股 | ⭐⭐⭐⭐ | 250日翻倍+调整≤50% |
| 9 | 三线红策略 | ⭐⭐⭐ | RPS纯技术筛选 |
| 10 | 蓝色钻石策略 | ⭐⭐⭐ | 捕捉第二波上涨 |
| 11 | 圆弧底策略 | ⭐⭐⭐ | 底部反转,低频高质量 |
| 12 | 首次涨停&一线红 | ⭐⭐⭐ | 涨停突破信号 |

---

### 步骤 2：检查数据新鲜度

```bash
python3 ~/.agents/skills/stock-screener/python/check_db_freshness.py
```

- **数据延迟 ≤ 1天**：直接执行
- **数据延迟 > 3天**：建议用户先更新数据

---

### 步骤 3：执行策略

| 策略 | 执行命令 |
|------|----------|
| 月线反转 | `python3 ~/.agents/skills/stock-screener/python/screen_monthly_reversal.py` |
| 口袋支点 | `python3 ~/.agents/skills/stock-screener/python/screen_pocket_pivot.py` |
| 第二阶段 | `python3 ~/.agents/skills/stock-screener/python/screen_stage2.py` |
| 火车头策略 | `python3 ~/.agents/skills/stock-screener/python/train_daily_advanced_strategy.py` |
| 老鸭头形态 | `python3 ~/.agents/skills/stock-screener/python/screen_old_duck_head.py` |
| 接近一年新高 | `python3 ~/.agents/skills/stock-screener/python/screen_near_year_high.py` |
| 顺向火车轨3.0 | `python3 ~/.agents/skills/stock-screener/python/sxhcg3_strategy.py` |
| 中期调整后选股 | `python3 ~/.agents/skills/stock-screener/python/mid_term_adjustment_strategy.py` |
| 三线红策略 | `python3 ~/.agents/skills/stock-screener/python/screen_three_line_red.py` |
| 蓝色钻石策略 | `python3 ~/.agents/skills/stock-screener/python/blue_diamond_strategy.py` |
| 圆弧底策略 | `python3 ~/.agents/skills/stock-screener/python/arc_bottom_strategy.py` |
| 首次涨停&一线红 | `python3 ~/.agents/skills/stock-screener/python/first_limit_up_strategy.py` |

---

### 步骤 4：生成报告

执行完成后，结果保存在：
- **CSV结果**: `~/.vntrader/screen_results/<策略名>_YYYYMMDD.csv`
- **分析报告**: 自动生成HTML报告

---

## 数据更新流程

```bash
# 1. 更新K线数据
python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py

# 2. 更新RPS数据
python3 ~/.agents/skills/stock-screener/python/update_daily_data.py
```

**建议更新时间**：每个交易日收盘后 17:00-18:00

---

## 策略详解

| 策略 | 详解文档 |
|------|----------|
| 月线反转 | [monthly-reversal.md](references/strategies/monthly-reversal.md) |
| 口袋支点 | [pocket-pivot.md](references/strategies/pocket-pivot.md) |
| 第二阶段 | [stage2.md](references/strategies/stage2.md) |
| 其他策略 | [references/strategies/](references/strategies/) |

---

## 风险管理

### 仓位控制
- **单只股票仓位**：≤ 10%
- **总仓位**：50-70%（根据市场环境调整）
- **股票数量**：5-10只分散投资

### 止损设置
| 策略类型 | 止损位 |
|----------|--------|
| 长期策略 | -8% 到 -10% |
| 中期策略 | -5% 到 -8% |
| 短期策略 | -3% 到 -5% |

---

## 常见问题

**Q: 筛选结果为0怎么办？**
A: 检查数据是否最新，或尝试放宽筛选条件（弱市中结果会减少）

**Q: 多久更新一次数据？**
A: 建议每个交易日收盘后更新一次

**Q: 如何选择策略？**
A: 新手推荐月线反转或口袋支点，进阶可组合多策略

**Q: 筛选出的股票什么时候买？**
A: 建议次日开盘观察，确认信号有效后介入

---

## 相关文档

- **快速开始**: [examples/quick-start.md](examples/quick-start.md)
- **日常工作流**: [examples/daily-workflow.md](examples/daily-workflow.md)
- **策略对比**: [references/strategy-comparison.md](references/strategy-comparison.md)
- **回测指南**: [references/backtest-guide.md](references/backtest-guide.md)

---

## 目录结构

```
stock-screener/
├── SKILL.md                    # 本文档（入口）
├── README.md                   # 项目说明
├── references/strategies/       # 策略详解文档
├── examples/                   # 使用示例
├── scripts/                    # 执行脚本
├── python/                     # Python源码
└── archive/                    # 历史文档
```
