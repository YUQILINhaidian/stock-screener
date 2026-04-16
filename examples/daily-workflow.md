# 日常工作流程

本文档描述每日使用 Stock Screener 的推荐工作流。

---

## 推荐时间

**每个交易日收盘后 17:00-18:00**

---

## 完整工作流

### 1. 更新数据

```bash
# 步骤 1：检查数据新鲜度
python3 ~/.agents/skills/stock-screener/python/check_db_freshness.py

# 步骤 2：更新K线数据
python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py

# 步骤 3：更新RPS数据
python3 ~/.agents/skills/stock-screener/python/update_daily_data.py
```

---

### 2. 执行主要策略

```bash
# 月线反转策略（推荐）
python3 ~/.agents/skills/stock-screener/python/screen_monthly_reversal.py

# 口袋支点策略（推荐）
python3 ~/.agents/skills/stock-screener/python/screen_pocket_pivot.py
```

---

### 3. 分析结果

查看筛选结果：
```bash
# 查看最新结果
ls -lt ~/.vntrader/screen_results/ | head -10

# 用 Numbers 打开
open -a Numbers ~/.vntrader/screen_results/monthly_reversal_*.csv
```

---

### 4. 管理股票池

```bash
# 创建新的股票池
python3 ~/.agents/skills/stock-screener/python/stock_pool_tracker.py create \
  --name my_pool --desc "我的自选"

# 更新股票池价格
python3 ~/.agents/skills/stock-screener/python/stock_pool_tracker.py update \
  --name my_pool

# 查看股票池表现
python3 ~/.agents/skills/stock-screener/python/stock_pool_tracker.py show \
  --name my_pool
```

---

## 周末工作流

### 策略回测

```bash
# 回测月线反转策略（最近5天）
python3 ~/.agents/skills/stock-screener/python/vnpy_backtest_signals.py \
  --file ~/.vntrader/screen_results/monthly_reversal_YYYYMMDD.csv \
  --days 5
```

---

## 快速命令汇总

| 任务 | 命令 |
|------|------|
| 检查数据 | `check_db_freshness.py` |
| 更新K线 | `update_kline_from_baostock.py` |
| 更新RPS | `update_daily_data.py` |
| 月线反转 | `screen_monthly_reversal.py` |
| 口袋支点 | `screen_pocket_pivot.py` |
| 第二阶段 | `screen_stage2.py` |
| 火车头策略 | `train_daily_advanced_strategy.py` |
| 三线红 | `screen_three_line_red.py` |

---

## 设置定时任务（可选）

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每个工作日 17:30 执行）
30 17 * * 1-5 cd ~/.agents/skills/stock-screener/python && python3 update_kline_from_baostock.py && python3 update_daily_data.py && python3 screen_monthly_reversal.py >> ~/.vntrader/logs/stock_screener.log 2>&1
```

---

## 风险管理检查清单

每日检查：

- [ ] 筛选结果数量是否正常
- [ ] 数据日期是否为昨天
- [ ] 股票池价格是否更新
- [ ] 止损位是否需要调整

---

## 相关文档

- [快速开始](quick-start.md)
- [策略详解](../references/strategies/)
- [回测指南](../references/backtest-guide.md)
