#!/bin/bash
# 圆弧底选股策略筛选脚本
#
# 用法:
#   bash ~/.codeflicker/skills/stock-screener/scripts/arc-bottom-screen.sh
#
# 输出:
#   ~/.vntrader/arc_bottom_YYYYMMDD_HHMMSS.csv
#

echo "=============================="
echo " 圆弧底选股策略"
echo "=============================="
echo ""
echo "逻辑: 短线30天低位蛰伏后首穿中线 + 长中线收敛 + 仍在底部区域"
echo ""

# 1. 检查数据新鲜度
echo ">>> 检查数据新鲜度..."
python3 ~/check_db_freshness.py 2>&1 | tail -3
echo ""

# 2. 运行圆弧底策略
echo ">>> 运行圆弧底策略..."
python3 ~/arc_bottom_strategy.py

echo ""
echo ">>> 完成！"
echo ">>> 最新结果: $(ls -t ~/.vntrader/arc_bottom_*.csv 2>/dev/null | head -1)"
