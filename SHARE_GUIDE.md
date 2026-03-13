# Stock Screener Skill 分享指南

## 📦 分享方式

有两种方式可以让其他人使用这个skill：

---

## 方式一：GitHub分享（推荐）

### 步骤1：创建GitHub仓库

1. 登录 GitHub (https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `stock-screener`
   - Description: `专业的选股策略工具 - 提供多种量化选股策略`
   - 选择 Public 或 Private
4. 点击 "Create repository"

### 步骤2：推送代码到GitHub

```bash
# 进入skill目录
cd ~/.codeflicker/skills/stock-screener

# 添加远程仓库（替换为你的用户名）
git remote add origin https://github.com/yinchang06/stock-screener.git

# 添加所有文件
git add .

# 提交更改
git commit -m "feat: 添加完整的选股策略工具"

# 推送到GitHub
git push -u origin main
```

### 步骤3：其他人安装

其他用户可以通过以下命令安装：

```bash
# 方法1: 使用skill-manager克隆
# 在CodeFlicker中告诉AI:
"从 https://github.com/yinchang06/stock-screener 克隆skill"

# 方法2: 手动安装
cd ~/.codeflicker/skills/
git clone https://github.com/yinchang06/stock-screener.git
```

---

## 方式二：文件打包分享

### 步骤1：打包skill

```bash
# 创建zip包
cd ~/.codeflicker/skills/
zip -r stock-screener.zip stock-screener/
```

### 步骤2：分享zip文件

- 通过网盘、邮件等方式分享 `stock-screener.zip`

### 步骤3：其他人安装

```bash
# 解压到skill目录
unzip stock-screener.zip -d ~/.codeflicker/skills/
```

---

## 📋 依赖说明

其他用户安装后，还需要安装以下依赖：

### 1. Python依赖

```bash
pip install pandas numpy vnpy baostock akshare
```

### 2. 数据库配置

```bash
# 确保VNPY数据库已配置
# 数据目录: ~/.vntrader/
```

### 3. 策略脚本

以下脚本需要放在用户主目录：

```
~/train_daily_strategy.py        # 火车头策略基类
~/train_daily_advanced_strategy.py  # 火车头高级策略
~/blue_diamond_strategy.py      # 蓝色钻石策略
~/pocket_pivot_strategy.py      # 口袋支点策略
~/arc_bottom_strategy.py        # 圆弧底策略
~/screen_monthly_reversal.py    # 月线反转策略
~/screen_three_line_red.py      # 三线红策略
~/sxhcg3_strategy.py           # 顺向火车轨3.0
~/first_limit_up_strategy.py   # 首次涨停策略
~/mid_term_adjustment_strategy.py  # 中期调整策略
```

---

## 🔧 快速设置脚本

创建一个设置脚本供其他用户使用：

```bash
#!/bin/bash
# setup_stock_screener.sh

echo "=== Stock Screener 依赖安装 ==="

# 安装Python依赖
pip install pandas numpy vnpy baostock akshare

# 创建必要目录
mkdir -p ~/.vntrader/stock_pools
mkdir -p ~/.vntrader/screen_results
mkdir -p ~/.vntrader/kline_charts

echo "✅ 安装完成！"
echo "请确保:"
echo "  1. VNPY数据库已配置"
echo "  2. K线数据已更新"
echo "  3. 策略脚本已放置在主目录"
```

---

## 📖 使用文档

分享时建议包含以下文档：

1. **README.md** - Skill概述
2. **USAGE_GUIDE.md** - 使用指南
3. **DEPENDENCIES.md** - 依赖说明
4. **QUICK_START.md** - 快速开始

---

## ⚠️ 注意事项

1. **数据隐私**: 不要分享包含个人交易数据的文件
2. **敏感信息**: 不要分享包含API密钥的配置文件
3. **许可证**: 建议添加LICENSE文件声明使用条款

---

## 🎯 分享检查清单

- [ ] 所有代码已提交到Git
- [ ] README.md 已更新
- [ ] 依赖文档已完善
- [ ] 示例代码可运行
- [ ] 移除了敏感信息
- [ ] 添加了LICENSE文件
