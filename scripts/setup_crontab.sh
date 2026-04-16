#!/bin/bash
# Crontab 定时任务配置脚本
#
# 功能: 一键安装/更新/卸载股票数据更新的定时任务
#
# 使用:
#   ./setup_crontab.sh install   # 安装定时任务
#   ./setup_crontab.sh update    # 更新定时任务配置
#   ./setup_crontab.sh uninstall # 卸载定时任务
#   ./setup_crontab.sh status    # 查看当前配置

set -e

SCRIPT_DIR="$HOME/.agents/skills/stock-screener/scripts"
DAILY_UPDATE_SCRIPT="$SCRIPT_DIR/daily_update.sh"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============ 定时任务配置 ============
# 可根据需要修改时间

CRON_JOBS=(
    # 每个交易日15:30（收盘后）更新数据并生成报告
    "30 15 * * 1-5 $DAILY_UPDATE_SCRIPT >> $HOME/.vntrader/logs/cron_daily.log 2>&1"
    
    # 每个交易日9:00（开盘前）快速更新股票池
    "0 9 * * 1-5 $DAILY_UPDATE_SCRIPT --quick >> $HOME/.vntrader/logs/cron_morning.log 2>&1"
    
    # 每周日20:00生成完整报告（含PDF）
    "0 20 * * 0 $SCRIPT_DIR/update_all_pools.sh >> $HOME/.vntrader/logs/cron_weekly.log 2>&1"
)

# ============ 检查脚本是否存在 ============
check_scripts() {
    if [ ! -f "$DAILY_UPDATE_SCRIPT" ]; then
        print_error "daily_update.sh 不存在: $DAILY_UPDATE_SCRIPT"
        exit 1
    fi
    
    if [ ! -x "$DAILY_UPDATE_SCRIPT" ]; then
        print_warning "daily_update.sh 没有执行权限，正在添加..."
        chmod +x "$DAILY_UPDATE_SCRIPT"
        chmod +x "$SCRIPT_DIR/update_all_pools.sh"
    fi
    
    print_success "脚本检查通过"
}

# ============ 备份现有crontab ============
backup_crontab() {
    local backup_file="$HOME/.crontab_backup_$(date +%Y%m%d_%H%M%S)"
    
    if crontab -l > /dev/null 2>&1; then
        crontab -l > "$backup_file"
        print_success "已备份现有crontab到: $backup_file"
    else
        print_info "当前没有crontab配置"
    fi
}

# ============ 安装定时任务 ============
install_crontab() {
    print_header "安装定时任务"
    
    check_scripts
    backup_crontab
    
    # 获取现有crontab
    local temp_cron=$(mktemp)
    crontab -l > "$temp_cron" 2>/dev/null || true
    
    # 添加新任务（先删除旧的，避免重复）
    sed -i '' '/stock-screener\/scripts\|daily_update\.sh\|update_all_pools\.sh/d' "$temp_cron"
    
    # 添加注释和任务
    cat >> "$temp_cron" << 'EOF'

# ============ 股票数据自动更新任务 ============
# 由 setup_crontab.sh 自动生成
# 修改时间请编辑 setup_crontab.sh 后重新运行
EOF
    
    for job in "${CRON_JOBS[@]}"; do
        echo "$job" >> "$temp_cron"
    done
    
    # 安装新crontab
    crontab "$temp_cron"
    rm "$temp_cron"
    
    print_success "定时任务安装成功！"
    echo ""
    show_schedule
}

# ============ 卸载定时任务 ============
uninstall_crontab() {
    print_header "卸载定时任务"
    
    backup_crontab
    
    # 获取现有crontab
    local temp_cron=$(mktemp)
    crontab -l > "$temp_cron" 2>/dev/null || true
    
    # 删除相关任务
    sed -i '' '/stock-screener\/scripts\|daily_update\.sh\|update_all_pools\.sh/d' "$temp_cron"
    sed -i '' '/股票数据自动更新任务/d' "$temp_cron"
    
    # 更新crontab
    crontab "$temp_cron"
    rm "$temp_cron"
    
    print_success "定时任务已卸载"
}

# ============ 显示任务计划 ============
show_schedule() {
    print_header "定时任务计划"
    
    echo ""
    echo "📅 每个交易日（周一至周五）:"
    echo "   ├─ 09:00  快速更新股票池（使用前一日数据）"
    echo "   └─ 15:30  完整更新（数据中心 + 股票池 + 报告）"
    echo ""
    echo "📊 每周日:"
    echo "   └─ 20:00  生成完整周报（含PDF）"
    echo ""
    echo "📂 报告输出:"
    echo "   └─ $HOME/.vntrader/reports/YYYY-MM-DD/"
    echo ""
    echo "📝 日志文件:"
    echo "   ├─ $HOME/.vntrader/logs/cron_daily.log   （每日更新）"
    echo "   ├─ $HOME/.vntrader/logs/cron_morning.log （早盘更新）"
    echo "   └─ $HOME/.vntrader/logs/cron_weekly.log  （周报）"
    echo ""
}

# ============ 显示当前状态 ============
show_status() {
    print_header "当前定时任务状态"
    
    echo ""
    if crontab -l 2>/dev/null | grep -q "daily_update.sh"; then
        print_success "定时任务已安装"
        echo ""
        echo "当前配置:"
        crontab -l | grep -A 10 "股票数据自动更新任务" || true
        echo ""
        show_schedule
    else
        print_warning "定时任务未安装"
        echo ""
        echo "运行以下命令安装:"
        echo "  $0 install"
    fi
}

# ============ 测试运行 ============
test_run() {
    print_header "测试运行"
    
    check_scripts
    
    print_info "开始测试运行 daily_update.sh（快速模式）..."
    echo ""
    
    bash "$DAILY_UPDATE_SCRIPT" --quick
    
    echo ""
    print_success "测试运行完成"
}

# ============ 主菜单 ============
show_menu() {
    print_header "Crontab 定时任务配置"
    
    echo ""
    echo "请选择操作:"
    echo ""
    echo "  1) install    - 安装定时任务"
    echo "  2) update     - 更新定时任务配置"
    echo "  3) uninstall  - 卸载定时任务"
    echo "  4) status     - 查看当前状态"
    echo "  5) test       - 测试运行"
    echo "  6) schedule   - 显示任务计划"
    echo ""
    echo "用法: $0 [install|update|uninstall|status|test|schedule]"
    echo ""
}

# ============ 主函数 ============
main() {
    case "${1:-}" in
        install)
            install_crontab
            ;;
        update)
            print_info "更新=卸载+重新安装"
            uninstall_crontab
            install_crontab
            ;;
        uninstall)
            uninstall_crontab
            ;;
        status)
            show_status
            ;;
        test)
            test_run
            ;;
        schedule)
            show_schedule
            ;;
        help|--help|-h)
            show_menu
            ;;
        *)
            show_menu
            echo ""
            print_error "请提供有效的操作参数"
            exit 1
            ;;
    esac
}

main "$@"
