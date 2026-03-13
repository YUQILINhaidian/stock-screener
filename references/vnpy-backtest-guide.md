# VNPy策略回测指南

## 📌 概述

VNPy是一个专业的量化交易框架，提供了完整的回测引擎。本文档介绍如何使用VNPy回测引擎对选股策略信号进行历史回溯分析。

---

## 🎯 核心功能

1. **信号跟随策略**：根据筛选信号买入，持仓N天后卖出
2. **专业统计指标**：收益率、夏普比率、最大回撤等
3. **真实交易模拟**：包含手续费、滑点等交易成本

---

## 🚀 快速开始

### 运行回测

```bash
# 使用最新信号文件回测
python3 ~/vnpy_backtest_signals.py --days 5 --max 10

# 指定CSV文件回测
python3 ~/vnpy_backtest_signals.py --file ~/.vntrader/train_daily_advanced_20260309.csv --days 5

# 参数说明
--days N    # 持仓天数（默认5天）
--max N     # 最大回测股票数
--file PATH # 指定信号文件
```

### 回测输出

```
首个交易日：    2026-03-10
最后交易日：    2026-03-15
总交易日：      5
盈利交易日：    3
亏损交易日：    2
起始资金：      100,000.00
结束资金：      105,230.00
总收益率：      5.23%
年化收益：      125.52%
最大回撤:       2.15
Sharpe Ratio：  2.35
总成交笔数：    10
```

---

## 📊 回测引擎架构

### 核心组件

| 组件 | 说明 |
|------|------|
| `BacktestingEngine` | VNPy回测引擎核心 |
| `SignalFollowStrategy` | 信号跟随策略（CTA模板） |
| `CtaTemplate` | CTA策略基类 |

### 策略逻辑

```python
class SignalFollowStrategy(CtaTemplate):
    """信号跟随策略"""
    
    # 参数
    holding_days = 5  # 持仓天数
    
    def on_bar(self, bar):
        # 1. 无持仓时，次日开盘买入
        if not self.position_opened and self.pos == 0:
            self.buy(bar.close_price, 1)
            self.position_opened = True
        
        # 2. 持仓达到指定天数，卖出
        elif self.pos > 0:
            self.entry_bar_count += 1
            if self.entry_bar_count >= self.holding_days:
                self.sell(bar.close_price, abs(self.pos))
```

---

## ⚙️ 回测配置

### 默认参数

| 参数 | 值 | 说明 |
|------|-----|------|
| rate | 0.0003 | 手续费率 0.03% |
| slippage | 0.01 | 滑点 1分 |
| size | 100 | 每手股数 |
| pricetick | 0.01 | 最小价格变动 |
| capital | 100000 | 初始资金 10万 |

### 修改配置

在 `vnpy_backtest_signals.py` 中修改：

```python
self.engine.set_parameters(
    vt_symbol=vt_symbol,
    interval=Interval.DAILY,
    start=start_date,
    end=end_date,
    rate=0.0003,      # 手续费率
    slippage=0.01,    # 滑点
    size=100,         # 每手股数
    pricetick=0.01,   # 最小价格变动
    capital=100000,   # 初始资金
)
```

---

## 📈 统计指标说明

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| total_return | 总收益率 | (结束资金 - 起始资金) / 起始资金 |
| annual_return | 年化收益 | 总收益率 × (365 / 持有天数) |
| max_drawdown | 最大回撤 | 最大连续亏损幅度 |
| sharpe_ratio | 夏普比率 | (收益率 - 无风险利率) / 收益率标准差 |
| winning_rate | 胜率 | 盈利交易次数 / 总交易次数 |

---

## 🔧 高级用法

### 自定义策略

继承 `CtaTemplate` 创建自定义策略：

```python
from vnpy_ctastrategy import CtaTemplate

class MyStrategy(CtaTemplate):
    """自定义策略"""
    
    # 参数
    fast_period = 5
    slow_period = 20
    
    parameters = ["fast_period", "slow_period"]
    
    def on_bar(self, bar):
        # 实现你的策略逻辑
        pass
```

### 多股票组合回测

```bash
# 回测所有策略的最新信号
python3 ~/vnpy_backtest_signals.py --all
```

---

## ⚠️ 注意事项

### 数据要求

1. **信号日期**：需要有足够的后续数据进行回测
2. **持仓天数**：确保信号日期后有 `hold_days` 天的数据
3. **数据完整性**：数据库中需要有完整的K线数据

### 常见问题

**Q: 回测结果为空？**
- 检查信号日期是否有足够的后续数据
- 检查数据库中是否有该股票的K线数据

**Q: 成交记录为空？**
- 策略可能没有触发买入条件
- 检查策略逻辑是否正确

**Q: 如何查看详细日志？**
- 查看VNPy日志文件
- 在策略中添加 `self.write_log()` 输出调试信息

---

## 📂 输出文件

```
~/.vntrader/backtest_results/
├── backtest_20260311_150000.csv  # 回测结果CSV
└── backtest_report.html          # HTML报告
```

---

## 🔗 相关链接

- [VNPy官方文档](https://www.vnpy.com/)
- [CTA策略模块](https://www.vnpy.com/docs/cn/cta_strategy.html)
- [回测引擎说明](https://www.vnpy.com/docs/cn/backtesting.html)

---

*文档更新：2026-03-11*
