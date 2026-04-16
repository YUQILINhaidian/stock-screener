#!/usr/bin/env python3
"""
快速测试脚本 - 验证 API 是否正常启动
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("🔍 检查依赖...")
    
    # 检查 FastAPI
    try:
        import fastapi
        print(f"  ✅ FastAPI {fastapi.__version__}")
    except ImportError:
        print("  ❌ FastAPI 未安装，请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 检查 Pydantic
    try:
        import pydantic
        print(f"  ✅ Pydantic {pydantic.__version__}")
    except ImportError:
        print("  ❌ Pydantic 未安装")
        sys.exit(1)
    
    # 检查 Uvicorn
    try:
        import uvicorn
        print(f"  ✅ Uvicorn {uvicorn.__version__}")
    except ImportError:
        print("  ❌ Uvicorn 未安装")
        sys.exit(1)
    
    print("\n🚀 尝试导入应用...")
    
    # 导入应用
    from app.main import app
    print("  ✅ 应用导入成功")
    
    # 检查路由
    routes = [route.path for route in app.routes]
    print(f"\n📋 注册的路由 ({len(routes)} 个):")
    for route in sorted(routes):
        if not route.startswith("/_"):
            print(f"  • {route}")
    
    print("\n✨ API 基础结构验证通过！")
    print("\n📖 下一步:")
    print("  1. 安装依赖: pip install -r requirements.txt")
    print("  2. 启动服务: uvicorn app.main:app --reload")
    print("  3. 访问文档: http://localhost:8000/docs")
    print()
    
except Exception as e:
    print(f"\n❌ 验证失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
