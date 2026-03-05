# 第二阶段策略详解

## 策略来源

本策略源自《股票魔法师》（Trade Like a Stock Market Wizard）作者 Mark Minervini。

参考文章：https://mp.weixin.qq.com/s/yOgzghJBGow-pIeUTN4Z-A

## 核心理论 - 四阶段模型

Mark Minervini 通过对明星股票的研究，总结出股票周期的四个阶段：

| 阶段 | 名称 | 特征 | 操作建议 |
|------|------|------|---------|
| **第一阶段** | 忽略时期：巩固 | 股价横盘震荡，成交量低迷 | 观望，不买入 |
| **第二阶段** | 突围时期：加速 | 股价突破，成交量放大，趋势向上 | **最佳买入时机** |
| **第三阶段** | 到顶时期：分配利润 | 股价高位震荡，成交量异常 | 卖出，止盈 |
| **第四阶段** | 衰败时期：投降 | 股价下跌，趋势向下 | 空仓，不买入 |

## 第二阶段的特点

### 1. 趋势特征
- 股票价格在200日均线以上
- 200日均线已呈现上涨趋势
- 150日均线在200日均线以上
- 股票价格有明显上涨趋势，价格曲线如台阶状上涨
- 短期移动平均线在长期移动平均线以上

### 2. 成交量特征
- 相较于价格萎靡不振时，价格猛增的日子里股票交易量同样增长明显
- 较大的几周中，上涨的交易周数量高于下跌的数量

### 3. 基本面特征
- 净利润突然上升
- 大型机构需求增加
- 连续几个季度报告出令人印象深刻的净利润

## 筛选条件（8条标准）

### 标准详解

**标准1：股价高于150日和200日均线**
```
C > MA(C,150) AND C > MA(C,200)
```
含义：确保股票处于长期上升趋势中

**标准2：150日均线高于200日均线**
```
MA(C,150) > MA(C,200)
```
含义：确认中期趋势强于长期趋势

**标准3：200日均线上涨至少1个月**
```
EVERY(MA(C,200) >= REF(MA(C,200),1), 20)
```
含义：长期趋势已经转向向上

**标准4：50日均线高于150日和200日均线**
```
MA(C,50) > MA(C,150) AND MA(C,50) > MA(C,200)
```
含义：短期趋势确认向上

**标准5：股价比52周最低点高出25%以上**
```
C / LLV(L,250) > 1.25
```
含义：股票已经从底部上涨，有上涨动能

**标准6：股价在52周高点的25%以内**
```
C / HHV(H,250) > 0.75
```
含义：股票接近或正在创新高

**标准7：相对强度（RS/RPS）排名不低于70**
```
RPS250 >= 70
```
含义：股票表现优于市场大部分股票

**标准8：股价在50日均线之上**
```
C > MA(C,50)
```
含义：短期趋势确认

## 通达信选股公式

### 完整版（含RPS）

```pascal
{第二阶段选股公式}
EJD1:=IF(MA(C,50)>MA(C,150),1,0);{50日均线高于150日均线}
EJD2:=IF(MA(C,150)>MA(C,200),1,0);{150日均线高于200日均线}
EJD3:=IF(C>MA(C,50),1,0);{当前价格高于50日均线}
EJD4:=IF(EVERY(MA(C,200)>REF(MA(C,200),5),20),1,0);{200日均线至少上涨了1个月}
EJD5:=IF(C/LLV(L,250)>1.3,1,0);{当前股价比最近一年最低股价至少高30%}
EJD6:=IF(C/HHV(H,250)>0.75,1,0);{当前价格至少处在最近一年最高价的75%以内}
EJD7:=IF(RPS250>=70,1,0);{相对动力排名不低于70}

EJD1 AND EJD2 AND EJD3 AND EJD4 AND EJD5 AND EJD6;
```

### 简化版（不含RPS）

```pascal
N:=20;
A1:=C>MA(C,150) AND C>MA(C,200);
A2:=MA(C,150) > MA(C,200);
A3:=EVERY(MA(C,200)>=REF(MA(C,200),1),N);
A4:=MA(C,50) > MA(C,150) AND MA(C,50) > MA(C,200);
A5:=C>MA(C,50);
A6:=C/LLV(C,250)>1.3;
A7:=C>HHV(C,250)*0.75;

A1 AND A2 AND A3 AND A4 AND A5 AND A6 AND A7;
```

## Python实现

### 数据库查询版本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段选股策略
根据Mark Minervini的8条标准筛选处于第二阶段的股票
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

DB_PATH = Path.home() / '.vntrader' / 'database.db'

def get_stock_data(conn, symbol, days=300):
    """获取股票历史数据"""
    query = """
    SELECT 
        datetime as trade_date,
        open_price as open,
        high_price as high,
        low_price as low,
        close_price as close,
        volume
    FROM dbbardata
    WHERE symbol = ? AND interval = 'd'
    ORDER BY datetime DESC
    LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(symbol, days))
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df

def check_stage2(df, rps_threshold=70):
    """
    检查股票是否处于第二阶段
    
    返回: (is_stage2, details)
    """
    if len(df) < 250:
        return False, {}
    
    # 计算均线
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma150'] = df['close'].rolling(window=150).mean()
    df['ma200'] = df['close'].rolling(window=200).mean()
    
    # 获取最新数据
    latest = df.iloc[-1]
    close = latest['close']
    ma50 = latest['ma50']
    ma150 = latest['ma150']
    ma200 = latest['ma200']
    
    # 检查条件
    conditions = {}
    
    # 条件1: 股价高于150日和200日均线
    conditions['c1'] = close > ma150 and close > ma200
    
    # 条件2: 150日均线高于200日均线
    conditions['c2'] = ma150 > ma200
    
    # 条件3: 200日均线上涨至少1个月（20个交易日）
    ma200_20days = df['ma200'].iloc[-20:]
    conditions['c3'] = all(ma200_20days.diff().dropna() >= 0)
    
    # 条件4: 50日均线高于150日和200日均线
    conditions['c4'] = ma50 > ma150 and ma50 > ma200
    
    # 条件5: 股价高于50日均线
    conditions['c5'] = close > ma50
    
    # 条件6: 股价比52周最低点高出25%以上
    low_250 = df['low'].rolling(window=250).min().iloc[-1]
    conditions['c6'] = close / low_250 > 1.25
    
    # 条件7: 股价在52周高点的25%以内
    high_250 = df['high'].rolling(window=250).max().iloc[-1]
    conditions['c7'] = close / high_250 > 0.75
    
    # 所有条件满足
    is_stage2 = all(conditions.values())
    
    details = {
        'close': close,
        'ma50': ma50,
        'ma150': ma150,
        'ma200': ma200,
        'low_250': low_250,
        'high_250': high_250,
        'position_ratio': close / high_250,
        'conditions': conditions
    }
    
    return is_stage2, details

def screen_stage2():
    """筛选处于第二阶段的股票"""
    conn = sqlite3.connect(DB_PATH)
    
    # 获取所有股票
    query = "SELECT DISTINCT symbol FROM dbbardata WHERE interval = 'd'"
    stocks = pd.read_sql_query(query, conn)
    
    results = []
    
    for symbol in stocks['symbol']:
        df = get_stock_data(conn, symbol, days=300)
        is_stage2, details = check_stage2(df)
        
        if is_stage2:
            results.append({
                'symbol': symbol,
                'close': details['close'],
                'ma50': details['ma50'],
                'ma150': details['ma150'],
                'ma200': details['ma200'],
                'position_ratio': details['position_ratio']
            })
    
    conn.close()
    
    return pd.DataFrame(results)

if __name__ == '__main__':
    results = screen_stage2()
    print(f"筛选结果：{len(results)}只股票")
    print(results)
```

## 使用建议

### 买入时机
1. 第二阶段初期进入最佳
2. 回调至50日均线附近买入
3. 突破前高时加仓

### 卖出时机
1. 进入第三阶段时卖出
2. 跌破50日均线时减仓
3. 跌破200日均线时清仓

### 风险控制
1. 单只股票仓位不超过10%
2. 设置止损位：-8%到-10%
3. 分散投资：5-10只股票

### 与其他策略组合
1. 第二阶段 + 口袋支点
2. 第二阶段 + 净利润断层
3. 第二阶段 + 月线反转

## 注意事项

1. **不要追高**：避免在第二阶段末期买入
2. **关注成交量**：确认突破有成交量配合
3. **基本面验证**：选择有净利润增长的股票
4. **市场环境**：大盘弱势时减少操作
5. **止损严格**：跌破关键支撑位坚决止损

## 参考资料

- 《股票魔法师》Mark Minervini
- 《股票魔法师2》Mark Minervini
- 陶博士2006公众号
