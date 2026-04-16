# 股票池自动化管理系统

## 📚 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [脚本说明](#脚本说明)
- [定时任务](#定时任务)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

---

## 🎯 功能特性

✅ **自动化数据更新** - 每日自动更新VNPy数据中心和股票池价格  
✅ **批量报告生成** - 一键生成所有股票池的可视化报告（HTML/PNG/PDF）  
✅ **定时任务支持** - 内置crontab配置，无需手动运行  
✅ **多格式输出** - 支持HTML网页、PNG截图、PDF报告  
✅ **智能交易日识别** - 自动跳过周末和节假日  
✅ **完整日志记录** - 所有操作详细记录，便于排查问题  

---

## 🚀 快速开始

### 1. 一次性设置

```bash
# 赋予脚本执行权限
cd ~/.agents/skills/stock-screener/scripts
chmod +x *.sh

# 安装定时任务
./setup_crontab.sh install
```

### 2. 手动运行测试

```bash
# 更新所有股票池并生成报告（完整模式）
./update_all_pools.sh

# 快速模式（跳过PDF）
./update_all_pools.sh --fast

# 仅生成HTML
./update_all_pools.sh --html-only
```

### 3. 查看报告

```bash
# 打开今日报告目录
open ~/.vntrader/reports/$(date +%Y-%m-%d)

# 查看汇总报告
cat ~/.vntrader/reports/$(date +%Y-%m-%d)/summary.txt
```

---

## 📜 脚本说明

### 1. `update_all_pools.sh` - 股票池批量更新

**功能**：更新所有股票池并生成可视化报告

**用法**：
```bash
./update_all_pools.sh              # 完整模式（HTML+PNG+PDF）
./update_all_pools.sh --fast       # 快速模式（HTML+PNG）
./update_all_pools.sh --html-only  # 仅HTML
```

**输出**：
- `~/.vntrader/reports/YYYY-MM-DD/` - 每日报告目录
- `~/.vntrader/reports/YYYY-MM-DD/summary.txt` - 汇总报告
- `~/.vntrader/logs/pool_update_YYYY-MM-DD.log` - 详细日志

**处理流程**：
1. 自动检测 `~/.vntrader/stock_pools/` 下的所有股票池
2. 调用 `stock_pool_tracker.py` 更新价格
3. 使用 `gstack_data_manager.py` 生成报告
4. 生成汇总统计信息

---

### 2. `daily_update.sh` - 每日数据更新

**功能**：更新VNPy数据中心 + 股票池 + 生成报告

**用法**：
```bash
./daily_update.sh              # 完整更新
./daily_update.sh --quick      # 快速模式（跳过数据中心）
./daily_update.sh --pools-only # 仅股票池
./daily_update.sh --data-only  # 仅数据中心
```

**输出**：
- `~/.vntrader/logs/daily_update_YYYY-MM-DD.log` - 每日日志

**智能特性**：
- ✅ 自动识别交易日（周末自动跳过数据中心更新）
- ✅ 失败自动通知（macOS Notification Center）
- ✅ 链式调用 `update_all_pools.sh --fast`

---

### 3. `setup_crontab.sh` - 定时任务管理

**功能**：一键安装/更新/卸载定时任务

**用法**：
```bash
./setup_crontab.sh install    # 安装定时任务
./setup_crontab.sh status     # 查看当前状态
./setup_crontab.sh test       # 测试运行
./setup_crontab.sh uninstall  # 卸载定时任务
```

**默认定时计划**：
```
📅 每个交易日（周一至周五）:
   ├─ 09:00  快速更新股票池
   └─ 15:30  完整更新（数据中心 + 报告）

📊 每周日:
   └─ 20:00  生成完整周报（含PDF）
```

**修改时间**：
编辑 `setup_crontab.sh` 中的 `CRON_JOBS` 数组，然后重新运行 `install`

---

## ⏰ 定时任务

### 安装定时任务

```bash
cd ~/.agents/skills/stock-screener/scripts
./setup_crontab.sh install
```

### 查看当前配置

```bash
./setup_crontab.sh status
```

### 手动触发测试

```bash
# 测试快速模式
./setup_crontab.sh test

# 查看日志
tail -f ~/.vntrader/logs/cron_daily.log
```

### 卸载定时任务

```bash
./setup_crontab.sh uninstall
```

---

## 💡 使用示例

### 示例1：每日早盘前快速查看

```bash
# 9:00 定时任务会自动执行，或手动运行：
./daily_update.sh --quick

# 查看报告
open ~/.vntrader/reports/$(date +%Y-%m-%d)/monthly_reversal_pool.png
```

### 示例2：周末生成完整周报

```bash
# 生成所有股票池的PDF报告
./update_all_pools.sh

# 批量打开所有PDF
open ~/.vntrader/reports/$(date +%Y-%m-%d)/*.pdf
```

### 示例3：单独查看某个股票池

```bash
# 使用gstack_data_manager直接生成
cd ~/.agents/skills/stock-screener
python3 python/gstack/gstack_data_manager.py --pool monthly_reversal_pool --screenshot
```

### 示例4：对比多个股票池

```bash
# 生成所有报告
./update_all_pools.sh --fast

# 使用浏览器批量打开
open ~/.vntrader/reports/$(date +%Y-%m-%d)/*.html
```

---

## 🛠️ 常见问题

### Q1: 定时任务没有执行怎么办？

**检查步骤**：
```bash
# 1. 确认crontab已安装
crontab -l | grep daily_update

# 2. 查看系统日志
tail -50 /var/mail/$USER

# 3. 检查脚本权限
ls -l ~/.agents/skills/stock-screener/scripts/*.sh

# 4. 手动测试
./setup_crontab.sh test
```

### Q2: 报告生成失败

**可能原因**：
- gstack browse未启动：手动运行一次 `~/.codeflicker/skills/gstack/browse/dist/browse status`
- 股票池数据不完整：检查 `~/.vntrader/stock_pools/*.json`
- 依赖缺失：检查Python依赖 `pip3 install -r requirements.txt`

**解决方法**：
```bash
# 查看详细日志
tail -100 ~/.vntrader/logs/pool_update_$(date +%Y-%m-%d).log

# 单独测试某个池子
python3 python/gstack/gstack_data_manager.py --pool monthly_reversal_pool -v
```

### Q3: 如何只更新特定股票池？

**方法1**：直接使用gstack_data_manager
```bash
python3 python/gstack/gstack_data_manager.py --pool YOUR_POOL_NAME --screenshot
```

**方法2**：修改update_all_pools.sh
```bash
# 在get_all_pools函数中添加过滤条件
get_all_pools() {
    find "$POOL_DIR" -name "*.json" | grep "monthly_reversal" | ...
}
```

### Q4: 如何添加新股票池？

**步骤**：
1. 使用选股脚本生成新池子（如 `screen_stage2.py`）
2. 池子自动保存到 `~/.vntrader/stock_pools/`
3. 下次运行 `update_all_pools.sh` 会自动识别

**验证**：
```bash
# 查看所有池子
ls -lh ~/.vntrader/stock_pools/*.json

# 测试新池子
python3 stock_pool_tracker.py update --name YOUR_NEW_POOL
```

### Q5: 定时任务时间如何调整？

**编辑 setup_crontab.sh**：
```bash
# 找到 CRON_JOBS 数组
CRON_JOBS=(
    # 格式: 分 时 日 月 周
    "30 15 * * 1-5 ..."  # 改为你想要的时间
)

# 重新安装
./setup_crontab.sh update
```

### Q6: 如何查看历史报告？

```bash
# 列出所有日期
ls -d ~/.vntrader/reports/*/

# 打开特定日期
open ~/.vntrader/reports/2026-04-09/

# 对比不同日期的同一股票池
diff ~/.vntrader/reports/2026-04-09/summary.txt \
     ~/.vntrader/reports/2026-04-10/summary.txt
```

---

## 📊 目录结构

```
~/.vntrader/
├── stock_pools/              # 股票池JSON文件
│   ├── monthly_reversal_pool.json
│   ├── first_limit_up_pool.json
│   └── ...
├── reports/                  # 每日报告
│   ├── 2026-04-09/
│   │   ├── monthly_reversal_pool.html
│   │   ├── monthly_reversal_pool.png
│   │   ├── monthly_reversal_pool.pdf
│   │   └── summary.txt
│   └── 2026-04-10/
│       └── ...
└── logs/                     # 日志文件
    ├── cron_daily.log
    ├── cron_morning.log
    ├── daily_update_2026-04-10.log
    └── pool_update_2026-04-10.log

~/.agents/skills/stock-screener/
├── python/gstack/
│   ├── gstack_data_manager.py  # 数据管理器
│   └── gstack_data_fetcher.py  # (已废弃)
└── scripts/
    ├── update_all_pools.sh     # 批量更新
    ├── daily_update.sh         # 每日更新
    └── setup_crontab.sh        # 定时任务
```

---

## 🎨 报告示例

**HTML看板特性**：
- ✅ 响应式设计（支持移动端）
- ✅ Tailwind CSS样式
- ✅ 收益率红绿配色（涨红跌绿）
- ✅ 按收益率排序
- ✅ 统计卡片（总数/平均收益/胜率/盈利数）

**查看报告**：
```bash
# 在浏览器打开
open ~/.vntrader/reports/$(date +%Y-%m-%d)/monthly_reversal_pool.html

# 快速预览PNG
open ~/.vntrader/reports/$(date +%Y-%m-%d)/monthly_reversal_pool.png
```

---

## 📞 支持

**问题反馈**：
- 查看日志：`~/.vntrader/logs/`
- 详细模式：添加 `-v` 或 `--verbose` 参数

**脚本位置**：
- `~/.agents/skills/stock-screener/scripts/`
- `~/.agents/skills/stock-screener/python/gstack/`

**相关文档**：
- gstack文档：`~/.codeflicker/skills/gstack/SKILL.md`
- stock-screener文档：`~/.agents/skills/stock-screener/SKILL.md`

---

## 🔄 更新日志

### v1.0.0 (2026-04-10)
- ✨ 初始版本发布
- ✅ 支持批量更新所有股票池
- ✅ 生成HTML/PNG/PDF报告
- ✅ 集成gstack浏览器自动化
- ✅ crontab定时任务支持
- ✅ 智能交易日识别

---

**Happy Trading! 📈**
