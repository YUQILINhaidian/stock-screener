# 接近一年新高策略详解

## 策略来源

本策略源自陶博士2006，原文链接：https://mp.weixin.qq.com/s/jLS-UxL74hB-rbbMLsf28g

## 核心公式

### 接近一年新高

```python
# 通达信公式
CLOSE/HHV(HIGH,250) > 0.9

# Python实现
current_close / max_high_250 > 0.9
```

**含义**：今日收盘价 / 过去250个交易日内的最高价 > 0.9

即：股价在一年新高价格的**90%以上**

### 一年新高

```python
# 通达信公式
NH:IF(H<HHV(H,250),0,1)

# Python实现
is_new_high = 1 if current_high >= max_high_250 else 0
```

**含义**：如果今日最高价等于或超过过去250个交易日最高价，则返回1

## 策略逻辑

### 为什么有效？

1. **趋势跟踪**：接近新高的股票往往处于上升趋势中
2. **强者恒强**：能够接近或突破一年高点的股票，通常基本面较好
3. **动量效应**：股价动量具有延续性，突破后往往还有上涨空间
4. **机构关注**：创新高的股票更容易吸引机构资金关注

### 筛选条件

| 条件 | 说明 |
|------|------|
| 价格位置 | 收盘价 >= 250日最高价 × 90% |
| 时间窗口 | 250个交易日（约一年） |
| 股票池 | 建议在"基金持股3%+北向持股三千万"板块中筛选 |

## Python实现

### 数据库查询版本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接近一年新高选股策略
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def screen_near_year_high(db_path='~/.vntrader/database.db', threshold=0.9):
    """
    筛选接近一年新高的股票
    
    参数:
        db_path: 数据库路径
        threshold: 阈值，默认0.9表示90%
    
    返回:
        DataFrame: 符合条件的股票列表
    """
    conn = sqlite3.connect(db_path)
    
    # 查询最近250个交易日的数据
    query = """
    WITH ranked_data AS (
        SELECT 
            symbol,
            trade_date,
            close,
            high,
            MAX(high) OVER (
                PARTITION BY symbol 
                ORDER BY trade_date 
                ROWS BETWEEN 249 PRECEDING AND CURRENT ROW
            ) as high_250,
            ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY trade_date DESC) as rn
        FROM daily_data
        WHERE trade_date >= date('now', '-400 days')
    )
    SELECT 
        symbol,
        trade_date,
        close,
        high_250,
        ROUND(close * 1.0 / high_250, 4) as position_ratio
    FROM ranked_data
    WHERE rn = 1 
        AND close * 1.0 / high_250 >= ?
    ORDER BY position_ratio DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(threshold,))
    conn.close()
    
    return df

if __name__ == '__main__':
    results = screen_near_year_high()
    print(f"筛选结果：{len(results)}只股票")
    print(results.to_string())
```

### 简化版本（使用本地数据）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接近一年新高选股 - 简化版
"""

import pandas as pd
import numpy as np

def screen_near_year_high(df, threshold=0.9):
    """
    筛选接近一年新高的股票
    
    参数:
        df: 包含 close, high 列的DataFrame
        threshold: 阈值
    
    返回:
        bool: 是否接近一年新高
    """
    if len(df) < 250:
        return False
    
    high_250 = df['high'].rolling(window=250).max().iloc[-1]
    current_close = df['close'].iloc[-1]
    
    return current_close / high_250 >= threshold
```

## 使用建议

### 选股范围

陶博士建议在以下板块中筛选：
- **基金持股3%以上**：机构认可度高
- **北向持股三千万以上**：外资关注

这样可以过滤掉：
- 流动性差的股票
- 基本面有问题的股票
- 庄股、妖股

### 后续分析

筛选出股票后，建议：

1. **查看K线图**：逐个翻看，确认趋势
2. **关注净利润断层**：如果是因为业绩突破，更值得关注
3. **检查成交量**：放量突破更可靠
4. **确认行业趋势**：行业景气度高的股票更安全

### 止损设置

- 建议止损位：-5%到-8%
- 突破失败后及时止损

## 与其他策略组合

### 组合1：接近新高 + RPS

```python
# 同时满足接近新高和高RPS
condition1 = close / high_250 >= 0.9
condition2 = rps_120 > 80
final_condition = condition1 and condition2
```

### 组合2：接近新高 + 成交量放大

```python
# 接近新高且成交量放大
condition1 = close / high_250 >= 0.9
condition2 = volume / avg_volume_20 > 1.5
final_condition = condition1 and condition2
```

### 组合3：接近新高 + 均线多头

```python
# 接近新高且均线多头排列
condition1 = close / high_250 >= 0.9
condition2 = ma_20 > ma_60 > ma_120
final_condition = condition1 and condition2
```

## 注意事项

1. **不是万能公式**：仅作为筛选工具，不构成买卖建议
2. **需要结合基本面**：业绩、估值、行业等因素同样重要
3. **注意市场环境**：弱势市场中突破容易失败
4. **假突破风险**：需要设置止损，控制风险
5. **数据延迟**：当日数据通常次日可用

## 历史案例

### 成功案例特征

- 突破时成交量放大
- 基本面支撑（业绩增长）
- 行业景气度高
- 机构持股比例上升

### 失败案例特征

- 突破时成交量萎缩
- 基本面恶化
- 行业处于下行周期
- 大盘环境弱势

## 参考资料

- 陶博士2006公众号：接近一年新高的选股公式（20190210）
- 《股票魔法师》Mark Minervini
- 《笑傲股市》William J. O'Neil
