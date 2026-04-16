#!/bin/bash

# 选股 Skill GUI 后端启动脚本

echo "🚀 启动选股 Skill GUI 后端..."
echo ""

# 检查是否在正确的目录
if [ ! -f "app/main.py" ]; then
    echo "❌ 错误：请在 api 目录下运行此脚本"
    exit 1
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python 版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 发现虚拟环境，激活中..."
    source venv/bin/activate
else
    echo "⚠️  未发现虚拟环境，建议创建："
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
    read -p "是否继续使用全局 Python 环境？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查依赖
echo ""
echo "🔍 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ FastAPI 未安装"
    echo "📦 正在安装依赖..."
    pip install -r requirements.txt
fi

# 启动服务
echo ""
echo "✨ 启动 FastAPI 服务..."
echo "   • API 端点: http://localhost:8000"
echo "   • API 文档: http://localhost:8000/docs"
echo "   • ReDoc: http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
