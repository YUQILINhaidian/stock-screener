# Stock Screener - 选股策略工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Stock Screener 是一个专业的选股策略工具，提供多种经过验证的量化选股策略，帮助用户快速筛选强势股票。

## 策略列表

| 策略 | 适用场景 | 难度 | 推荐度 |
|------|---------|------|--------|
| **月线反转策略** | 中长期投资、捕捉趋势反转 | ⭐⭐⭐ 进阶 | ⭐⭐⭐⭐⭐ |
| **口袋支点策略** | 中短期投资、捕捉突破买点 | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ |
| **第二阶段策略** | 中长期投资、捕捉主升浪 | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ |
| **接近一年新高** | 中长期投资、捕捉突破机会 | ⭐ 简单 | ⭐⭐⭐⭐⭐ |
| **火车头策略** | 中长期投资、波段交易 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ |
| **三线红策略** | 中长期投资、持续强势 | ⭐ 简单 | ⭐⭐⭐ |
| **蓝色钻石策略** | 中期波段、调整买入 | ⭐⭐ 进阶 | ⭐⭐⭐ |

## 策略来源

- **月线反转** - 陶博士2006改进版月线反转6.5
- **口袋支点** - 《像欧奈尔信徒一样交易》Gil Morales & Dr. Chris Kacher
- **第二阶段** - 《股票魔法师》Mark Minervini
- **接近一年新高** - William O'Neil CANSLIM 系统

## 安装

```bash
# 克隆仓库
git clone https://github.com/yinchang06/stock-screener-skill.git

# 复制到 CodeFlicker skills 目录
cp -r stock-screener-skill ~/.codeflicker/skills/stock-screener
```

## 使用方法

### 月线反转策略

```bash
python3 ~/screen_monthly_reversal.py
```

### 口袋支点策略

```bash
python3 ~/screen_pocket_pivot.py
```

### 第二阶段策略

```bash
python3 ~/screen_stage2.py
```

### 接近一年新高策略

```bash
python3 ~/screen_near_year_high.py
```

## 目录结构

```
stock-screener/
├── SKILL.md                    # 主文档
├── README.md                   # 说明文档
├── references/                 # 策略详解
│   ├── monthly-reversal-guide.md
│   ├── pocket-pivot-guide.md
│   ├── stage2-guide.md
│   ├── near-high-guide.md
│   ├── train-strategy-guide.md
│   └── strategy-comparison.md
├── scripts/                    # 执行脚本
│   ├── monthly-reversal-screen.sh
│   ├── pocket-pivot-screen.sh
│   ├── stage2-screen.sh
│   ├── near-year-high.sh
│   └── quick-screen.sh
└── examples/                   # 使用示例
    ├── monthly-reversal-examples.md
    ├── pocket-pivot-examples.md
    ├── stage2-examples.md
    └── near-high-examples.md
```

## 筛选条件

### 月线反转6.5（7条标准）
1. RPS强度：RPS50>87 OR RPS120>90
2. 结构紧凑：50日低点>200日低点 或 30日低点>120日低点
3. 创新高：10天内曾创80日新高 或 当天创50日新高
4. 均线支撑：收盘价站上20日线和200日线
5. 均线靠近：45天内至少有一次低于200日线
6. 均线趋势：120日线或200日线呈上升趋势
7. 价格位置：接近120日或250日新高

### 口袋支点（9条标准）
1. RPS强度：RPS250>=87 OR RPS120>=90 OR RPS50>=90
2. 成交量放大：创10日最高成交金额/涨停/2倍成交
3. 均线突破：创90/100/120日新高
4. 结构紧凑：15日低点不是50日低点
5. 调整幅度限制：最大下跌不超过46%
6. 涨幅要求：当日涨幅>=5%
7. 换手率稳定：两天平均换手不高于15%
8. 价格偏离限制：偏离均线幅度限制

### 第二阶段（8条标准）
1. 50日均线高于150日均线
2. 150日均线高于200日均线
3. 当前价格高于50日均线
4. 200日均线至少上涨了1个月
5. 当前股价比最近一年最低股价至少高30%
6. 当前价格至少处在最近一年最高价的75%以内
7. RPS250不低于70

## 参考资料

- [陶博士2006公众号](https://mp.weixin.qq.com/s/JnTeY7T0rPcWXE3NeHRb7Q)
- [股票魔法师](https://www.amazon.com/Trade-Like-Stock-Market-Wizard/dp/0071807225)
- [像欧奈尔信徒一样交易](https://www.amazon.com/Trade-O'Neil-Disciples-Gil-Morales/dp/0470616539)

## License

MIT License

## Author

yinchang06
