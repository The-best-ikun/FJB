"""
LLM服务模块
负责与各种大语言模型进行交互
"""

import logging
import os
import json
import asyncio
from urllib import request as urllib_request
from urllib import error as urllib_error
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

# 尝试导入不同的LLM库
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
# try:
#     import deepseek
#     DEEPSEEK_AVAILABLE = True
# except ImportError:
#     DEEPSEEK_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)
# 抽象类
class LLMProvider(ABC):
    """LLM提供者抽象基类"""
    
    @abstractmethod
    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """
        生成文本
        
        Args:
            messages: 对话历史列表，每个元素包含role和content
            max_tokens: 最大令牌数
            
        Returns:
            str: 生成的文本
        """
        pass
    
    @abstractmethod
    async def initialize(self):
        """初始化模型"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass

# 抽象类的具体实现
# OpenAI GPT模型
class OpenAIProvider(LLMProvider):
    """OpenAI GPT模型提供者"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    async def initialize(self):
        """初始化OpenAI客户端"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI库未安装")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY环境变量未设置")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI提供者初始化完成，模型: {self.model}")
    
    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """使用OpenAI生成文本"""
        try:
            # 确保有系统消息
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"}] + messages
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI生成文本失败: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取OpenAI统计信息"""
        return {
            "provider": "openai",
            "model": self.model,
            "status": "active" if self.client else "inactive"
        }
# Anthropic Claude模型
class AnthropicProvider(LLMProvider):
    """Anthropic Claude模型提供者"""
    
    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        self.model = model
        self.client = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
    
    async def initialize(self):
        """初始化Anthropic客户端"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic库未安装")
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY环境变量未设置")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info(f"Anthropic提供者初始化完成，模型: {self.model}")
    
    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """使用Anthropic生成文本"""
        try:
            # Anthropic需要过滤掉system消息，因为它不支持system role
            anthropic_messages = []
            system_message = None
            
            for msg in messages:
                if msg.get("role") == "system":
                    system_message = msg.get("content", "")
                elif msg.get("role") in ["user", "assistant"]:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 如果没有系统消息，使用默认的
            if not system_message:
                system_message = "你是一个专业的代码助手，擅长分析和解释代码。"
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                system=system_message,
                messages=anthropic_messages
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic生成文本失败: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取Anthropic统计信息"""
        return {
            "provider": "anthropic",
            "model": self.model,
            "status": "active" if self.client else "inactive"
        }

"""
DeepSeek 大模型提供者（HTTP 版，初代MVP代码）

此实现不依赖官方 SDK，通过 OpenAI 兼容的 Chat Completions 接口进行调用。
需要的环境变量：
- DEEPSEEK_API_KEY: 授权 Token，形如 sk-***
- DEEPSEEK_API_URL: API 根路径（可选，默认 https://api.deepseek.com/v1/chat/completions）
"""

class DeepSeekHTTPProvider(LLMProvider):
    """DeepSeek 模型提供者（纯 HTTP）"""

    def __init__(self, model: str = "deepseek-chat"):

        self.model = model
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        
        # DeepSeek 提供 路径
        self.api_url = os.getenv("DEEPSEEK_API_URL")
        self.initialized = False

    async def initialize(self):
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY 密钥未设置")
        if not self.api_url:
            raise ValueError("DEEPSEEK_API_URL 请求网址未设置")
        # HTTP 版无需创建客户端，这里仅做校验
        self.initialized = True
        logger.info(f"DeepSeek(HTTP) 提供者初始化完成，模型: {self.model}")

    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        if not self.initialized:
            raise RuntimeError("DeepSeek(HTTP) 提供者未初始化")

        # 确保有系统消息
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"}] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        def _do_request() -> str:
            req = urllib_request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urllib_request.urlopen(req, timeout=60) as resp:
                    body = resp.read().decode("utf-8")
            except urllib_error.HTTPError as http_err:
                try:
                    err_body = http_err.read().decode("utf-8")
                except Exception:
                    err_body = ""
                raise RuntimeError(f"DeepSeek HTTP {http_err.code}: {err_body}") from http_err
            except Exception as e:
                raise RuntimeError(f"DeepSeek 请求失败: {e}") from e

            try:
                data = json.loads(body)
            except Exception as e:
                raise RuntimeError(f"DeepSeek 响应解析失败: {e}; 原始: {body[:500]}") from e

            # OpenAI 兼容格式：choices[0].message.content
            choices = data.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

            # 兜底支持 text 字段或其他形式
            if "text" in data and isinstance(data["text"], str):
                return data["text"].strip()

            raise RuntimeError("无法解析 DeepSeek 响应: 缺少 choices[0].message.content")

        try:
            # 在异步环境中执行阻塞的 urllib 调用
            return await asyncio.to_thread(_do_request)
        except Exception as e:
            logger.error(f"DeepSeek(HTTP) 生成文本失败: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "provider": "deepseek",
            "model": self.model,
            "status": "active" if self.initialized else "inactive",
            "api_url": self.api_url,
        }


class QingYanHTTPProvider(LLMProvider):
    """智谱轻言 (QingYan) HTTP 提供者轻量实现

    使用简单的 HTTP POST 请求与服务交互，不依赖官方 SDK。
    环境变量：
      - QINGYAN_API_KEY: API 密钥
      - QINGYAN_API_URL: API 根路径（例如 https://api.qingyan.ai/v1/chat/completions）
    该实现与 DeepSeekHTTPProvider 相似，尽量兼容常见的 OpenAI-like 返回格式。
    """

    def __init__(self, model: str = "glm-4.5-flash"):
        self.model = model
        self.api_key = os.getenv("QINGYAN_API_KEY")
        self.api_url = os.getenv("QINGYAN_API_URL")
        self.initialized = False

    async def initialize(self):
        if not self.api_key:
            raise ValueError("QINGYAN_API_KEY 未设置")
        if not self.api_url:
            raise ValueError("QINGYAN_API_URL 未设置")
        # 不创建持久客户端，仅做基础校验
        self.initialized = True
        logger.info(f"QingYan(HTTP) 提供者初始化完成，模型: {self.model}")
        print(f"QingYan(HTTP) 提供者初始化完成，模型: {self.model}")

    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        if not self.initialized:
            raise RuntimeError("QingYan(HTTP) 提供者未初始化")

        # 确认是不是第一次对话，如果系统消息为空，则使用默认的系统消息
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"}] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        def _do_request() -> str:
            req = urllib_request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            try:
                with urllib_request.urlopen(req, timeout=60) as resp:
                    body = resp.read().decode("utf-8")
            except urllib_error.HTTPError as http_err:
                try:
                    err_body = http_err.read().decode("utf-8")
                except Exception:
                    err_body = ""
                raise RuntimeError(f"QingYan HTTP {http_err.code}: {err_body}") from http_err
            except Exception as e:
                raise RuntimeError(f"QingYan 请求失败: {e}") from e

            try:
                data = json.loads(body)
            except Exception as e:
                raise RuntimeError(f"QingYan 响应解析失败: {e}; 原始: {body[:500]}") from e

            # 支持 OpenAI-like 格式：choices[0].message.content 或 choices[0].text
            choices = data.get("choices") or []
            if choices:
                first = choices[0]
                # 支持 choices[0].message.content
                message = first.get("message") if isinstance(first, dict) else None
                if message and isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()

                # 支持 legacy text 字段或 choices[0].text
                text = first.get("text") if isinstance(first, dict) else None
                if isinstance(text, str) and text.strip():
                    return text.strip()

            # 兜底支持 data.text
            if "text" in data and isinstance(data["text"], str):
                return data["text"].strip()

            raise RuntimeError("无法解析 QingYan 响应: 缺少可用文本字段")

        try:
            return await asyncio.to_thread(_do_request)
        except Exception as e:
            logger.error(f"QingYan(HTTP) 生成文本失败: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "provider": "GLM-4-Flash-250414",
            "model": self.model,
            "status": "active" if self.initialized else "inactive",
            "api_url": self.api_url,
        }
# 本地大模型
class LocalProvider(LLMProvider):
    """本地模型提供者（使用Transformers）"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
    
    async def initialize(self):
        """初始化本地模型"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers库未安装")
        
        try:
            logger.info(f"正在加载本地模型: {self.model_name}")
            
            # 加载分词器和模型
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # 创建文本生成管道
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=512,
                do_sample=True,
                temperature=0.7
            )
            
            logger.info("本地模型初始化完成")
            
        except Exception as e:
            logger.error(f"本地模型初始化失败: {e}")
            raise
    
    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """使用本地模型生成文本"""
        try:
            # 将对话历史转换为单个文本提示
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "system":
                    prompt_parts.append(f"系统: {content}")
                elif role == "user":
                    prompt_parts.append(f"用户: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"助手: {content}")
            
            # 组合所有消息
            full_prompt = "\n".join(prompt_parts) + "\n助手:"
            
            # 使用管道生成文本
            result = self.pipeline(
                full_prompt,
                max_length=min(max_tokens, 512),
                num_return_sequences=1,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # 提取生成的文本
            generated_text = result[0]['generated_text']
            
            # 移除原始提示，只返回生成的部分
            if generated_text.startswith(full_prompt):
                generated_text = generated_text[len(full_prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"本地模型生成文本失败: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取本地模型统计信息"""
        return {
            "provider": "local",
            "model": self.model_name,
            "status": "active" if self.pipeline else "inactive"
        }

class LLMService:
    """LLM服务类，管理不同的LLM提供者"""
    
    def __init__(self):
        self.provider: Optional[LLMProvider] = None
        self.provider_name = "openai"  # 默认使用OpenAI
    
    async def initialize(self):
        """初始化LLM服务"""
        try:
            # 根据环境变量选择提供者,如果配置文件中没有，默认为 deepseek
            provider_name = os.getenv("LLM_PROVIDER", "deepseek")
            
            if provider_name == "openai" and OPENAI_AVAILABLE:
                self.provider = OpenAIProvider()
            elif provider_name == "anthropic" and ANTHROPIC_AVAILABLE:
                self.provider = AnthropicProvider()
            elif provider_name == "deepseek":
                # DeepSeek 使用纯 HTTP 实现，不依赖 SDK
                self.provider = DeepSeekHTTPProvider()
            elif provider_name == "glm-4.5-flash":
                
                # 智谱轻言服务提供者
                self.provider = QingYanHTTPProvider()
            elif provider_name == "local" and TRANSFORMERS_AVAILABLE:
                self.provider = LocalProvider()
            else:
                # 回退到可用的提供者
                if OPENAI_AVAILABLE:
                    self.provider = OpenAIProvider()
                    provider_name = "openai"
                elif ANTHROPIC_AVAILABLE:
                    self.provider = AnthropicProvider()
                    provider_name = "anthropic"
                # 尝试 DeepSeek HTTP 作为进一步回退（如果配置了 Key）
                elif os.getenv("DEEPSEEK_API_KEY"):
                        self.provider = DeepSeekHTTPProvider()
                        provider_name = "deepseek"

                # 否则使用本地模型（如果可用）
                elif TRANSFORMERS_AVAILABLE:
                    self.provider = LocalProvider()
                    provider_name = "local"
                else:
                    raise RuntimeError("没有可用的LLM提供者")
            
            # 初始化选定的提供者
            await self.provider.initialize()
            self.provider_name = provider_name
            
            logger.info(f"LLM服务初始化完成，使用提供者: {provider_name}")
            print(f"LLM服务初始化完成，使用提供者: {provider_name}")
            
        except Exception as e:
            logger.error(f"LLM服务初始化失败: {e}")
            raise
    
    async def generate_text(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """
        生成文本
        
        Args:
            messages: 对话历史列表，每个元素包含role和content
            max_tokens: 最大令牌数
            
        Returns:
            str: 生成的文本
        """
        if not self.provider:
            raise RuntimeError("LLM服务未初始化")
        
        return await self.provider.generate_text(messages, max_tokens)
    
    async def generate_text_with_history(self, conversation_history: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """
        使用对话历史生成文本（别名方法，为了更清晰的语义）
        
        Args:
            conversation_history: 完整的对话历史，包含system、user、assistant消息
            max_tokens: 最大令牌数
            
        Returns:
            str: 生成的文本
        """
        return await self.generate_text(conversation_history, max_tokens)
    
    async def generate_code_explanation(self, code: str, language: str) -> str:
        """
        生成代码解释
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            str: 代码解释
        """
        # 构建对话消息
        messages = [
            {"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"},
            {"role": "user", "content": f"""请解释以下{language}代码的功能和实现原理：

```{language}
{code}
```

请提供：
1. 代码的主要功能
2. 关键实现细节
3. 可能的改进建议"""}
        ]
        
        return await self.generate_text(messages)
    
    async def generate_documentation(self, code: str, language: str) -> str:
        """
        生成代码文档
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            str: 生成的文档
        """
        messages = [
            {"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"},
            {"role": "user", "content": f"""请为以下{language}代码生成详细的文档：

```{language}
{code}
```

请生成包含以下内容的文档：
1. 功能描述
2. 参数说明
3. 返回值说明
4. 使用示例
5. 注意事项"""}
        ]
        
        return await self.generate_text(messages)
    
    async def answer_question(self, question: str, context: str) -> str:
        """
        回答问题
        
        Args:
            question: 用户问题
            context: 上下文信息
            
        Returns:
            str: 答案
        """
        messages = [
            {"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"},
            {"role": "user", "content": f"""基于以下信息回答用户的问题：

{context}

用户问题：{question}

请提供准确、详细的答案。"""}
        ]
        
        return await self.generate_text(messages)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取LLM服务统计信息"""
        if not self.provider:
            return {"status": "not_initialized"}
        
        stats = await self.provider.get_stats()
        stats["service_status"] = "active"
        return stats
