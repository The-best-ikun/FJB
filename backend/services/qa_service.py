"""
问答服务模块
负责处理用户问题，调用RAG引擎获取答案
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
from services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

class QAService:
    """问答服务类"""
    
    def __init__(self, rag_engine: RAGEngine):
        """
        初始化问答服务
        
        Args:
            rag_engine: RAG引擎实例
        """
        self.rag_engine = rag_engine
        logger.info("问答服务初始化完成")
    
    async def ask_question(self, question: str, context: Optional[str] = None) -> Tuple[str, List[str]]:
        """
        处理用户问题，返回答案和相关来源
        
        Args:
            question: 用户问题
            context: 可选的上下文信息
            
        Returns:
            Tuple[str, List[str]]: (答案, 来源列表)
        """
        try:
            logger.info(f"处理问题: {question}")
            
            # 构建完整的查询，包含上下文信息
            full_query = question
            if context:
                full_query = f"上下文: {context}\n问题: {question}"
            
            # 使用RAG引擎获取答案
            answer, sources = await self.rag_engine.query(full_query)
            
            # 如果没有找到相关答案，返回默认回复
            if not answer or answer.strip() == "":
                answer = self._get_default_answer(question)
                sources = []
            
            logger.info(f"问题处理完成，答案长度: {len(answer)}")
            return answer, sources
            
        except Exception as e:
            logger.error(f"处理问题时出错: {e}")
            # 返回错误提示
            return f"抱歉，处理您的问题时出现了错误: {str(e)}", []
    
    async def ask_question_with_history(self, conversation_history: List[Dict[str, str]]) -> Tuple[str, List[str]]:
        """
        使用对话历史处理用户问题，返回答案和相关来源
        
        Args:
            conversation_history: 完整的对话历史，每个元素包含role和content
            
        Returns:
            Tuple[str, List[str]]: (答案, 来源列表)
        """
        try:
            logger.info(f"处理对话历史问题，历史消息数: {len(conversation_history)}")
            
            # 获取最后一个用户消息作为当前问题
            current_question = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "user":
                    current_question = msg.get("content", "")
                    break
            
            if not current_question:
                return "请提供您的问题。", []
            
            # 使用RAG引擎处理对话历史
            answer, sources = await self.rag_engine.query_with_history(conversation_history)
            
            # 如果没有找到相关答案，返回默认回复
            if not answer or answer.strip() == "":
                answer = self._get_default_answer(current_question)
                sources = []
            
            logger.info(f"对话历史问题处理完成，答案长度: {len(answer)}")
            return answer, sources
            
        except Exception as e:
            logger.error(f"处理对话历史问题时出错: {e}")
            # 返回错误提示
            return f"抱歉，处理您的问题时出现了错误: {str(e)}", []
    # 无法处理问题时返回默认答案
    def _get_default_answer(self, question: str) -> str:
        """
        获取默认答案（当RAG引擎无法提供答案时）
        
        Args:
            question: 用户问题
            
        Returns:
            str: 默认答案
        """
        # 根据问题类型提供不同的默认答案
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ['函数', 'function', '方法', 'method']):
            return "我暂时无法找到关于这个函数的具体信息。建议您检查代码中的函数定义，或者提供更多的上下文信息。"
        
        elif any(keyword in question_lower for keyword in ['类', 'class', '接口', 'interface']):
            return "我暂时无法找到关于这个类的具体信息。建议您检查代码中的类定义，或者提供更多的上下文信息。"
        
        elif any(keyword in question_lower for keyword in ['错误', 'error', 'bug', '问题']):
            return "我暂时无法分析这个错误。建议您检查错误日志，或者提供更多的错误信息和相关代码。"
        
        elif any(keyword in question_lower for keyword in ['如何', 'how', '怎么', '怎样']):
            return "我暂时无法提供具体的实现指导。建议您查看相关的文档或示例代码，或者提供更多的上下文信息。"
        
        else:
            return "我暂时无法回答这个问题。建议您提供更多的上下文信息，或者尝试重新表述您的问题。"
    # 获取相似问题（用于推荐）
    async def get_similar_questions(self, question: str, limit: int = 5) -> List[str]:
        """
        获取相似问题（用于推荐）
        
        Args:
            question: 当前问题
            limit: 返回的问题数量限制
            
        Returns:
            List[str]: 相似问题列表
        """
        try:
            # 使用RAG引擎搜索相似内容
            similar_content = await self.rag_engine.search(question, limit)
            
            # 提取问题（这里简化处理，实际可以更智能地提取，中期提升项目竞争性优化区）
            similar_questions = []
            for content in similar_content:
                # 简单地从内容中提取可能的问题
                if '?' in content:
                    questions = content.split('?')
                    for q in questions:
                        if q.strip() and len(q.strip()) > 10:
                            similar_questions.append(q.strip() + '?')
                            if len(similar_questions) >= limit:
                                break
                
                if len(similar_questions) >= limit:
                    break
            
            return similar_questions[:limit]
            
        except Exception as e:
            logger.error(f"获取相似问题时出错: {e}")
            return []
    # 查看历史记录
    async def get_question_history(self, user_id: Optional[str] = None) -> List[dict]:
        """
        获取问题历史记录
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            List[dict]: 问题历史记录
        """
        # 这里可以实现问题历史记录功能
        # 目前返回空列表
        return []
    # 答案质量评分
    async def rate_answer(self, question: str, answer: str, rating: int) -> bool:
        """
        评价答案质量
        
        Args:
            question: 问题
            answer: 答案
            rating: 评分（1-5）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 这里可以实现答案评价功能，用于改进RAG引擎
            logger.info(f"收到答案评价: 问题='{question[:50]}...', 评分={rating}")
            return True
            
        except Exception as e:
            logger.error(f"评价答案时出错: {e}")
            return False
