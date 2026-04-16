# 数据库配置说明

Stock Screener 依赖 VNPY 的数据库来存储股票 K 线数据和基本面数据。

## 数据库文件

本项目需要以下数据库文件：

| 数据库文件 | 大小 | 说明 |
|-----------|------|------|
| `database.db` | ~1GB | K线数据、RPS数据等 |
| `fundamental.db` | ~660KB | 基本面数据 |

## 数据库位置

数据库文件应放置在 VNPY 的数据目录：

```
~/.vntrader/
├── database.db      # 主数据库
├── fundamental.db   # 基本面数据库
├── stock_pools/     # 股票池数据
├── screen_results/  # 筛选结果
└── charts/          # K线图表
```

## 获取数据库文件

### 方式 1：从分享者获取（推荐）

由于数据库文件较大，建议通过以下方式获取：

1. **云盘下载**：分享者可上传到网盘（百度网盘、阿里云盘等）
2. **本地复制**：直接从已配置好的电脑复制

下载后将文件放置到 `~/.vntrader/` 目录。

### 方式 2：从头构建数据库

如果没有现成的数据库文件，可以通过以下步骤构建：

#### 1. 安装 VNPY

```bash
pip install vnpy
```

#### 2. 创建数据目录

```bash
mkdir -p ~/.vntrader/stock_pools
mkdir -p ~/.vntrader/screen_results
mkdir -p ~/.vntrader/charts
mkdir -p ~/.vntrader/kline_charts
```

#### 3. 初始化数据库

```bash
# 运行数据初始化脚本（首次运行会创建数据库表）
python3 <skill_directory>/python/update_kline_from_baostock.py
```

#### 4. 下载历史数据

```bash
# 下载所有A股日线数据（耗时约30分钟-1小时）
python3 <skill_directory>/python/update_kline_from_baostock.py

# 计算 RPS 指标
python3 <skill_directory>/python/update_daily_data.py
```

### 方式 3：使用 BaoStock 数据源

本项目使用 BaoStock 作为数据源，需要先安装：

```bash
pip install baostock
```

数据更新脚本会自动从 BaoStock 获取数据。

## 数据更新

建议每日收盘后更新数据：

```bash
# 检查数据新鲜度
python3 <skill_directory>/python/check_db_freshness.py

# 更新K线数据
python3 <skill_directory>/python/update_kline_from_baostock.py

# 重新计算RPS
python3 <skill_directory>/python/update_daily_data.py
```

## 数据库结构

### database.db 主要表

| 表名 | 说明 |
|------|------|
| `db_bar_data` | K线数据（日K、周K、月K） |
| `rps_data` | RPS 相对强度指标 |
| `stock_info` | 股票基本信息 |

### fundamental.db 主要表

| 表名 | 说明 |
|------|------|
| `fundamental_data` | 基本面数据 |

## 常见问题

### Q: 数据库文件太大怎么办？

A: 数据库包含所有A股历史数据，体积较大是正常的。如果磁盘空间有限，可以：
- 定期清理旧数据
- 只保留需要的时间段数据

### Q: 数据更新失败怎么办？

A: 检查以下项目：
1. 网络连接是否正常
2. BaoStock 服务是否可用
3. 数据库文件是否有写入权限

### Q: 如何备份数据库？

A: 直接复制数据库文件即可：

```bash
cp ~/.vntrader/database.db ~/.vntrader/database_backup_$(date +%Y%m%d).db
```

## 配置验证

运行以下命令验证数据库配置是否正确：

```bash
# 检查数据库文件是否存在
ls -la ~/.vntrader/*.db

# 检查数据新鲜度
python3 <skill_directory>/python/check_db_freshness.py
```

如果一切正常，`check_db_freshness.py` 会显示数据的最新日期。
