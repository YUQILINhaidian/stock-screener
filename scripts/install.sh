#!/bin/bash
# Stock Screener 一键安装脚本

set -e

echo "=========================================="
echo "  Stock Screener 依赖安装脚本"
echo "=========================================="

# 检测 Python 版本
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 未找到 Python，请先安装 Python 3.9+"
    exit 1
fi

echo ""
echo "✅ 使用 Python: $($PYTHON_CMD --version)"

# 安装 Python 依赖
echo ""
echo "📦 安装 Python 依赖..."
$PYTHON_CMD -m pip install --user pandas numpy vnpy baostock akshare mplfinance requests

# 创建必要目录
echo ""
echo "📁 创建必要目录..."
mkdir -p ~/.vntrader
mkdir -p ~/.vntrader/screen_results
mkdir -p ~/.vntrader/charts
mkdir -p ~/.vntrader/reports
mkdir -p ~/.vntrader/stock_pools
mkdir -p ~/.vntrader/logs

# 检查 VNPy 数据库
echo ""
echo "🔍 检查 VNPy 数据库..."
$PYTHON_CMD -c "
try:
    from vnpy.trader.database import get_database
    db = get_database()
    print('✅ VNPy 数据库已配置')
except Exception as e:
    print('⚠️  VNPy 数据库初始化:', str(e))
    print('请运行: python -c \"from vnpy.trader.database import get_database; get_database()\"')
"

# 检查数据
echo ""
echo "📊 检查股票数据..."
STOCK_COUNT=$($PYTHON_CMD -c "
try:
    import sqlite3
    conn = sqlite3.connect('$HOME/.vntrader/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM dbbardata')
    count = cursor.fetchone()[0]
    print(count)
except:
    print(0)
" 2>/dev/null || echo "0")

if [ "$STOCK_COUNT" -gt 1000 ]; then
    echo "✅ 已有 $STOCK_COUNT 只股票数据"
else
    echo "⚠️  股票数据不足（$STOCK_COUNT 只），请运行以下命令更新："
    echo "   python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py"
fi

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 更新股票数据（首次使用必须）："
echo "   python3 ~/.agents/skills/stock-screener/python/update_kline_from_baostock.py"
echo "   python3 ~/.agents/skills/stock-screener/python/update_daily_data.py"
echo ""
echo "2. 运行选股策略："
echo "   python3 ~/.agents/skills/stock-screener/python/screen_monthly_reversal.py"
echo ""
echo "3. 在 CodeFlicker 中使用："
echo "   直接说 '选股' 或 '运行月线反转策略'"
echo ""
