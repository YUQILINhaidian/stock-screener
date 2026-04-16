# 快速开始

本指南帮助你在 5 分钟内完成第一次选股。

---

## 场景 1：运行月线反转策略

**适合**：中长期投资者，寻找趋势反转机会

### 步骤

#### 1. 检查数据新鲜度

```bash
python3 ~/.agents/skills/stock-screener/python/check_db_freshness.py
```

**预期输出**：
```
✅ 数据延迟1天（正常，当日数据通常次日更新）
```

#### 2. 执行策略

```bash
python3 ~/.agents/skills/stock-screener/python/screen_monthly_reversal.py
```

**执行过程**：
- 加载5189只股票
- 计算RPS指标
- 应用7个筛选条件
- 输出符合条件的股票列表

#### 3. 查看结果

结果保存在：
```
~/.vntrader/screen_results/monthly_reversal_YYYYMMDD.csv
```

---

## 场景 2：运行口袋支点策略

**适合**：中短期投资者，寻找成交量突破买点

```bash
python3 ~/.agents/skills/stock-screener/python/screen_pocket_pivot.py
```

---

## 场景 3：如果数据过期

**数据延迟 > 3天时**，先更新数据：

```bash
# 1. 更新K线数据（约3-5分钟）
python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py

# 2. 更新RPS计算（约1分钟）
python3 ~/.agents/skills/stock-screener/python/update_daily_data.py

# 3. 重新执行策略
python3 ~/.agents/skills/stock-screener/python/screen_monthly_reversal.py
```

---

## 如何解读结果

### CSV列说明

| 列名 | 含义 |
|------|------|
| symbol | 股票代码 |
| close | 收盘价 |
| ratio_30_120 | 30日/120日价格比值（越高越强势） |
| turnover | 成交额（万） |
| trade_date | 数据日期 |

### 筛选建议

1. **优先选择** ratio_30_120 > 1.3 的股票
2. **关注成交额** > 10亿的标的（流动性好）
3. **结合RPS** 优选RPS > 90的股票

---

## 下一步

- 查看 [daily-workflow.md](daily-workflow.md) 了解日常工作流程
- 阅读 [策略详解](../references/strategies/) 深入理解策略逻辑
