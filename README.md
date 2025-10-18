# 代码库智能问答与文档生成 VSCode插件

这是一个基于RAG（检索增强生成）技术的VSCode插件，能够智能回答关于代码库的问题并自动生成代码文档。

## 技术架构

```
VSCode插件(JavaScript/TypeScript)
    ↓ 通过HTTP API调用
后端服务(Python + FastAPI)
    ↓ 内部调用
RAG引擎(LangChain/LlamaIndex) + 向量数据库(ChromaDB)
    ↓ 调用
LLM服务(OpenAI/Anthropic/本地模型)
```

## 功能特性

### VSCode插件功能
- 🤖 **智能问答**: 在VSCode中直接提问关于代码库的问题
- 📝 **文档生成**: 自动为选中的代码生成详细文档
- 🔍 **代码搜索**: 快速搜索代码库中的相关内容
- 📊 **项目概览**: 生成项目结构和概览文档

### 后端服务功能
- 🚀 **FastAPI服务**: 提供RESTful API接口
- 🧠 **RAG引擎**: 结合向量数据库和LLM的智能问答
- 📚 **向量数据库**: 使用ChromaDB存储代码文档向量
- 🔧 **多语言支持**: 支持Python、JavaScript、TypeScript、Java、C++、Go、Rust等

## 项目结构（该项目前端结构已修改为纯JavaScript进行逻辑实现）

```
FJB/
├── package.json                 # VSCode插件配置
├── tsconfig.json               # TypeScript配置
├── src/                        # VSCode插件源代码
│   ├── extension.ts            # 插件主入口
│   ├── apiClient.ts            # API客户端
│   ├── qaPanel.ts              # 问答面板
│   └── docGenerator.ts         # 文档生成器
├── backend/                    # Python后端服务
│   ├── main.py                 # FastAPI主应用
│   ├── requirements.txt        # Python依赖
│   ├── start.py                # 启动脚本
│   ├── env.example             # 环境变量示例
│   ├── services/               # 服务模块
│   │   ├── qa_service.py       # 问答服务
│   │   ├── doc_service.py      # 文档生成服务
│   │   ├── rag_engine.py       # RAG引擎
│   │   ├── vector_db.py        # 向量数据库
│   │   └── llm_service.py      # LLM服务
│   └── utils/                  # 工具模块
│       ├── logger.py           # 日志配置
│       ├── embedding_service.py # 嵌入服务
│       ├── code_analyzer.py    # 代码分析器
│       └── doc_formatter.py    # 文档格式化器
└── README.md                   # 项目文档
```

## 安装和配置

### 1. 安装VSCode插件

```bash
# 安装依赖
npm install

# 编译TypeScript
npm run compile

# 在VSCode中按F5启动调试模式
```

### 2. 配置后端服务

```bash
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 复制环境变量配置
cp env.example .env

# 编辑.env文件，配置API密钥
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. 启动后端服务

```bash
# 使用启动脚本
python start.py

# 或者直接使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 使用方法

### 智能问答
1. 在VSCode中打开命令面板（Ctrl+Shift+P）
2. 输入"智能问答"并选择命令
3. 在问答面板中输入问题
4. 获得基于代码库的智能回答

### 文档生成
1. 在代码编辑器中选择要生成文档的代码
2. 右键选择"生成文档"或使用命令面板
3. 系统会自动生成详细的代码文档
4. 文档会在新标签页中打开

### 代码库索引
1. 后端服务启动后，访问 `http://localhost:8000/api/index-codebase`
2. 提供代码库路径进行索引
3. 索引完成后即可进行智能问答

## API接口

### 健康检查
```
GET /health
```

### 智能问答
```
POST /api/ask
Content-Type: application/json

{
  "question": "这个函数是做什么的？",
  "context": "当前文件路径"
}
```

### 文档生成
```
POST /api/generate-doc
Content-Type: application/json

{
  "code": "function example() { ... }",
  "language": "javascript"
}
```

### 代码库搜索
```
GET /api/search?query=函数定义&limit=10
```

## 配置选项

### 环境变量
- `LLM_PROVIDER`: LLM服务提供者（openai/anthropic/local）
- `OPENAI_API_KEY`: OpenAI API密钥
- `ANTHROPIC_API_KEY`: Anthropic API密钥
- `VECTOR_DB_PATH`: 向量数据库存储路径
- `HOST`: 服务器主机地址
- `PORT`: 服务器端口

### VSCode插件配置
在VSCode设置中可以配置：
- 后端服务URL
- 超时时间
- 日志级别

## 开发指南

### 添加新的代码语言支持
1. 在 `backend/utils/code_analyzer.py` 中添加语言分析逻辑
2. 更新 `backend/services/vector_db.py` 中的文件扩展名列表
3. 在 `backend/utils/doc_formatter.py` 中添加语言特定的文档格式

### 集成新的LLM服务
1. 在 `backend/services/llm_service.py` 中实现新的提供者类
2. 继承 `LLMProvider` 抽象基类
3. 实现必要的方法：`generate_text`, `initialize`, `get_stats`

### 自定义向量数据库
1. 在 `backend/services/vector_db.py` 中修改数据库实现
2. 确保实现所有必要的方法
3. 更新 `backend/services/rag_engine.py` 中的调用

## 故障排除

### 常见问题

1. **后端服务无法启动**
   - 检查Python版本（需要3.8+）
   - 确认所有依赖已安装
   - 检查端口是否被占用

2. **VSCode插件无法连接后端**
   - 确认后端服务正在运行
   - 检查防火墙设置
   - 验证API端点URL配置

3. **LLM服务无响应**
   - 检查API密钥配置
   - 确认网络连接
   - 查看日志文件获取详细错误信息

4. **向量数据库问题**
   - 检查存储路径权限
   - 确认磁盘空间充足
   - 尝试重新索引代码库

### 日志查看
- VSCode插件日志：开发者工具控制台
- 后端服务日志：`backend/logs/` 目录
- 系统日志：操作系统日志文件

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请创建 Issue 或联系开发团队。
