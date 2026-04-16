#!/bin/bash
# 🚀 股票池自动化系统 - 快速启动指南
#
# 首次使用请运行此脚本进行初始化和测试

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🚀 股票池自动化系统 - 快速启动  ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 步骤1: 检查环境
echo -e "${YELLOW}▶ 步骤1: 检查环境...${NC}"
if [ ! -f "$SCRIPT_DIR/update_all_pools.sh" ]; then
    echo "❌ 脚本文件不存在"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 未安装"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"
echo ""

# 步骤2: 赋予执行权限
echo -e "${YELLOW}▶ 步骤2: 设置脚本权限...${NC}"
chmod +x "$SCRIPT_DIR"/*.sh
echo -e "${GREEN}✅ 权限设置完成${NC}"
echo ""

# 步骤3: 测试批量更新（HTML-only模式，快速）
echo -e "${YELLOW}▶ 步骤3: 运行测试（HTML-only模式）...${NC}"
echo "   这将更新所有股票池并生成HTML报告"
echo "   预计耗时: ~30秒"
echo ""

if "$SCRIPT_DIR/update_all_pools.sh" --html-only; then
    echo ""
    echo -e "${GREEN}✅ 测试运行成功！${NC}"
else
    echo ""
    echo -e "❌ 测试失败，请查看日志"
    exit 1
fi

echo ""

# 步骤4: 显示报告
TODAY=$(date +%Y-%m-%d)
REPORT_DIR="$HOME/.vntrader/reports/$TODAY"

echo -e "${YELLOW}▶ 步骤4: 查看生成的报告...${NC}"
echo ""
if [ -d "$REPORT_DIR" ]; then
    echo "📊 报告目录: $REPORT_DIR"
    echo ""
    echo "生成的文件:"
    ls -lh "$REPORT_DIR" | tail -n +2 | awk '{printf "   %s  %s\n", $5, $9}'
    echo ""
    
    # 询问是否打开报告
    read -p "是否在浏览器打开报告？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$REPORT_DIR"/*.html 2>/dev/null || true
    fi
else
    echo "⚠️  报告目录不存在: $REPORT_DIR"
fi

echo ""

# 步骤5: 询问是否安装定时任务
echo -e "${YELLOW}▶ 步骤5: 安装定时任务（可选）${NC}"
echo ""
echo "定时任务将自动:"
echo "   • 每周一至周五 09:00 - 快速更新股票池"
echo "   • 每周一至周五 15:30 - 完整更新（数据+报告）"
echo "   • 每周日 20:00 - 生成完整周报"
echo ""

read -p "是否安装定时任务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$SCRIPT_DIR/setup_crontab.sh" install
else
    echo "跳过定时任务安装"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 初始化完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "📖 常用命令:"
echo ""
echo "  # 更新所有股票池（快速模式）"
echo "  $SCRIPT_DIR/update_all_pools.sh --fast"
echo ""
echo "  # 查看今日报告"
echo "  open ~/.vntrader/reports/\$(date +%Y-%m-%d)/"
echo ""
echo "  # 查看定时任务状态"
echo "  $SCRIPT_DIR/setup_crontab.sh status"
echo ""
echo "  # 查看详细文档"
echo "  cat $SCRIPT_DIR/README.md"
echo ""
echo -e "${GREEN}Happy Trading! 📈${NC}"
