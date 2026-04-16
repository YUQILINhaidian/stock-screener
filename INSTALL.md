# 安装指南

本文档帮助你将 Stock Screener skill 分享给其他人使用。

---

## 方式一：GitHub 克隆（推荐）

### 发布者操作

#### 1. 推送到 GitHub

```bash
cd ~/.agents/skills/stock-screener

# 提交所有更改
git add .
git commit -m "feat: 重组 skill 结构，优化文档"
git push origin main
```

#### 2. 分享仓库地址

告诉其他人你的仓库地址，例如：
```
https://github.com/YUQILINhaidian/stock-screener
```

---

### 安装者操作

#### 1. 克隆 Skill

**方法 A：在 CodeFlicker 中让 AI 帮你克隆**
```
从 https://github.com/YUQILINhaidian/stock-screener 克隆 skill
```

**方法 B：手动克隆**
```bash
cd ~/.agents/skills
git clone https://github.com/YUQILINhaidian/stock-screener.git
```

#### 2. 安装依赖

```bash
# 进入 skill 目录
cd ~/.agents/skills/stock-screener

# 运行安装脚本
bash scripts/install.sh
```

#### 3. 验证安装

```bash
# 检查数据新鲜度
python3 ~/.agents/skills/stock-screener/python/check_db_freshness.py
```

---

## 方式二：打包分享

### 发布者操作

```bash
# 打包（排除 .git 目录）
cd ~/.agents/skills
zip -r stock-screener.zip stock-screener/ -x "*.git*"
```

分享 `stock-screener.zip` 给其他人。

### 安装者操作

```bash
# 解压
unzip stock-screener.zip -d ~/.agents/skills/

# 安装依赖
cd ~/.agents/skills/stock-screener
bash scripts/install.sh
```

---

## 依赖要求

### 必需依赖

| 依赖 | 用途 | 安装命令 |
|------|------|----------|
| Python 3.9+ | 运行时 | 系统自带 |
| pandas | 数据处理 | `pip install pandas` |
| vnpy | 交易框架 | `pip install vnpy` |
| baostock | 数据源 | `pip install baostock` |
| akshare | 数据源 | `pip install akshare` |

### 一键安装依赖

```bash
pip install pandas numpy vnpy baostock akshare mplfinance
```

---

## 数据库配置

Stock Screener 依赖 VNPy 的数据库，需要：

### 1. 初始化 VNPy 数据库

```python
# 在 Python 中运行一次
from vnpy.trader.database import get_database
db = get_database()
print("数据库已初始化")
```

### 2. 更新股票数据

首次使用需要下载历史数据：

```bash
# 下载 K 线数据（约 5-10 分钟）
python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py

# 计算 RPS 指标（约 1-2 分钟）
python3 ~/.agents/skills/stock-screener/python/update_daily_data.py
```

---

## 目录结构说明

安装后的目录结构：

```
~/.agents/skills/stock-screener/
├── SKILL.md                    # 入口文档（AI 调用）
├── README.md                   # 项目说明
├── INSTALL.md                  # 本文档
│
├── python/                     # Python 脚本
│   ├── screen_monthly_reversal.py
│   ├── screen_pocket_pivot.py
│   ├── update_kline_from_baostock.py
│   └── ...
│
├── scripts/                    # Shell 脚本
│   ├── install.sh              # 安装脚本
│   └── *.sh                    # 其他脚本
│
├── references/strategies/      # 策略详解
└── examples/                   # 使用示例
```

---

## 常见问题

### Q: 提示找不到 vnpy 模块？

```bash
pip install vnpy
```

### Q: 数据库连接失败？

确保 VNPy 数据库已初始化：
```python
from vnpy.trader.database import get_database
get_database()
```

### Q: RPS 计算报错？

需要至少 250 天的历史数据，运行：
```bash
python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py
```

---

## 版本更新

```bash
cd ~/.agents/skills/stock-screener
git pull origin main
```
