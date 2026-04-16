#!/bin/bash
# 每日股票数据更新脚本
#
# 功能:
# 1. 更新VNPy数据中心的K线数据
# 2. 更新所有股票池价格
# 3. 生成每日报告
#
# 适合作为crontab定时任务运行
# 
# 使用:
#   ./daily_update.sh              # 完整更新
#   ./daily_update.sh --quick      # 快速模式（跳过数据中心更新）
#   ./daily_update.sh --pools-only # 仅更新股票池

set -e

# ============ 配置 ============
VNTRADER_DIR="$HOME/.vntrader"
DATA_UPDATE_SCRIPT="$HOME/update_daily_data.py"  # VNPy数据更新脚本
POOL_UPDATE_SCRIPT="$HOME/.agents/skills/stock-screener/scripts/update_all_pools.sh"

LOG_DIR="$VNTRADER_DIR/logs"
TODAY=$(date +"%Y-%m-%d")
LOG_FILE="$LOG_DIR/daily_update_${TODAY}.log"

mkdir -p "$LOG_DIR"

# ============ 日志 ============
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "================================================================================" | tee -a "$LOG_FILE"
    echo "  $*" | tee -a "$LOG_FILE"
    echo "================================================================================" | tee -a "$LOG_FILE"
}

log_success() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# ============ 参数解析 ============
UPDATE_DATA_CENTER=true
UPDATE_POOLS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            UPDATE_DATA_CENTER=false
            shift
            ;;
        --pools-only)
            UPDATE_DATA_CENTER=false
            UPDATE_POOLS=true
            shift
            ;;
        --data-only)
            UPDATE_DATA_CENTER=true
            UPDATE_POOLS=false
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --quick        快速模式（跳过数据中心更新，仅更新股票池）"
            echo "  --pools-only   仅更新股票池"
            echo "  --data-only    仅更新数据中心"
            echo "  --help         显示帮助"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# ============ 检查交易日 ============
is_trading_day() {
    local today_weekday=$(date +%u)  # 1-7 (Monday-Sunday)
    
    # 周末不是交易日
    if [ "$today_weekday" -eq 6 ] || [ "$today_weekday" -eq 7 ]; then
        return 1
    fi
    
    # TODO: 可以增加节假日检查（从API获取）
    return 0
}

# ============ 更新数据中心 ============
update_data_center() {
    log_section "第1步: 更新VNPy数据中心"
    
    if [ ! -f "$DATA_UPDATE_SCRIPT" ]; then
        log_error "数据更新脚本不存在: $DATA_UPDATE_SCRIPT"
        return 1
    fi
    
    log "开始更新K线数据..."
    
    # 运行数据更新脚本
    if python3 "$DATA_UPDATE_SCRIPT" >> "$LOG_FILE" 2>&1; then
        log_success "数据中心更新完成"
        return 0
    else
        log_error "数据中心更新失败"
        return 1
    fi
}

# ============ 更新股票池 ============
update_stock_pools() {
    log_section "第2步: 更新股票池并生成报告"
    
    if [ ! -f "$POOL_UPDATE_SCRIPT" ]; then
        log_error "股票池更新脚本不存在: $POOL_UPDATE_SCRIPT"
        return 1
    fi
    
    log "运行股票池批量更新..."
    
    # 使用fast模式（生成HTML+PNG，跳过PDF以节省时间）
    if bash "$POOL_UPDATE_SCRIPT" --fast >> "$LOG_FILE" 2>&1; then
        log_success "股票池更新完成"
        return 0
    else
        log_error "股票池更新失败"
        return 1
    fi
}

# ============ 发送通知（可选） ============
send_notification() {
    local status="$1"
    local message="$2"
    
    # TODO: 集成企业微信/钉钉/邮件通知
    # 示例: 使用macOS通知
    if command -v osascript &> /dev/null; then
        osascript -e "display notification \"$message\" with title \"股票数据更新\" subtitle \"$status\""
    fi
}

# ============ 主流程 ============
main() {
    log_section "每日股票数据更新任务"
    log "开始时间: $(date +'%Y-%m-%d %H:%M:%S')"
    log "运行用户: $(whoami)"
    log "工作目录: $(pwd)"
    
    # 检查是否交易日
    if ! is_trading_day; then
        log "⚠️  今天是周末，跳过数据更新"
        log "仅更新股票池价格（使用上一交易日数据）"
        UPDATE_DATA_CENTER=false
    fi
    
    local has_error=false
    
    # 步骤1: 更新数据中心
    if $UPDATE_DATA_CENTER; then
        if ! update_data_center; then
            has_error=true
            log_error "数据中心更新失败，继续处理股票池..."
        fi
    else
        log "跳过数据中心更新（--quick模式或非交易日）"
    fi
    
    # 步骤2: 更新股票池
    if $UPDATE_POOLS; then
        if ! update_stock_pools; then
            has_error=true
        fi
    else
        log "跳过股票池更新（--data-only模式）"
    fi
    
    # 完成
    log_section "任务完成"
    log "结束时间: $(date +'%Y-%m-%d %H:%M:%S')"
    log "日志文件: $LOG_FILE"
    
    # 生成报告链接
    local report_dir="$VNTRADER_DIR/reports/${TODAY}"
    if [ -d "$report_dir" ]; then
        log ""
        log "📊 今日报告: $report_dir"
        log "   - 报告数量: $(ls -1 "$report_dir"/*.html 2>/dev/null | wc -l | tr -d ' ') 个"
        log "   - 汇总报告: $report_dir/summary.txt"
    fi
    
    # 发送通知
    if $has_error; then
        send_notification "失败" "部分任务执行失败，请查看日志"
        exit 1
    else
        send_notification "成功" "所有任务执行成功"
        exit 0
    fi
}

# 运行
main
