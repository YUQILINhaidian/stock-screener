#!/bin/bash
# 首次涨停&一线红选股策略筛选脚本
#
# 用法:
#   bash ~/.codeflicker/skills/stock-screener/scripts/first-limit-up-screen.sh
#
# 输出:
#   ~/.vntrader/first_limit_up_YYYYMMDD_HHMMSS.csv
#

echo "=================================="
echo " 首次涨停&一线红选股策略"
echo "=================================="
echo ""
echo "逻辑: RPS≥90 + 涨停 + 一线红 + 首次触发"
echo ""

# 1. 检查数据新鲜度
echo ">>> 检查数据新鲜度..."
python3 ~/check_db_freshness.py 2>&1 | tail -3
echo ""

# 2. 运行首次涨停&一线红策略
echo ">>> 运行首次涨停&一线红策略..."
python3 ~/first_limit_up_strategy.py

echo ""
echo ">>> 完成！"
echo ">>> 最新结果: $(ls -t ~/.vntrader/first_limit_up_*.csv 2>/dev/null | head -1)"
