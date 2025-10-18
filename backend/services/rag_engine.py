"""
RAG引擎模块
负责检索增强生成，结合向量数据库和LLM服务
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
import asyncio
from services.vector_db import VectorDatabase
from services.llm_service import LLMService
from utils.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class RAGEngine:
    """RAG引擎类"""
    
    def __init__(self, vector_db: VectorDatabase):
        """
        初始化RAG引擎
        
        Args:
            vector_db: 向量数据库实例
        """
        self.vector_db = vector_db
        self.llm_service = LLMService()

        # 初始化嵌入模型服务
        self.embedding_service = EmbeddingService()
        logger.info("RAG引擎初始化完成")
    
    async def initialize(self):
        """初始化RAG引擎的各个组件"""
        try:
            # 初始化LLM服务
            await self.llm_service.initialize()
            
            # 初始化嵌入服务
            await self.embedding_service.initialize()
            
            logger.info("RAG引擎所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"RAG引擎初始化失败: {e}")
            raise
    
    async def query(self, question: str, top_k: int = 5) -> Tuple[str, List[str]]:
        """
        处理用户查询，返回答案和相关来源
        
        Args:
            question: 用户问题
            top_k: 检索的相关文档数量
            
        Returns:
            Tuple[str, List[str]]: (答案, 来源列表)
        """
        try:
            logger.info(f"处理RAG查询: {question}")
            
            # 1. 检索相关文档
            relevant_docs = await self._retrieve_relevant_documents(question, top_k)
            
            if not relevant_docs:
                # 如果检索不到相关文档，不应直接返回“无法回答”。
                # 对于常识性或无需上下文的问题，直接调用LLM进行回答更合适。
                logger.info("未找到相关文档，改为直接调用LLM生成回答")
                try:
                    messages = [
                        {"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"},
                        {"role": "user", "content": f"请直接回答以下问题：\n\n{question}\n\n请用中文，尽量简明扼要。"}
                    ]
                    answer = await self.llm_service.generate_text(messages)
                    return answer, []
                except Exception as e:
                    logger.error(f"直接调用LLM回答失败: {e}")
                
            
            # 2. 构建上下文
            context = self._build_context(relevant_docs)
            
            # 3. 生成答案
            answer = await self._generate_answer(question, context)
            
            # 4. 提取来源信息
            sources = self._extract_sources(relevant_docs)
            
            logger.info(f"RAG查询完成，答案长度: {len(answer)}")
            return answer, sources
            
        except Exception as e:
            logger.error(f"RAG查询处理失败: {e}")
            return f"处理查询时出现错误: {str(e)}", []
    
    async def query_with_history(self, conversation_history: List[Dict[str, str]], top_k: int = 5) -> Tuple[str, List[str]]:
        """
        使用对话历史处理用户查询，返回答案和相关来源
        
        Args:
            conversation_history: 完整的对话历史，每个元素包含role和content
            top_k: 检索的相关文档数量
            
        Returns:
            Tuple[str, List[str]]: (答案, 来源列表)
        """
        try:
            logger.info(f"处理RAG对话历史查询，历史消息数: {len(conversation_history)}")
            
            # 获取最后一个用户消息作为当前问题
            current_question = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "user":
                    current_question = msg.get("content", "")
                    break
            
            if not current_question:
                return "请提供您的问题。", []
            
            # 1. 检索相关文档（基于当前问题）
            relevant_docs = await self._retrieve_relevant_documents(current_question, top_k)
            
            if not relevant_docs:
                # 如果检索不到相关文档，直接使用LLM基于对话历史回答
                logger.info("未找到相关文档，使用对话历史直接调用LLM生成回答")
                try:
                    answer = await self.llm_service.generate_text(conversation_history)
                    return answer, []
                except Exception as e:
                    logger.error(f"直接调用LLM回答失败: {e}")
                    return "抱歉，无法回答您的问题。", []
            
            # 2. 构建上下文
            context = self._build_context(relevant_docs)
            
            # 3. 构建包含对话历史和上下文的完整消息
            messages = [
                {"role": "system", "content": f"你是一个专业的代码助手，请基于以下相关信息回答用户的问题。\n\n{context}"},
            ] + conversation_history
            
            # 4. 生成答案
            answer = await self.llm_service.generate_text(messages)
            
            # 5. 提取来源信息
            sources = self._extract_sources(relevant_docs)
            
            logger.info(f"RAG对话历史查询完成，答案长度: {len(answer)}")
            return answer, sources
            
        except Exception as e:
            logger.error(f"RAG对话历史查询处理失败: {e}")
            return f"处理查询时出现错误: {str(e)}", []
    
    async def _retrieve_relevant_documents(self, question: str, top_k: int) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            question: 用户问题
            top_k: 返回的文档数量
            
        Returns:
            List[Dict[str, Any]]: 相关文档列表
        """
        try:
            # 生成问题的嵌入向量
            question_embedding = await self.embedding_service.embed_text(question)
            
            # 在向量数据库中搜索相似文档
            similar_docs = await self.vector_db.similarity_search(
                query_embedding=question_embedding,
                top_k=top_k
            )
            
            logger.info(f"检索到 {len(similar_docs)} 个相关文档")
            return similar_docs
            
        except Exception as e:
            logger.error(f"检索相关文档失败: {e}")
            return []
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        构建上下文信息
        
        Args:
            documents: 相关文档列表
            
        Returns:
            str: 构建的上下文
        """
        context_parts = ["相关文档信息："]
        
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '')
            source = doc.get('source', 'unknown')
            score = doc.get('score', 0)
            
            context_parts.append(f"\n文档 {i} (来源: {source}, 相似度: {score:.3f}):")
            context_parts.append(content[:500])  # 限制每个文档的长度
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    async def _generate_answer(self, question: str, context: str) -> str:
        """
        基于上下文生成答案
        
        Args:
            question: 用户问题
            context: 上下文信息
            
        Returns:
            str: 生成的答案
        """
        try:
            # 构建对话消息
            messages = [
                {"role": "system", "content": "你是一个专业的代码助手，请基于以下相关信息回答用户的问题。"},
                {"role": "user", "content": f"""{context}

用户问题：{question}

请按照以下要求回答：
1. 基于提供的相关信息回答问题
2. 如果信息不足，请明确说明
3. 提供具体、准确的答案
4. 如果涉及代码，请提供清晰的示例
5. 使用中文回答

答案："""}
            ]
            
            # 使用LLM生成答案
            answer = await self.llm_service.generate_text(messages)
            
            return answer
            
        except Exception as e:
            logger.error(f"生成答案失败: {e}")
            return "抱歉，生成答案时出现了错误。"
    
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        提取来源信息
        
        Args:
            documents: 相关文档列表
            
        Returns:
            List[str]: 来源列表
        """
        sources = []
        for doc in documents:
            source = doc.get('source', '')
            if source and source not in sources:
                sources.append(source)
        
        return sources
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            # 生成查询的嵌入向量
            query_embedding = await self.embedding_service.embed_text(query)
            
            # 在向量数据库中搜索
            results = await self.vector_db.similarity_search(
                query_embedding=query_embedding,
                top_k=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """
        添加文档到RAG系统
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 生成文档的嵌入向量
            embedding = await self.embedding_service.embed_text(content)
            
            # 添加到向量数据库
            success = await self.vector_db.add_document(
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            if success:
                logger.info(f"文档添加成功: {metadata.get('source', 'unknown')}")
            else:
                logger.error("文档添加失败")
            
            return success
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    async def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        更新文档
        
        Args:
            doc_id: 文档ID
            content: 新的文档内容
            metadata: 新的元数据
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 生成新的嵌入向量
            embedding = await self.embedding_service.embed_text(content)
            
            # 更新向量数据库中的文档
            success = await self.vector_db.update_document(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            return success
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            success = await self.vector_db.delete_document(doc_id)
            return success
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取RAG引擎统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 获取向量数据库统计信息
            db_stats = await self.vector_db.get_stats()
            
            # 获取LLM服务统计信息
            llm_stats = await self.llm_service.get_stats()
            
            return {
                "vector_db": db_stats,
                "llm_service": llm_stats,
                "embedding_service": {
                    "status": "active",
                    "model": self.embedding_service.model_name
                }
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
