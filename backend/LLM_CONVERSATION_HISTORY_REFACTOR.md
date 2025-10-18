# LLM服务对话历史支持重构总结

## 修改概述

根据用户反馈，原有的LLM服务只传递单个问题而不考虑对话历史，这不符合大模型的实际使用场景。本次重构将LLM服务的`generate_text`方法改为支持完整的对话历史。

## 主要修改

### 1. 抽象类修改 (`LLMProvider`)

**修改前:**
```python
@abstractmethod
async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
    """生成文本"""
    pass
```

**修改后:**
```python
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
```

### 2. 各提供者实现更新

#### OpenAIProvider
- 确保系统消息存在，如果没有则自动添加
- 直接传递完整的messages列表给OpenAI API

#### AnthropicProvider  
- 特殊处理：Anthropic不支持system role，需要将system消息提取到单独的system参数
- 过滤掉system消息，只传递user和assistant消息

#### DeepSeekHTTPProvider
- 确保系统消息存在
- 直接传递完整的messages列表

#### QingYanHTTPProvider
- 确保系统消息存在
- 直接传递完整的messages列表

#### LocalProvider
- 将对话历史转换为文本格式
- 使用"系统:"、"用户:"、"助手:"前缀来区分不同角色

### 3. LLMService类更新

- 更新`generate_text`方法签名
- 更新所有相关方法（`generate_code_explanation`、`generate_documentation`、`answer_question`）
- 添加`generate_text_with_history`别名方法，提供更清晰的语义

### 4. RAGEngine更新

- 更新`_generate_answer`方法，使用新的对话消息格式
- 更新直接调用LLM的部分
- 删除不再需要的`_build_prompt`方法

## 使用示例

### 基本用法
```python
# 创建对话历史
conversation_history = [
    {"role": "system", "content": "你是一个专业的代码助手。"},
    {"role": "user", "content": "什么是Python装饰器？"},
    {"role": "assistant", "content": "装饰器是一种设计模式..."},
    {"role": "user", "content": "能给我一个例子吗？"}
]

# 生成回答
llm_service = LLMService()
await llm_service.initialize()
response = await llm_service.generate_text_with_history(conversation_history)
```

### 在RAG引擎中的使用
```python
# RAG引擎现在会自动构建包含系统消息的对话格式
messages = [
    {"role": "system", "content": "你是一个专业的代码助手，请基于以下相关信息回答用户的问题。"},
    {"role": "user", "content": f"{context}\n\n用户问题：{question}\n\n请按照以下要求回答：..."}
]
answer = await self.llm_service.generate_text(messages)
```

## 优势

1. **支持完整对话历史**: 大模型现在可以理解整个对话上下文，而不仅仅是当前问题
2. **更好的回答质量**: 基于对话历史的回答更加连贯和准确
3. **统一的接口**: 所有LLM提供者都使用相同的对话历史格式
4. **向后兼容**: 保持了原有的功能，只是改变了参数格式
5. **清晰的语义**: 通过`generate_text_with_history`方法名明确表达意图

## 注意事项

1. **Anthropic特殊处理**: Anthropic API不支持system role，需要特殊处理
2. **本地模型限制**: 本地模型需要将对话历史转换为文本格式
3. **系统消息管理**: 所有提供者都会自动确保系统消息存在
4. **错误处理**: 保持了原有的错误处理机制

## 测试

创建了`test_conversation_history.py`测试脚本来验证新功能是否正常工作。

这次重构解决了用户提出的核心问题：大模型现在可以基于完整的对话历史生成回答，而不是仅仅基于单个问题。
