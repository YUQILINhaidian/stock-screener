# 口袋支点策略详解

## 策略来源

本策略源自《像欧奈尔信徒一样交易》（Trade Like an O'Neil Disciple）作者 Gil Morales 和 Dr. Chris Kacher。

陶博士改进版参考：https://mp.weixin.qq.com/s/JnTeY7T0rPcWXE3NeHRb7Q

## 核心理论

口袋支点（Pocket Pivot）是一种**成交量突破信号**，通常出现在股票突破前的最后调整阶段。

### 核心思想

当股票在底部区域出现**异常放量**，但价格并未大幅上涨时，往往预示着**主力资金正在吸筹**。这种成交量异常是机构建仓的重要信号。

### 与传统突破的区别

| 特征 | 传统突破 | 口袋支点 |
|------|---------|---------|
| 成交量位置 | 突破时放量 | 突破前放量 |
| 价格位置 | 新高附近 | 调整阶段 |
| 买入时机 | 突破后 | 突破前 |

## 筛选条件详解

### 条件1：RPS强度

```
KD1:=RPS250>=87 OR RPS120>=90 OR RPS50>=90
```

**含义**：50日RPS、120日RPS、250日RPS至少有一个达到90（或87）以上。

**目的**：确保股票具有相对强度，表现优于市场大部分股票。

### 条件2：成交量放大

```
FKD21:=AMO=HHV(AMO,10);{创10日的最高成交金额}
FKD22:=C/REF(C,1)>1.099;{当日上涨超过9.9%}
FKD23:=AMO/MA(AMO,10)>2;{成交金额是10天平均的一倍以上}
KD2:=FKD21 OR FKD22 OR FKD23
```

**含义**：满足以下任一条件：
- 创10日最高成交金额
- 当日涨幅超过9.9%
- 成交金额是10天平均的2倍以上

**目的**：确认主力资金介入，成交量是关键信号。

### 条件3：均线突破

```
FKD31:=C>MA(C,90) AND MA(C,90)>=REF(MA(C,90),5) AND H>=HHV(H,90)
FKD32:=C>MA(C,100) AND MA(C,100)>=REF(MA(C,100),5) AND H>=HHV(H,100) AND MA(C,90)>=REF(MA(C,90),5)
FKD33:=C>MA(C,120) AND MA(C,120)>=REF(MA(C,120),2)
KD3:=FKD31 OR FKD32 OR FKD33
```

**含义**：满足以下任一组合：
- 收盘在90日均线上方，且90日线上升，且创90日新高
- 收盘在100日均线上方，且100日线上升，且创100日新高
- 收盘在120日均线上方，且120日线上升

**目的**：确认趋势向上，均线支撑有效。

### 条件4：结构紧凑

```
KD4:=LLV(L,15)>LLV(L,50)*0.995 OR FKD250
```

**含义**：15日内最低价不是50日内最低价，或者创250日新高。

**目的**：确保股票结构紧凑，未出现大幅下跌。

### 条件5：调整幅度限制

```
H120:=HHV(H,120)
T1:=HHVBARS(H,120)
L120:=LLV(L,T1+1)
FKD51:=LLV(L,40)/HHV(H,120)>0.5
FKD5:=FKD51 OR FKD250
KD5:=L120/H120>0.54 AND FKD5
```

**含义**：
- 40日内最低价不低于120日内最高价的一半
- 或者创250日新高
- 阶段最大下跌幅度不超过46%

**目的**：限制中期调整幅度，确保股票基本面未恶化。

### 条件6：结构紧凑条件

```
FKD41:=FKD250 OR LLV(L,15)>LLV(L,50)
FKD42:=LLV(L,15)=LLV(L,50) AND LLV(L,15)>LLV(L,100) AND H/HHV(H,250)>0.88
FKD43:=LLV(L,15)=LLV(L,50) AND LLV(L,15)>LLV(L,100) AND H/HHV(H,250)>0.75 AND H>=HHV(H,40) AND C/REF(C,1)>1.07
KD6:=FKD41 OR FKD42 OR FKD43
```

**含义**：满足以下任一条件：
- 创250日新高，或15日低点不是50日低点
- 15日低点等于50日低点但不是100日低点，且接近一年新高（>88%）
- 15日低点等于50日低点但不是100日低点，且接近一年新高（>75%），且创40日新高，且当日涨幅>7%

**目的**：确保价格结构紧凑，避免选入弱势股。

### 条件7：涨幅要求

```
KD7:=C/REF(C,1)>=1.05
```

**含义**：当日涨幅>=5%

**目的**：确认突破动力。

### 条件8：换手率稳定

```
KD8:=REF(MA(100*VOL/(FINANCE(7)/100),1),2)<=15
```

**含义**：两天平均换手率不高于15%

**目的**：避免追高换手率过高的股票。

### 条件9：价格偏离限制

```
KD9:=REF(L,1)<=REF(MA(C,50),1)*1.24 OR REF(L,1)<=REF(MA(C,10),1)*1.03
```

**含义**：昨日最低价偏离50日线<24%，或偏离10日线<3%

**目的**：避免选入价格偏离均线过远的股票。

## 通达信选股公式

```pascal
{陶博士口袋支点}
KD1:=RPS250>=87 OR RPS120>=90 OR RPS50>=90;

{要素一：成交量}
FKD21:=AMO=HHV(AMO,10);
FKD22:=C/REF(C,1)>1.099;
FKD23:=AMO/MA(AMO,10)>2;
KD2:=FKD21 OR FKD22 OR FKD23;

{要素二：均线突破}
FKD311:=C>MA(C,90);
FKD312:=MA(C,90)>=REF(MA(C,90),5);
FKD313:=H>=HHV(H,90);
FKD31:=FKD311 AND FKD312 AND FKD313;

FKD321:=C>MA(C,100);
FKD322:=MA(C,100)>=REF(MA(C,100),5);
FKD323:=H>=HHV(H,100);
FKD32:=FKD321 AND FKD322 AND FKD323 AND FKD312;

FKD331:=C>MA(C,120);
FKD332:=MA(C,120)>=REF(MA(C,120),2);
FKD33:=FKD331 AND FKD332;

KD3:=FKD31 OR FKD32 OR FKD33;

{要素三：结构紧凑}
FKD250:=H>=HHV(H,250);
KD4:=LLV(L,15)>LLV(L,50)*0.995 OR FKD250;

{要素四：调整幅度}
H120:=HHV(H,120);
T1:=HHVBARS(H,120);
L120:=LLV(L,T1+1);
FKD51:=LLV(L,40)/HHV(H,120)>0.5;
FKD5:=FKD51 OR FKD250;
KD5:=L120/H120>0.54 AND FKD5;

{要素五：结构紧凑条件}
FKD41:=FKD250 OR LLV(L,15)>LLV(L,50);
FKD42:=LLV(L,15)=LLV(L,50) AND LLV(L,15)>LLV(L,100) AND H/HHV(H,250)>0.88;
FKD43:=LLV(L,15)=LLV(L,50) AND LLV(L,15)>LLV(L,100) AND H/HHV(H,250)>0.75 AND H>=HHV(H,40) AND C/REF(C,1)>1.07;
KD6:=FKD41 OR FKD42 OR FKD43;

{要素六：涨幅}
KD7:=C/REF(C,1)>=1.05;

{要素七：换手率}
KD8:=REF(MA(100*VOL/(FINANCE(7)/100),1),2)<=15;

{要素八：价格偏离}
KD9:=REF(L,1)<=REF(MA(C,50),1)*1.24 OR REF(L,1)<=REF(MA(C,10),1)*1.03;

XG:=KD1 AND KD2 AND KD3 AND KD4 AND KD5 AND KD6 AND KD7 AND KD8 AND KD9;
BARSSINCEN(XG,20)=0;
```

## Python实现

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口袋支点选股策略
根据陶博士改进版的9条标准筛选股票
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

DB_PATH = Path.home() / '.vntrader' / 'database.db'

def check_pocket_pivot(df):
    """
    检查股票是否符合口袋支点条件
    
    返回: (is_pocket_pivot, details)
    """
    if len(df) < 250:
        return False, {}
    
    # 获取最新数据
    latest = df.iloc[-1]
    close = latest['close']
    high = latest['high']
    low = latest['low']
    volume = latest['volume']
    
    # 计算均线
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma90'] = df['close'].rolling(window=90).mean()
    df['ma100'] = df['close'].rolling(window=100).mean()
    df['ma120'] = df['close'].rolling(window=120).mean()
    
    # 条件检查
    conditions = {}
    
    # 条件2: 成交量放大
    amo_10 = df['turnover'].iloc[-10:]  # 假设有成交额
    conditions['c2_volume'] = (
        df['turnover'].iloc[-1] == amo_10.max() or  # 创10日最高成交金额
        close / df['close'].iloc[-2] > 1.099 or     # 当日涨幅>9.9%
        df['turnover'].iloc[-1] / amo_10.mean() > 2  # 成交金额是10天平均的2倍
    )
    
    # 条件3: 均线突破
    ma90_rising = df['ma90'].iloc[-1] >= df['ma90'].iloc[-6]
    ma100_rising = df['ma100'].iloc[-1] >= df['ma100'].iloc[-6]
    ma120_rising = df['ma120'].iloc[-1] >= df['ma120'].iloc[-3]
    
    high_90 = df['high'].iloc[-90:].max()
    high_100 = df['high'].iloc[-100:].max()
    
    conditions['c3_ma_breakout'] = (
        (close > df['ma90'].iloc[-1] and ma90_rising and high >= high_90) or
        (close > df['ma100'].iloc[-1] and ma100_rising and high >= high_100) or
        (close > df['ma120'].iloc[-1] and ma120_rising)
    )
    
    # 条件7: 涨幅要求
    conditions['c7_price_change'] = close / df['close'].iloc[-2] >= 1.05
    
    # 检查所有条件
    is_pocket_pivot = all(conditions.values())
    
    return is_pocket_pivot, conditions
```

## 使用建议

### 买入时机
1. 出现口袋支点信号当天或次日买入
2. 结合第二阶段策略使用效果更佳
3. 关注成交量是否持续放大

### 卖出时机
1. 跌破口袋支点最低价止损
2. 突破失败后减仓
3. 达到目标价后止盈

### 风险控制
1. 单只股票仓位不超过10%
2. 设置止损位：-5%到-8%
3. 分散投资：5-10只股票

### 与其他策略组合

1. **口袋支点 + 第二阶段**：在第二阶段中寻找口袋支点
2. **口袋支点 + 接近新高**：在接近新高的股票中寻找口袋支点
3. **口袋支点 + 净利润断层**：口袋支点后出现净利润断层更佳

## 注意事项

1. **成交量是关键**：口袋支点的核心是成交量异常
2. **RPS必须设置**：必须正确计算RPS才能使用
3. **结构紧凑**：避免选入结构松散的股票
4. **市场环境**：弱势市场中信号可能失效
5. **止损严格**：一旦信号失败必须止损

## 参考资料

- 《像欧奈尔信徒一样交易》Gil Morales & Dr. Chris Kacher
- 陶博士2006公众号
- 《股票魔法师》Mark Minervini
