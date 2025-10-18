"""
FastAPI后端服务主文件
提供RESTful API接口，处理VSCode插件的请求
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import uvicorn
import logging
from datetime import datetime

# 尝试加载项目根目录下的 .env 文件，方便本地开发时配置 API keys 等环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    _dotenv_loaded = True
except Exception:
    _dotenv_loaded = False

# 导入自定义模块
from services.qa_service import QAService
from services.doc_service import DocService
from services.rag_engine import RAGEngine
from services.vector_db import VectorDatabase
from utils.embedding_service import EmbeddingService
from utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)

if _dotenv_loaded:
    logger.info("已加载 .env 环境变量（如果存在）")
else:
    logger.warning("未检测到 python-dotenv，.env 文件不会自动加载。若需加载请安装 python-dotenv")

# 创建FastAPI应用实例
app = FastAPI(
    title="代码库智能问答与文档生成API",
    description="基于RAG的代码库智能问答和文档生成服务",
    version="1.0.0"
)

# 配置CORS中间件，允许VSCode插件跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
qa_service: Optional[QAService] = None
doc_service: Optional[DocService] = None
rag_engine: Optional[RAGEngine] = None
vector_db: Optional[VectorDatabase] = None

# Pydantic模型定义
class QuestionRequest(BaseModel):
    """问答请求模型"""
    question: str
    context: Optional[str] = None

class ConversationMessage(BaseModel):
    """对话消息模型"""
    role: str  # "system", "user", "assistant"
    content: str

class ConversationRequest(BaseModel):
    """对话历史请求模型"""
    conversationHistory: List[ConversationMessage]

class QuestionResponse(BaseModel):
    """问答响应模型"""
    answer: str
    timestamp: str
    sources: Optional[List[str]] = None

class DocRequest(BaseModel):
    """文档生成请求模型"""
    code: str
    language: Optional[str] = None

class DocResponse(BaseModel):
    """文档生成响应模型"""
    documentation: str
    timestamp: str
    language: str

class CodeFile(BaseModel):
    """代码文件模型"""
    path: str
    relativePath: str
    extension: str
    size: int

class CodebaseIndexRequest(BaseModel):
    """代码库索引请求模型"""
    workspacePath: str
    codeFiles: List[CodeFile]

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    services: dict

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    global qa_service, doc_service, rag_engine, vector_db
    
    logger.info("正在启动代码库智能问答与文档生成服务...")
    
    try:
        # 打印关键环境变量，帮助调试 .env 加载情况
        logger.info(f"LLM_PROVIDER={os.getenv('LLM_PROVIDER')}")
        logger.info(f"OPENAI_API_KEY set?={'YES' if os.getenv('OPENAI_API_KEY') else 'NO'}")
        logger.info(f"ANTHROPIC_API_KEY set?={'YES' if os.getenv('ANTHROPIC_API_KEY') else 'NO'}")

        # 初始化嵌入服务（用于文本到向量的统一入口）
        logger.info("初始化嵌入服务...")
        embedding_service = EmbeddingService()
        await embedding_service.initialize()

        # 初始化向量数据库并注入 embedding_service
        logger.info("初始化向量数据库...")
        vector_db = VectorDatabase(embedding_service=embedding_service)
        await vector_db.initialize()

        # 初始化RAG引擎
        logger.info("初始化RAG引擎...")
        rag_engine = RAGEngine(vector_db)
        await rag_engine.initialize()

        # 初始化问答服务
        logger.info("初始化问答服务...")
        qa_service = QAService(rag_engine)

        # 初始化文档生成服务
        logger.info("初始化文档生成服务...")
        doc_service = DocService(rag_engine)

        logger.info("所有服务初始化完成！")

    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("正在关闭服务...")
    
    if vector_db:
        await vector_db.close()
    
    logger.info("服务已关闭")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    services_status = {
        "vector_db": vector_db is not None,
        "rag_engine": rag_engine is not None,
        "qa_service": qa_service is not None,
        "doc_service": doc_service is not None
    }
    
    return HealthResponse(
        status="healthy" if all(services_status.values()) else "unhealthy",
        timestamp=datetime.now().isoformat(),
        services=services_status
    )

@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    问答接口
    接收用户问题，返回智能回答
    """
    if not qa_service:
        raise HTTPException(status_code=503, detail="问答服务未初始化")
    
    try:
        logger.info(f"收到问答请求: {request.question}")
        
        # 调用问答服务
        answer, sources = await qa_service.ask_question(
            question=request.question,
            context=request.context
        )
        
        logger.info("问答请求处理完成")
        
        return QuestionResponse(
            answer=answer,
            timestamp=datetime.now().isoformat(),
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"问答请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"问答服务错误: {str(e)}")

@app.post("/api/ask-with-history", response_model=QuestionResponse)
async def ask_question_with_history(request: ConversationRequest):
    """
    支持对话历史的问答接口
    接收完整的对话历史，返回智能回答
    """
    if not qa_service:
        raise HTTPException(status_code=503, detail="问答服务未初始化")
    
    try:
        logger.info(f"收到对话历史问答请求，历史消息数: {len(request.conversationHistory)}")
        
        # 将对话历史转换为字典格式
        conversation_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in request.conversationHistory
        ]
        
        # 调用问答服务的新方法（需要先在QAService中添加）
        answer, sources = await qa_service.ask_question_with_history(conversation_history)
        
        logger.info("对话历史问答请求处理完成")
        
        return QuestionResponse(
            answer=answer,
            timestamp=datetime.now().isoformat(),
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"对话历史问答请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"问答服务错误: {str(e)}")

@app.post("/api/generate-doc", response_model=DocResponse)
async def generate_documentation(request: DocRequest):
    """
    文档生成接口
    接收代码，返回生成的文档
    """
    if not doc_service:
        raise HTTPException(status_code=503, detail="文档生成服务未初始化")
    
    try:
        logger.info(f"收到文档生成请求，代码长度: {len(request.code)}")
        
        # 调用文档生成服务
        documentation = await doc_service.generate_documentation(
            code=request.code,
            language=request.language
        )
        
        logger.info("文档生成请求处理完成")
        
        return DocResponse(
            documentation=documentation,
            timestamp=datetime.now().isoformat(),
            language=request.language or "unknown"
        )
        
    except Exception as e:
        logger.error(f"文档生成请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档生成服务错误: {str(e)}")

@app.post("/api/index-codebase")
async def index_codebase(request: CodebaseIndexRequest, background_tasks: BackgroundTasks):
    """
    代码库索引接口
    将代码库内容索引到向量数据库中
    """
    if not vector_db:
        raise HTTPException(status_code=503, detail="向量数据库未初始化")
    
    try:
        logger.info(f"开始索引代码库: {request.workspacePath}, 文件数量: {len(request.codeFiles)}")
        
        # 在后台任务中执行索引
        background_tasks.add_task(
            vector_db.index_codebase_with_files,
            request.workspacePath,
            request.codeFiles
        )
        
        return {
            "message": f"代码库索引任务已启动，共 {len(request.codeFiles)} 个文件",
            "status": "processing",
            "fileCount": len(request.codeFiles)
        }
        
    except Exception as e:
        logger.error(f"代码库索引失败: {e}")
        raise HTTPException(status_code=500, detail=f"代码库索引错误: {str(e)}")

@app.get("/api/search")
async def search_codebase(query: str, limit: int = 10):
    """
    代码库搜索接口
    在索引的代码库中搜索相关内容
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG引擎未初始化")
    
    try:
        logger.info(f"收到搜索请求: {query}")
        
        # 执行搜索
        results = await rag_engine.search(query, limit)
        
        return {
            "query": query,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"搜索请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )
