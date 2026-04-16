#!/usr/bin/env python3
"""
测试 LLM 配置脚本

验证不同的 LLM 提供商是否配置正确
"""

import sys
import os
import asyncio

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.llm_providers import LLMFactory, get_default_llm_provider
from app.config import settings

async def test_llm():
    """测试 LLM 配置"""
    
    print("🤖 测试 LLM 配置")
    print("=" * 60)
    
    # 显示当前配置
    print(f"\n📋 当前配置:")
    print(f"  提供商: {settings.LLM_PROVIDER}")
    print(f"  模型: {settings.LLM_MODEL or '(使用默认)'}")
    print(f"  API Key: {'✅ 已配置' if settings.LLM_API_KEY else '❌ 未配置'}")
    print(f"  Base URL: {settings.LLM_BASE_URL or '(使用默认)'}")
    print(f"  温度: {settings.LLM_TEMPERATURE}")
    print(f"  最大 Tokens: {settings.LLM_MAX_TOKENS}")
    
    if not settings.LLM_API_KEY:
        print("\n❌ 错误: 未配置 LLM_API_KEY")
        print("请在 .env 文件中设置 LLM_API_KEY")
        return False
    
    try:
        # 创建提供商
        print(f"\n🔄 正在初始化 {settings.LLM_PROVIDER} 提供商...")
        provider = get_default_llm_provider()
        print(f"✅ 提供商初始化成功: {provider.get_provider_name()}")
        
        # 测试简单对话
        print(f"\n🧪 测试 AI 对话...")
        test_messages = [
            {"role": "user", "content": "请用一句话介绍你自己"}
        ]
        
        response = await provider.chat(
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"\n✅ AI 响应成功!")
        print(f"回复内容: {response[:100]}...")
        
        # 测试市场分析
        print(f"\n🧪 测试市场分析功能...")
        from app.services.ai_service import AIService
        
        ai_service = AIService(provider)
        result = await ai_service.analyze_market("SSE", "1M")
        
        print(f"✅ 市场分析成功!")
        print(f"  趋势: {result.get('trend')}")
        print(f"  置信度: {result.get('confidence')}")
        print(f"  推荐策略: {result.get('recommended_strategies')}")
        
        print(f"\n{'=' * 60}")
        print("✅ 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print(f"\n建议:")
        print(f"  1. 检查 API Key 是否正确")
        print(f"  2. 确认提供商类型是否正确")
        print(f"  3. 检查网络连接")
        print(f"  4. 查看详细错误信息:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm())
    sys.exit(0 if success else 1)
