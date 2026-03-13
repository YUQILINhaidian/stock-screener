# 策略汇总分析功能说明

## 📌 功能概述

策略汇总分析工具用于对不同策略筛选出来的结果进行统一查看和分析，提供筛选指标明细和K线图展示功能。

---

## 🎯 核心功能

### 1. 策略结果汇总

自动扫描以下策略的最新筛选结果：

| 策略 | CSV文件模式 | 说明 |
|------|-------------|------|
| 口袋支点策略 | `pocket_pivot_*.csv` | 51只股票 |
| 火车头高级策略 | `train_daily_advanced_*.csv` | 44只股票 |
| 圆弧底策略 | `arc_bottom_*.csv` | 2只股票 |
| 首次涨停&一线红 | `first_limit_up_*.csv` | 32只股票 |
| 蓝色钻石策略 | `blue_diamond_*.csv` | — |

### 2. 筛选指标明细

不同策略的关键指标：

**口袋支点策略**：
- price, change_pct, volume_ratio
- rps_50, rps_120, rps_250
- max_dd, conditions

**火车头高级策略**：
- price, rps_5, rps_10, rps_50, rps_120, rps_250
- rps_sum, max_dd_120, strategy

**圆弧底策略**：
- close, cond2, cond4, cond6
- converge_ratio

**首次涨停&一线红**：
- close, change_pct, limit_pct
- rps_max, rps_50, rps_120, rps_250

### 3. HTML报告生成

生成包含以下内容的HTML报告：
- 各策略筛选数量统计
- 关键指标均值/中位数/范围
- Top 10股票列表
- 响应式布局，支持移动端查看

### 4. K线图生成

为筛选出的股票生成K线图：
- 显示MA5/MA10/MA20/MA50均线
- 显示成交量
- 显示RPS信息
- 输出为PNG格式

---

## 🚀 使用方法

### 命令行

```bash
# 查看所有策略汇总
python3 ~/strategy_summary.py

# 查看单个策略详情
python3 ~/strategy_summary.py --strategy pocket_pivot

# 生成HTML报告
python3 ~/strategy_summary.py --html

# 生成K线图
python3 ~/strategy_summary.py --generate-charts

# 全部执行
python3 ~/strategy_summary.py -c --html
```

### 使用脚本

```bash
# 执行并打开HTML报告
bash ~/.codeflicker/skills/stock-screener/scripts/strategy-summary.sh --html
```

---

## 📂 输出文件

```
~/.vntrader/strategy_summary/
├── summary_20260311_105811.html     # HTML汇总报告
├── pocket_pivot/
│   └── charts/
│       ├── 002796_SZSE.png
│       ├── 002498_SZSE.png
│       └── ...
├── train_advanced/
│   └── charts/
├── arc_bottom/
│   └── charts/
└── first_limit_up/
    └── charts/
```

---

## 📊 示例输出

```
================================================================================
📊 策略筛选结果汇总
================================================================================
生成时间: 2026-03-11 10:57:50
📈 共 4 个策略有筛选结果，合计 129 只股票

┌────────────────────────────────────────────────────────────────────────────┐
│ 口袋支点策略 (51只)                                          │
│ 捕捉强势股调整后的启动买点，当日涨幅≥5% + 放量 + RPS强势                                    │
│ 文件: pocket_pivot_20260310_193125.csv                            │
└────────────────────────────────────────────────────────────────────────────┘
  Top 5 股票:
    1. 002796.SZSE 世嘉科技   ¥57.32
    2. 002498.SZSE 汉缆股份   ¥8.94
    ...
```

---

## ⚙️ 配置

策略配置可在 `strategy_summary.py` 中的 `STRATEGIES` 字典修改：

```python
STRATEGIES = {
    'pocket_pivot': StrategyConfig(
        name='pocket_pivot',
        display_name='口袋支点策略',
        csv_pattern='pocket_pivot_*.csv',
        key_metrics=['price', 'change_pct', 'volume_ratio', 'rps_50', 'rps_120', 'rps_250', 'max_dd'],
        description='捕捉强势股调整后的启动买点，当日涨幅≥5% + 放量 + RPS强势'
    ),
    # ...
}
```

---

## 🔧 依赖

- Python 3.8+
- pandas
- mplfinance（K线图生成）
- VNPy数据库

安装mplfinance：
```bash
pip install mplfinance
```

---

*文档更新：2026-03-11*
