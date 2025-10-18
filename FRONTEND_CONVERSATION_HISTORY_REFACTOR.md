# 前端对话历史支持重构总结

## 修改概述

为了支持完整的对话历史功能，我们对前端和后端都进行了相应的修改，确保大模型能够基于整个对话上下文生成回答，而不是仅仅基于当前问题。

## 前端修改

### 1. QAPanel类修改 (`src/qaPanel.js`)

#### 新增属性
```javascript
this._conversationHistory = []; // 存储对话历史
```

#### 修改的方法

**`_handleAskQuestion`方法**
- 添加用户消息到对话历史
- 调用新的API方法传递完整对话历史
- 将助手回答添加到对话历史

**`_handleClearHistory`方法**
- 同时清空对话历史和UI显示

**`show`方法**
- 在面板初始化时恢复保存的对话历史
- 在面板关闭时保存对话历史到状态中

### 2. ApiClient类修改 (`src/apiClient.js`)

#### 新增方法
```javascript
async askQuestionWithHistory(conversationHistory) {
    // 发送对话历史到新的API端点
    const response = await this.client.post('/api/ask-with-history', {
        conversationHistory
    });
    return response.data.answer;
}
```

#### 保持向后兼容
- 原有的`askQuestion`方法仍然保留，确保向后兼容

## 后端修改

### 1. API接口修改 (`backend/main.py`)

#### 新增请求模型
```python
class ConversationMessage(BaseModel):
    """对话消息模型"""
    role: str  # "system", "user", "assistant"
    content: str

class ConversationRequest(BaseModel):
    """对话历史请求模型"""
    conversationHistory: List[ConversationMessage]
```

#### 新增API端点
```python
@app.post("/api/ask-with-history", response_model=QuestionResponse)
async def ask_question_with_history(request: ConversationRequest):
    """支持对话历史的问答接口"""
    # 处理对话历史请求
```

### 2. QAService修改 (`backend/services/qa_service.py`)

#### 新增方法
```python
async def ask_question_with_history(self, conversation_history: List[Dict[str, str]]) -> Tuple[str, List[str]]:
    """使用对话历史处理用户问题"""
    # 获取最后一个用户消息作为当前问题
    # 调用RAG引擎的对话历史方法
```

### 3. RAGEngine修改 (`backend/services/rag_engine.py`)

#### 新增方法
```python
async def query_with_history(self, conversation_history: List[Dict[str, str]], top_k: int = 5) -> Tuple[str, List[str]]:
    """使用对话历史处理用户查询"""
    # 基于当前问题检索相关文档
    # 构建包含对话历史和上下文的完整消息
    # 使用LLM生成答案
```

## 工作流程

### 1. 用户提问流程
1. 用户在VSCode插件中输入问题
2. 前端将问题添加到对话历史
3. 前端调用`askQuestionWithHistory`API，传递完整对话历史
4. 后端接收对话历史，提取当前问题
5. RAG引擎基于当前问题检索相关文档
6. 构建包含对话历史和上下文的完整消息
7. LLM基于完整上下文生成回答
8. 返回答案给前端显示

### 2. 对话历史管理
- **保存**: 面板关闭时自动保存对话历史到VSCode状态
- **恢复**: 面板重新打开时自动恢复对话历史
- **清空**: 用户点击清空按钮时同时清空历史和UI

## 优势

1. **完整上下文**: 大模型现在可以理解整个对话历史，生成更连贯的回答
2. **状态持久化**: 对话历史在VSCode重启后仍然保持
3. **向后兼容**: 原有的API接口仍然可用
4. **智能检索**: RAG引擎基于当前问题检索相关文档，同时考虑对话历史
5. **错误处理**: 完善的错误处理机制

## 使用示例

### 前端使用
```javascript
// 创建对话历史
const conversationHistory = [
    { role: "system", content: "你是一个专业的代码助手。" },
    { role: "user", content: "什么是Python装饰器？" },
    { role: "assistant", content: "装饰器是一种设计模式..." },
    { role: "user", content: "能给我一个例子吗？" }
];

// 发送请求
const answer = await apiClient.askQuestionWithHistory(conversationHistory);
```

### 后端API调用
```bash
curl -X POST "http://localhost:8000/api/ask-with-history" \
  -H "Content-Type: application/json" \
  -d '{
    "conversationHistory": [
      {"role": "system", "content": "你是一个专业的代码助手。"},
      {"role": "user", "content": "什么是Python装饰器？"},
      {"role": "assistant", "content": "装饰器是一种设计模式..."},
      {"role": "user", "content": "能给我一个例子吗？"}
    ]
  }'
```

## 测试

创建了`test_conversation_api.py`测试脚本来验证新的API功能。

## 注意事项

1. **状态管理**: 对话历史存储在VSCode的webview状态中，重启VSCode后会恢复
2. **性能考虑**: 长对话历史可能影响API响应时间，建议设置合理的对话长度限制
3. **错误处理**: 如果对话历史格式不正确，API会返回相应的错误信息
4. **安全性**: 对话历史包含用户输入，需要注意数据安全

这次重构完全解决了用户提出的问题：前端现在可以传递完整的对话历史给后端，大模型能够基于整个对话上下文生成更准确、更连贯的回答。
