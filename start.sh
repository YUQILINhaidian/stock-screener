#!/bin/bash

# 选股工作台 - 一键启动脚本
# 支持开发模式和生产模式（Docker）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                    ║${NC}"
    echo -e "${BLUE}║      📊 量化投资工作台 - 启动脚本               ║${NC}"
    echo -e "${BLUE}║                                                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 开发模式启动
start_dev() {
    print_info "启动开发模式..."
    
    # 检查 Python
    if ! command_exists python3; then
        print_error "未找到 Python 3，请先安装"
        exit 1
    fi
    
    # 检查 Node.js
    if ! command_exists node; then
        print_error "未找到 Node.js，请先安装"
        exit 1
    fi
    
    # 检查后端端口
    if check_port 8000; then
        print_warning "端口 8000 已被占用，跳过后端启动"
    else
        print_info "启动后端 API (端口 8000)..."
        cd api
        
        # 检查虚拟环境
        if [ ! -d "venv" ]; then
            print_info "创建虚拟环境..."
            python3 -m venv venv
        fi
        
        # 激活虚拟环境并安装依赖
        source venv/bin/activate
        pip install -q -r requirements.txt
        
        # 后台启动
        nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/stock-screener-api.log 2>&1 &
        API_PID=$!
        echo $API_PID > /tmp/stock-screener-api.pid
        
        print_success "后端 API 已启动 (PID: $API_PID)"
        cd ..
    fi
    
    # 检查前端端口
    if check_port 5173; then
        print_warning "端口 5173 已被占用，跳过前端启动"
    else
        print_info "启动前端 UI (端口 5173)..."
        cd ui
        
        # 检查并安装依赖
        if [ ! -d "node_modules" ]; then
            print_info "安装前端依赖..."
            npm install
        fi
        
        # 后台启动
        nohup npm run dev > /tmp/stock-screener-ui.log 2>&1 &
        UI_PID=$!
        echo $UI_PID > /tmp/stock-screener-ui.pid
        
        print_success "前端 UI 已启动 (PID: $UI_PID)"
        cd ..
    fi
    
    echo ""
    print_success "开发服务启动完成！"
    echo ""
    print_info "访问地址："
    echo -e "  ${GREEN}• 前端 UI:${NC}  http://localhost:5173"
    echo -e "  ${GREEN}• API 文档:${NC} http://localhost:8000/docs"
    echo ""
    print_info "查看日志："
    echo -e "  ${YELLOW}• 后端:${NC} tail -f /tmp/stock-screener-api.log"
    echo -e "  ${YELLOW}• 前端:${NC} tail -f /tmp/stock-screener-ui.log"
    echo ""
    print_info "停止服务："
    echo -e "  ${YELLOW}./start.sh stop${NC}"
    echo ""
}

# Docker 模式启动
start_docker() {
    print_info "启动 Docker 模式..."
    
    # 检查 Docker
    if ! command_exists docker; then
        print_error "未找到 Docker，请先安装"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "未找到 Docker Compose，请先安装"
        exit 1
    fi
    
    # 检查 .env 文件
    if [ ! -f "api/.env" ]; then
        print_warning "未找到 api/.env 文件，将使用默认配置"
        print_info "如需配置 AI 功能，请复制 api/.env.example 并修改"
    fi
    
    print_info "构建并启动容器..."
    
    # 使用 docker compose（新版）或 docker-compose（旧版）
    if docker compose version >/dev/null 2>&1; then
        docker compose up -d --build
    else
        docker-compose up -d --build
    fi
    
    print_success "Docker 容器启动完成！"
    echo ""
    print_info "访问地址："
    echo -e "  ${GREEN}• 前端 UI:${NC}  http://localhost"
    echo -e "  ${GREEN}• API 文档:${NC} http://localhost:8000/docs"
    echo ""
    print_info "查看容器状态："
    echo -e "  ${YELLOW}docker ps${NC}"
    echo ""
    print_info "查看日志："
    echo -e "  ${YELLOW}docker logs stock-screener-api${NC}"
    echo -e "  ${YELLOW}docker logs stock-screener-ui${NC}"
    echo ""
    print_info "停止服务："
    echo -e "  ${YELLOW}./start.sh stop --docker${NC}"
    echo ""
}

# 停止服务
stop_services() {
    local mode=$1
    print_info "停止服务..."
    
    if [ "$mode" == "--docker" ]; then
        # 停止 Docker 容器
        if docker compose version >/dev/null 2>&1; then
            docker compose down
        else
            docker-compose down
        fi
        print_success "Docker 容器已停止"
    else
        # 停止开发模式服务
        if [ -f "/tmp/stock-screener-api.pid" ]; then
            API_PID=$(cat /tmp/stock-screener-api.pid)
            if kill $API_PID 2>/dev/null; then
                print_success "后端 API 已停止 (PID: $API_PID)"
            fi
            rm /tmp/stock-screener-api.pid
        fi
        
        if [ -f "/tmp/stock-screener-ui.pid" ]; then
            UI_PID=$(cat /tmp/stock-screener-ui.pid)
            if kill $UI_PID 2>/dev/null; then
                print_success "前端 UI 已停止 (PID: $UI_PID)"
            fi
            rm /tmp/stock-screener-ui.pid
        fi
    fi
}

# 查看状态
show_status() {
    print_info "服务状态："
    echo ""
    
    # 检查开发模式
    if [ -f "/tmp/stock-screener-api.pid" ]; then
        API_PID=$(cat /tmp/stock-screener-api.pid)
        if kill -0 $API_PID 2>/dev/null; then
            echo -e "  ${GREEN}• 后端 API:${NC} 运行中 (PID: $API_PID, 端口: 8000)"
        else
            echo -e "  ${RED}• 后端 API:${NC} 已停止"
        fi
    else
        echo -e "  ${YELLOW}• 后端 API:${NC} 未启动"
    fi
    
    if [ -f "/tmp/stock-screener-ui.pid" ]; then
        UI_PID=$(cat /tmp/stock-screener-ui.pid)
        if kill -0 $UI_PID 2>/dev/null; then
            echo -e "  ${GREEN}• 前端 UI:${NC}  运行中 (PID: $UI_PID, 端口: 5173)"
        else
            echo -e "  ${RED}• 前端 UI:${NC}  已停止"
        fi
    else
        echo -e "  ${YELLOW}• 前端 UI:${NC}  未启动"
    fi
    
    echo ""
    
    # 检查 Docker 模式
    if docker ps --filter "name=stock-screener" --format "{{.Names}}" | grep -q "stock-screener"; then
        print_info "Docker 容器状态："
        docker ps --filter "name=stock-screener" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    fi
}

# 显示帮助
show_help() {
    print_banner
    echo "用法: ./start.sh [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  dev, --dev        启动开发模式（默认）"
    echo "  docker, --docker  使用 Docker 启动"
    echo "  stop              停止服务"
    echo "  status            查看服务状态"
    echo "  help, --help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  ./start.sh              # 启动开发模式"
    echo "  ./start.sh --docker     # 使用 Docker 启动"
    echo "  ./start.sh stop         # 停止开发模式服务"
    echo "  ./start.sh stop --docker # 停止 Docker 容器"
    echo "  ./start.sh status       # 查看服务状态"
    echo ""
}

# 主函数
main() {
    print_banner
    
    case "${1:-dev}" in
        dev|--dev)
            start_dev
            ;;
        docker|--docker)
            start_docker
            ;;
        stop)
            stop_services "$2"
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 进入脚本所在目录
cd "$(dirname "$0")"

# 执行主函数
main "$@"
