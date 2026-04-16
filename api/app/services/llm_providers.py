"""
LLM 提供商抽象基类和具体实现

支持多种大模型：
- Claude (Anthropic)
- OpenAI (GPT-4, GPT-3.5)
- 通义千问 (Qwen)
- 文心一言 (Ernie)
- DeepSeek
- 其他兼容 OpenAI API 的模型
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings

class LLMProvider(ABC):
    """LLM 提供商抽象基类"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.extra_params = kwargs
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        聊天接口
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            str: 模型回复
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass


class ClaudeProvider(LLMProvider):
    """Claude (Anthropic) 提供商"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.anthropic.com/v1")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """调用 Claude API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    def get_provider_name(self) -> str:
        return "Claude (Anthropic)"


class OpenAIProvider(LLMProvider):
    """OpenAI 提供商（GPT-4, GPT-3.5）"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """调用 OpenAI API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_provider_name(self) -> str:
        return "OpenAI"


class QwenProvider(LLMProvider):
    """通义千问提供商"""
    
    def __init__(self, api_key: str, model: str = "qwen-turbo", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://dashscope.aliyuncs.com/api/v1")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """调用通义千问 API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": {
                        "messages": messages
                    },
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        **kwargs
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["output"]["text"]
    
    def get_provider_name(self) -> str:
        return "通义千问 (Qwen)"


class DeepSeekProvider(LLMProvider):
    """DeepSeek 提供商"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.deepseek.com/v1")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """调用 DeepSeek API（兼容 OpenAI 格式）"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_provider_name(self) -> str:
        return "DeepSeek"


class GenericOpenAIProvider(LLMProvider):
    """通用 OpenAI 兼容提供商（支持自定义 base_url）"""
    
    def __init__(self, api_key: str, model: str, base_url: str, **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.base_url = base_url
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """调用兼容 OpenAI API 的服务"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def get_provider_name(self) -> str:
        return f"Generic OpenAI Compatible ({self.base_url})"


# LLM 工厂类
class LLMFactory:
    """LLM 提供商工厂"""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        创建 LLM 提供商实例
        
        Args:
            provider_type: 提供商类型 (claude, openai, qwen, deepseek, generic)
            api_key: API 密钥
            model: 模型名称（可选，使用默认模型）
            **kwargs: 额外参数（如 base_url）
        
        Returns:
            LLMProvider: LLM 提供商实例
        """
        provider_type = provider_type.lower()
        
        if provider_type == "claude":
            return ClaudeProvider(api_key, model or "claude-3-5-sonnet-20241022", **kwargs)
        elif provider_type == "openai":
            return OpenAIProvider(api_key, model or "gpt-4", **kwargs)
        elif provider_type == "qwen":
            return QwenProvider(api_key, model or "qwen-turbo", **kwargs)
        elif provider_type == "deepseek":
            return DeepSeekProvider(api_key, model or "deepseek-chat", **kwargs)
        elif provider_type == "generic":
            if "base_url" not in kwargs:
                raise ValueError("Generic provider requires 'base_url' parameter")
            return GenericOpenAIProvider(api_key, model or "default", **kwargs)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")


# 便捷函数：从配置创建默认提供商
def get_default_llm_provider() -> LLMProvider:
    """从配置创建默认的 LLM 提供商"""
    return LLMFactory.create_provider(
        provider_type=settings.LLM_PROVIDER,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL if hasattr(settings, 'LLM_BASE_URL') else None
    )
