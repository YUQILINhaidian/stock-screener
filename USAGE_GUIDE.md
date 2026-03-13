# Stock Screener 选股策略使用指南

> 量化选股策略工具集 - 基于RPS强度、形态分析、趋势跟踪的多策略筛选系统

---

## 📌 目录

1. [快速开始](#快速开始)
2. [策略概览](#策略概览)
3. [详细使用方法](#详细使用方法)
4. [股票池管理](#股票池管理)
5. [策略汇总分析](#策略汇总分析)
6. [数据更新](#数据更新)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

---

## 🚀 快速开始

### 一键筛选强势股

```bash
# 运行火车头策略（推荐）
python3 ~/train_daily_advanced_strategy.py

# 查看筛选结果
ls -t ~/.vntrader/train_daily_advanced_*.csv | head -1 | xargs cat
```

### 生成HTML报告

```bash
# 生成包含全部筛选结果和K线图的HTML报告
python3 ~/strategy_summary.py --html

# 打开报告
open ~/.vntrader/strategy_summary/summary_*.html
```

### 查看策略汇总

```bash
python3 ~/strategy_summary.py
```

---

## 📊 策略概览

| 策略 | 适用场景 | 难度 | 推荐度 | 执行命令 |
|------|----------|------|--------|----------|
| **月线反转** | 趋势反转 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | `python3 ~/monthly_reversal_strategy.py` |
| **口袋支点** | 突破买点 | ⭐⭐ | ⭐⭐⭐⭐⭐ | `python3 ~/pocket_pivot_strategy.py` |
| **第二阶段** | 主升浪 | ⭐⭐ | ⭐⭐⭐⭐⭐ | `python3 ~/stage2_strategy.py` |
| **接近一年新高** | 突破机会 | ⭐ | ⭐⭐⭐⭐⭐ | `python3 ~/near_year_high_strategy.py` |
| **火车头策略** | 波段交易 | ⭐⭐⭐ | ⭐⭐⭐⭐ | `python3 ~/train_daily_advanced_strategy.py` |
| **三线红** | 持续强势 | ⭐ | ⭐⭐⭐ | `python3 ~/screen_three_line_red.py` |
| **蓝色钻石** | 第二波上涨 | ⭐⭐ | ⭐⭐⭐ | `python3 ~/blue_diamond_strategy.py` |
| **圆弧底** | 底部建仓 | ⭐⭐ | ⭐⭐⭐⭐ | `python3 ~/arc_bottom_strategy.py` |
| **首次涨停&一线红** | 短线追涨 | ⭐⭐ | ⭐⭐⭐⭐ | `python3 ~/first_limit_up_strategy.py` |

---

## 📖 详细使用方法

### 1. 月线反转策略（强烈推荐）

**适用场景**：中长期投资、捕捉趋势反转

**核心条件**：
- 收盘价突破50日均线
- 收盘价突破150日均线
- 收盘价突破200日均线
- 50日均线 > 200日均线
- 当前价格相对强度RS > 70
- 150日均线斜率 > 0
- 200日均线斜率 > 0
- 当前价格 > 50日前价格

**执行**：
```bash
python3 ~/monthly_reversal_strategy.py
```

### 2. 口袋支点策略

**适用场景**：中短期投资、捕捉突破买点

**核心条件**：
- 当日涨幅 ≥ 5%
- RPS50/120/250 多条件满足
- 量比适中（有放量但不极端）
- 价格位置合理
- 结构紧凑

**执行**：
```bash
python3 ~/pocket_pivot_strategy.py
```

### 3. 第二阶段策略

**适用场景**：中长期投资、捕捉主升浪

**核心条件**：
- 股价处于第二阶段（上升趋势）
- 相对强度指标符合要求
- 均线多头排列

**执行**：
```bash
python3 ~/stage2_strategy.py
```

### 4. 接近一年新高策略

**适用场景**：中长期投资、捕捉突破机会

**核心条件**：
- 价格接近52周新高（≥ 85%）
- RPS强度适中

**执行**：
```bash
python3 ~/near_year_high_strategy.py
```

### 5. 火车头策略

**适用场景**：中长期投资、波段交易

**核心条件**：
- MRGC策略：创新高 + 高RPS
- SXHCG策略：双线红（RPS和 > 185）
- RPS120 + RPS250 > 185

**执行**：
```bash
python3 ~/train_daily_advanced_strategy.py
```

### 6. 三线红策略

**适用场景**：中长期投资、持续强势

**核心条件**：
- RPS5 > 90
- RPS120 > 90
- RPS250 > 90

**执行**：
```bash
python3 ~/screen_three_line_red.py
```

### 7. 蓝色钻石策略

**适用场景**：中期波段、调整买入

**核心条件**：
- RPS20 ≥ 90 或 RPS50 ≥ 95
- 短期调整后反弹信号
- 成交量放大

**执行**：
```bash
python3 ~/blue_diamond_strategy.py
```

### 8. 圆弧底策略

**适用场景**：中长期、底部反转建仓

**核心条件**：
- 多重综合均线确认底部反转
- 短线、中短、中线、长线四条加权均线
- LONGCROSS形态确认

**执行**：
```bash
python3 ~/arc_bottom_strategy.py
```

### 9. 首次涨停&一线红策略

**适用场景**：短线追涨、捕捉涨停突破

**核心条件**：
- RPS50/120/250 任一 ≥ 90
- 当日涨停
- 最高价 ≥ 250日最高价 × 50%
- 过去20天内首次满足条件

**执行**：
```bash
python3 ~/first_limit_up_strategy.py
```

---

## 📦 股票池管理

### 创建股票池

```bash
python3 ~/stock_pool_tracker.py create --name my_pool --desc "我的自选股"
```

### 更新价格跟踪

```bash
python3 ~/stock_pool_tracker.py update --name my_pool
```

### 查看表现

```bash
python3 ~/stock_pool_tracker.py show --name my_pool
```

### 生成报告

```bash
python3 ~/stock_pool_tracker.py report --name my_pool
```

---

## 📈 策略汇总分析

### 查看汇总

```bash
# 查看所有策略汇总
python3 ~/strategy_summary.py

# 查看单个策略
python3 ~/strategy_summary.py --strategy pocket_pivot
```

### 生成HTML报告

```bash
# 生成HTML报告（自动生成K线图）
python3 ~/strategy_summary.py --html

# 打开报告
open ~/.vntrader/strategy_summary/summary_*.html
```

### 生成K线图

```bash
# 为所有策略结果生成K线图
python3 ~/strategy_summary.py --generate-charts

# 为单个策略生成K线图
python3 ~/strategy_summary.py -s first_limit_up -c
```

---

## 🧪 策略回测

### VNPy回测引擎

**使用最新信号文件回测**：
```bash
python3 ~/vnpy_backtest_signals.py --days 5 --max 10
```

**指定CSV文件回测**：
```bash
python3 ~/vnpy_backtest_signals.py --file ~/.vntrader/train_daily_advanced_20260309.csv --days 5
```

**参数说明**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| --days | 持仓天数 | 5 |
| --max | 最大回测股票数 | 全部 |
| --file | 指定信号文件 | 最新文件 |

### 简单回测工具

```bash
# 回测指定文件
python3 ~/strategy_backtest.py --file ~/.vntrader/train_daily_advanced_20260309.csv

# 回测所有策略
python3 ~/strategy_backtest.py --all
```

### 回测输出内容

- 总收益率 / 年化收益
- 最大回撤
- Sharpe Ratio（夏普比率）
- 胜率 / 交易次数
- 个股收益明细

### 注意事项

- 信号日期需要至少有 `hold_days` 天后的数据
- 建议使用历史信号文件进行回测
- VNPy回测包含手续费（0.03%）和滑点（0.01元）

---

## 🔄 数据更新

### 完整更新流程

```bash
# 1. 更新K线数据（从Baostock）
python3 ~/update_kline_from_baostock.py

# 2. 检查数据新鲜度
python3 ~/check_db_freshness.py

# 3. 运行策略筛选
python3 ~/train_daily_advanced_strategy.py

# 4. 生成汇总报告
python3 ~/strategy_summary.py --html
```

### 建议更新时间

- **每日收盘后**：17:00-18:00
- **周末**：完整更新和回顾

### 设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加每日18:00自动更新
0 18 * * 1-5 cd ~ && python3 update_kline_from_baostock.py >> ~/.vntrader/cron.log 2>&1
```

---

## 💡 最佳实践

### 策略组合使用

1. **稳健组合**：月线反转 + 口袋支点 + 第二阶段
2. **激进组合**：首次涨停&一线红 + 蓝色钻石
3. **长期组合**：圆弧底 + 接近一年新高

### 仓位管理

| 策略类型 | 单只仓位 | 总仓位 |
|----------|----------|--------|
| 长线策略 | 10-15% | 60-80% |
| 中线策略 | 5-10% | 40-60% |
| 短线策略 | 3-5% | 20-40% |

### 止损纪律

- **长线策略**：-8% 到 -10%
- **中线策略**：-5% 到 -8%
- **短线策略**：-3% 到 -5%

### 信号确认

1. **形态确认**：查看K线图确认形态
2. **成交量确认**：放量突破更可靠
3. **RPS确认**：RPS越高越强势

---

## ❓ 常见问题

### Q1: 筛选结果为空怎么办？

**可能原因**：
1. 数据过期 - 运行 `python3 ~/update_kline_from_baostock.py` 更新数据
2. 市场环境 - 弱势市场可能没有符合条件的股票
3. 策略条件太严格 - 可以适当放宽条件

### Q2: RPS值如何计算？

**计算方法**：
- 横向百分位排名：在所有股票中计算N日涨幅，然后按百分位排名
- RPS = 百分位 × 100
- 例如：RPS90 表示该股票涨幅超过90%的股票

### Q3: 如何选择合适的策略？

**建议**：
- 新手：从"接近一年新高"策略开始
- 进阶：使用"月线反转"或"口袋支点"
- 高级：组合多个策略，分散风险

### Q4: K线图中文显示乱码？

**解决方案**：
```bash
# 安装中文字体
brew install font-noto-sans-cjk

# 或在代码中设置字体
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
```

### Q5: 如何回测策略效果？

**方法**：
1. 创建股票池记录筛选结果
2. 定期更新价格跟踪
3. 生成报告分析收益

---

## 📂 文件结构

```
~/
├── train_daily_advanced_strategy.py  # 火车头策略
├── pocket_pivot_strategy.py          # 口袋支点策略
├── arc_bottom_strategy.py            # 圆弧底策略
├── first_limit_up_strategy.py        # 首次涨停策略
├── blue_diamond_strategy.py          # 蓝色钻石策略
├── strategy_summary.py               # 策略汇总分析
├── stock_pool_tracker.py             # 股票池管理
├── update_kline_from_baostock.py     # 数据更新
└── check_db_freshness.py             # 数据检查

~/.vntrader/
├── database.db                       # 股票数据库
├── stock_names.json                  # 股票名称缓存
├── stock_pools/                      # 股票池目录
└── strategy_summary/                 # 策略汇总报告
    ├── summary_*.html                # HTML报告
    ├── pocket_pivot/charts/          # 口袋支点K线图
    ├── train_advanced/charts/        # 火车头K线图
    ├── arc_bottom/charts/            # 圆弧底K线图
    └── first_limit_up/charts/        # 首次涨停K线图
```

---

## 🔗 相关链接

- [策略对比分析](references/strategy-comparison.md)
- [圆弧底策略详解](references/arc-bottom-guide.md)
- [首次涨停策略详解](references/first-limit-up-guide.md)
- [策略汇总功能说明](references/strategy-summary-guide.md)

---

*文档版本：1.0.0*  
*更新时间：2026-03-11*  
*作者：Stock Screener Team*
