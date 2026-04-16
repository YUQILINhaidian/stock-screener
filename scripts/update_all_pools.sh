#!/bin/bash
# 股票池批量更新与报告生成脚本
# 
# 功能:
# 1. 更新所有股票池的价格数据
# 2. 生成可视化HTML/PNG/PDF报告
# 3. 支持自动检测所有股票池
# 4. 可单独运行或作为定时任务
#
# 使用:
#   ./update_all_pools.sh              # 更新所有池子并生成报告
#   ./update_all_pools.sh --html-only  # 只生成HTML
#   ./update_all_pools.sh --fast       # 快速模式（跳过PDF）

set -e  # 遇到错误立即退出

# ============ 配置区 ============
POOL_DIR="$HOME/.vntrader/stock_pools"
REPORT_DIR="$HOME/.vntrader/reports"
TRACKER_SCRIPT="$HOME/stock_pool_tracker.py"
GSTACK_MANAGER="$HOME/.agents/skills/stock-screener/python/gstack/gstack_data_manager.py"

# 日期戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TODAY=$(date +"%Y-%m-%d")

# 日志文件
LOG_DIR="$HOME/.vntrader/logs"
LOG_FILE="$LOG_DIR/pool_update_${TODAY}.log"

# ============ 初始化 ============
mkdir -p "$REPORT_DIR"
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ ERROR: $*" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $*" | tee -a "$LOG_FILE"
}

# ============ 参数解析 ============
MODE="full"  # full | html-only | fast

while [[ $# -gt 0 ]]; do
    case $1 in
        --html-only)
            MODE="html-only"
            shift
            ;;
        --fast)
            MODE="fast"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --html-only    仅生成HTML报告，不截图/导出PDF"
            echo "  --fast         快速模式（生成HTML+PNG，跳过PDF）"
            echo "  --help         显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                  # 完整模式（HTML+PNG+PDF）"
            echo "  $0 --html-only      # 仅HTML"
            echo "  $0 --fast           # 快速模式"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# ============ 检查依赖 ============
check_dependencies() {
    log "检查依赖..."
    
    if [ ! -f "$TRACKER_SCRIPT" ]; then
        log_error "stock_pool_tracker.py 不存在: $TRACKER_SCRIPT"
        exit 1
    fi
    
    if [ ! -f "$GSTACK_MANAGER" ]; then
        log_error "gstack_data_manager.py 不存在: $GSTACK_MANAGER"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# ============ 获取所有股票池 ============
get_all_pools() {
    if [ ! -d "$POOL_DIR" ]; then
        log_error "股票池目录不存在: $POOL_DIR"
        exit 1
    fi
    
    # 查找所有 .json 文件（排除备份）
    find "$POOL_DIR" -name "*.json" -not -name "*_backup*" -type f | while read -r pool_file; do
        basename "$pool_file" .json
    done | sort
}

# ============ 更新单个股票池 ============
update_pool() {
    local pool_name="$1"
    
    log "正在更新: $pool_name"
    
    if python3 "$TRACKER_SCRIPT" update --name "$pool_name" >> "$LOG_FILE" 2>&1; then
        log_success "$pool_name - 价格更新完成"
        return 0
    else
        log_error "$pool_name - 价格更新失败"
        return 1
    fi
}

# ============ 生成报告 ============
generate_report() {
    local pool_name="$1"
    local report_subdir="$REPORT_DIR/${TODAY}"
    mkdir -p "$report_subdir"
    
    log "生成报告: $pool_name"
    
    # 生成HTML
    local html_output="$report_subdir/${pool_name}.html"
    
    case "$MODE" in
        html-only)
            # 仅生成HTML
            if python3 "$GSTACK_MANAGER" --pool "$pool_name" --output "$html_output" >> "$LOG_FILE" 2>&1; then
                log_success "$pool_name - HTML报告已生成: $html_output"
            else
                log_error "$pool_name - HTML生成失败"
                return 1
            fi
            ;;
        
        fast)
            # 生成HTML + PNG
            if python3 "$GSTACK_MANAGER" --pool "$pool_name" --output "$html_output" --screenshot >> "$LOG_FILE" 2>&1; then
                log_success "$pool_name - HTML+PNG报告已生成"
            else
                log_error "$pool_name - 报告生成失败"
                return 1
            fi
            ;;
        
        full)
            # 生成HTML + PNG + PDF
            if python3 "$GSTACK_MANAGER" --pool "$pool_name" --output "$html_output" --screenshot --pdf >> "$LOG_FILE" 2>&1; then
                log_success "$pool_name - 完整报告已生成（HTML+PNG+PDF）"
            else
                log_error "$pool_name - 报告生成失败"
                return 1
            fi
            ;;
    esac
    
    return 0
}

# ============ 生成汇总报告 ============
generate_summary() {
    local report_subdir="$REPORT_DIR/${TODAY}"
    local summary_file="$report_subdir/summary.txt"
    
    log "生成汇总报告..."
    
    cat > "$summary_file" << EOF
================================================================================
股票池批量更新汇总报告
================================================================================
生成时间: $(date +'%Y-%m-%d %H:%M:%S')
更新模式: $MODE
报告目录: $report_subdir

--------------------------------------------------------------------------------
处理结果:
--------------------------------------------------------------------------------
EOF
    
    # 统计成功/失败数量
    local total=0
    local success=0
    local failed=0
    
    for pool_name in $(get_all_pools); do
        total=$((total + 1))
        
        if [ -f "$report_subdir/${pool_name}.html" ]; then
            success=$((success + 1))
            echo "✅ $pool_name" >> "$summary_file"
        else
            failed=$((failed + 1))
            echo "❌ $pool_name" >> "$summary_file"
        fi
    done
    
    cat >> "$summary_file" << EOF

--------------------------------------------------------------------------------
统计信息:
--------------------------------------------------------------------------------
总股票池数量: $total
成功处理: $success
处理失败: $failed
成功率: $(awk "BEGIN {printf \"%.1f%%\", ($success/$total)*100}")

报告文件列表:
$(ls -lh "$report_subdir" | tail -n +2)

================================================================================
详细日志: $LOG_FILE
================================================================================
EOF
    
    log_success "汇总报告已生成: $summary_file"
    
    # 输出到终端
    cat "$summary_file"
}

# ============ 主流程 ============
main() {
    log "==================== 开始批量更新 ===================="
    log "运行模式: $MODE"
    
    # 检查依赖
    check_dependencies
    
    # 获取所有股票池
    local pools=($(get_all_pools))
    local total_pools=${#pools[@]}
    
    if [ $total_pools -eq 0 ]; then
        log_error "未找到任何股票池"
        exit 1
    fi
    
    log "发现 $total_pools 个股票池"
    
    # 统计
    local update_success=0
    local update_failed=0
    local report_success=0
    local report_failed=0
    
    # 处理每个股票池
    local i=0
    for pool_name in "${pools[@]}"; do
        i=$((i + 1))
        log ""
        log "[$i/$total_pools] 处理: $pool_name"
        log "----------------------------------------"
        
        # 1. 更新价格
        if update_pool "$pool_name"; then
            update_success=$((update_success + 1))
            
            # 2. 生成报告
            if generate_report "$pool_name"; then
                report_success=$((report_success + 1))
            else
                report_failed=$((report_failed + 1))
            fi
        else
            update_failed=$((update_failed + 1))
            report_failed=$((report_failed + 1))
        fi
        
        # 避免频繁操作，延迟1秒
        sleep 1
    done
    
    log ""
    log "==================== 处理完成 ===================="
    log "价格更新: $update_success 成功, $update_failed 失败"
    log "报告生成: $report_success 成功, $report_failed 失败"
    log ""
    
    # 生成汇总
    generate_summary
    
    log ""
    log "==================== 全部完成 ===================="
    log "报告目录: $REPORT_DIR/${TODAY}"
    log "日志文件: $LOG_FILE"
    
    # 返回状态码
    if [ $update_failed -gt 0 ] || [ $report_failed -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# 运行主流程
main
