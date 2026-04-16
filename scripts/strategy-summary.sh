#!/bin/bash
# 策略汇总分析脚本
#
# 用法:
#   bash ~/.codeflicker/skills/stock-screener/scripts/strategy-summary.sh
#   bash ~/.codeflicker/skills/stock-screener/scripts/strategy-summary.sh --html
#   bash ~/.codeflicker/skills/stock-screener/scripts/strategy-summary.sh -c --html
#

echo "================================"
echo " 策略筛选结果汇总分析"
echo "================================"
echo ""

# 运行策略汇总
python3 ~/strategy_summary.py "$@"

# 如果生成了HTML报告，打开它
if [[ "$*" == *"--html"* ]]; then
    echo ""
    echo ">>> 打开HTML报告..."
    latest_html=$(ls -t ~/.vntrader/strategy_summary/summary_*.html 2>/dev/null | head -1)
    if [ -n "$latest_html" ]; then
        open "$latest_html"
    fi
fi
