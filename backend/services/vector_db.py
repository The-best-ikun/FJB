"""
向量数据库服务模块
负责管理代码文档的向量存储和检索
"""

import logging
import os
# 统一 HF_ENDPOINT，避免出现双斜杠导致的 404（如 https://hf-mirror.com//api/...）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 提前设置 
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np

logger = logging.getLogger(__name__)

class VectorDatabase:
    """向量数据库类，使用ChromaDB作为后端"""
    
    def __init__(self, persist_directory: str = "./chroma_db", embedding_service: Optional[object] = None):
        """
        初始化向量数据库
        
        Args:
            persist_directory: 数据库持久化目录
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        logger.info(f"向量数据库初始化，持久化目录: {persist_directory}")

        # Embedding service 注入（优先使用外部服务）
        self.embedding_service = embedding_service

        

        # 原始 CodeBERT 初始化逻辑已注释（保留以便回退或调试）
        # try:
        #     import torch
        #     from transformers import AutoTokenizer, AutoModel
        #     print(f"当前镜像地址: {os.getenv('HF_ENDPOINT', 'https://huggingface.co')}")
        #     model_name = os.getenv('CODE_EMBEDDING_MODEL', 'microsoft/codebert-base')
        #     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        #     self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        #     self._embedding_model = AutoModel.from_pretrained(model_name)
        #     self._embedding_model.to(device)
        #     self._embedding_model.eval()
        #     with torch.no_grad():
        #         sample = self._tokenizer("print(1)", return_tensors='pt')
        #         sample = {k: v.to(device) for k, v in sample.items()}
        #         out = self._embedding_model(**sample)
        #         hidden = out.last_hidden_state
        #         self._embedding_dim = hidden.size(-1)
        #     self._embed_available = True
        #     logger.info(f"CodeBERT 嵌入模型已初始化 (model={model_name}, dim={self._embedding_dim}, device={device})")
        # except Exception as e:
        #     logger.warning(f"未能初始化 CodeBERT 嵌入模型，将回退到占位符嵌入: {e}")
    
    async def initialize(self):
        """初始化向量数据库连接和集合"""
        try:
            # 确保持久化目录存在
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 创建ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            collection_name = "codebase_documents"
            try:
                self.collection = self.client.get_collection(collection_name)
                logger.info(f"连接到现有集合: {collection_name}")
            except ValueError:
                # 集合不存在，创建新集合
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "代码库文档向量存储"}
                )
                logger.info(f"创建新集合: {collection_name}")
            
            logger.info("向量数据库初始化完成")
            
        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    async def add_document(self, content: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """
        添加文档到向量数据库
        
        Args:
            content: 文档内容
            embedding: 文档的嵌入向量
            metadata: 文档元数据
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 生成文档ID
            doc_id = metadata.get('id', f"doc_{len(self.collection.get()['ids'])}")
            
            # 添加文档到集合
            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"文档添加成功: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    async def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        相似性搜索
        
        Args:
            query_embedding: 查询的嵌入向量
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 执行相似性搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 格式化结果
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i],  # 将距离转换为相似度分数
                        'source': results['metadatas'][0][i].get('source', 'unknown')
                    })
            
            logger.info(f"相似性搜索完成，返回 {len(formatted_results)} 个结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            return []
    
    async def update_document(self, doc_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """
        更新文档
        
        Args:
            doc_id: 文档ID
            content: 新的文档内容
            embedding: 新的嵌入向量
            metadata: 新的元数据
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 更新文档
            self.collection.update(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata]
            )

            logger.info(f"文档更新成功: {doc_id}")
            return True

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
            # 删除文档
            self.collection.delete(ids=[doc_id])

            logger.info(f"文档删除成功: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Optional[Dict[str, Any]]: 文档信息，如果不存在则返回None
        """
        try:
            # 获取文档
            results = self.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas']
            )
            
            if results['documents'] and results['documents'][0]:
                return {
                    'id': doc_id,
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    async def get_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取所有文档
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        try:
            # 获取所有文档
            results = self.collection.get(
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            documents = []
            if results['documents']:
                for i in range(len(results['documents'])):
                    documents.append({
                        'id': results['ids'][i],
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    })
            
            return documents
            
        except Exception as e:
            logger.error(f"获取所有文档失败: {e}")
            return []
    
    async def index_codebase(self, codebase_path: str):
        """
        索引整个代码库
        
        Args:
            codebase_path: 代码库路径
        """
        try:
            logger.info(f"开始索引代码库: {codebase_path}")
            
            # 这里应该实现代码库遍历和文档提取逻辑
      
            
            import os
            import glob
            
            # 支持的代码文件扩展名
            code_extensions = ['*.py', '*.js', '*.ts', '*.java', '*.cpp', '*.c', '*.go', '*.rs']
            
            total_files = 0
            indexed_files = 0
            
            for ext in code_extensions:
                pattern = os.path.join(codebase_path, '**', ext)
                files = glob.glob(pattern, recursive=True)
                total_files += len(files)
                
                for file_path in files:
                    try:
                        # 读取文件内容
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 创建元数据
                        metadata = {
                            'source': file_path,
                            'type': 'code_file',
                            'extension': os.path.splitext(file_path)[1],
                            'size': len(content)
                        }
                        
                        # 生成嵌入向量：优先使用注入的 EmbeddingService
                        embedding = None
                        if self.embedding_service:
                            try:
                                # embedding_service.embed_text 可能是异步或同步接口；支持两者
                                import asyncio, inspect
                                if inspect.iscoroutinefunction(self.embedding_service.embed_text):
                                    embedding = await self.embedding_service.embed_text(content)
                                else:
                                    # 在线程池中调用同步 embed_text
                                    loop = asyncio.get_running_loop()
                                    embedding = await loop.run_in_executor(None, self.embedding_service.embed_text, content)
                            except Exception as e:
                                logger.error(f"使用注入的 EmbeddingService 生成嵌入失败，尝试回退: {e}")

                        # 如果注入服务不可用或生成失败，回退到原始本地/占位符逻辑（原逻辑被注释保留）
                        if embedding is None:
                            try:
                                # 回退：如果原先在类中启用了 CodeBERT，此处可调用 _embed_text
                                import asyncio
                                loop = asyncio.get_running_loop()
                                embedding = await loop.run_in_executor(None, self._embed_text, content)
                            except Exception:
                                # 最终回退为零向量
                                embedding = [0.0] * (getattr(self, '_embedding_dim', 384) or 384)
                        
                        # 添加到向量数据库
                        success = await self.add_document(content, embedding, metadata)
                        if success:
                            indexed_files += 1
                        
                    except Exception as e:
                        logger.error(f"处理文件 {file_path} 时出错: {e}")
            
            logger.info(f"代码库索引完成: {indexed_files}/{total_files} 个文件")
            
        except Exception as e:
            logger.error(f"索引代码库失败: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 获取集合信息
            count = self.collection.count()
            
            # 获取一些示例文档
            sample_docs = self.collection.get(limit=10, include=['metadatas'])
            
            # 统计文件类型
            file_types = {}
            if sample_docs['metadatas']:
                for metadata in sample_docs['metadatas']:
                    ext = metadata.get('extension', 'unknown')
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'total_documents': count,
                'file_types': file_types,
                'persist_directory': self.persist_directory,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'error': str(e)}
    
    async def close(self):
        """关闭数据库连接"""
        try:
            if self.client:
                # ChromaDB会自动处理连接关闭
                logger.info("向量数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接时出错: {e}")
    
    async def reset(self):
        """重置数据库（删除所有数据）"""
        try:
            if self.client:
                # 删除集合
                self.client.delete_collection("codebase_documents")
                
                # 重新创建集合
                self.collection = self.client.create_collection(
                    name="codebase_documents",
                    metadata={"description": "代码库文档向量存储"}
                )
                
                logger.info("数据库已重置")
                
        except Exception as e:
            logger.error(f"重置数据库失败: {e}")
            raise
    # 生成嵌入式向量
    def _embed_text(self, text: str) -> List[float]:
        """
        使用已加载的 CodeBERT 模型生成文本嵌入向量（同步函数，供 run_in_executor 调用）

        返回归一化的向量列表。
        """


        # 如果模型不可用，回退到占位符模式
        if not self._embed_available or not self._embedding_model or not self._tokenizer:
            # 回退到固定维度的零向量
            dim = self._embedding_dim or 384
            return [0.0] * dim

        try:
            import torch

            device = next(self._embedding_model.parameters()).device

            # 对长文本进行截断，避免超长序列
            max_length = int(os.getenv('CODE_EMBEDDING_MAX_LENGTH', '512'))
            inputs = self._tokenizer(text, truncation=True, max_length=max_length, return_tensors='pt')
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._embedding_model(**inputs)
                hidden = outputs.last_hidden_state  # (batch, seq, hidden)

                # 使用平均池化作为句子表示
                emb = hidden.mean(dim=1).squeeze(0)

                # L2 归一化
                emb = emb / (emb.norm(p=2) + 1e-12)

                # 转换为 Python list
                return emb.cpu().numpy().tolist()

        except Exception as e:
            logger.error(f"生成嵌入时出错: {e}")
            dim = self._embedding_dim or 384
            return [0.0] * dim
    
    async def index_codebase_with_files(self, workspace_path: str, code_files: List[Dict[str, Any]]):
        """
        使用提供的文件列表索引代码库
        
        Args:
            workspace_path: 工作区路径
            code_files: 代码文件列表，每个元素包含path, relativePath, extension, size
        """
        try:
            logger.info(f"开始索引代码库: {workspace_path}, 文件数量: {len(code_files)}")

            # 打印收到的第一个元素类型，便于诊断前端是否传入了 Pydantic 模型对象
            if code_files and len(code_files) > 0:
                try:
                    sample = code_files[0]
                    logger.info(f"收到 code_files 首元素类型: {type(sample)}, repr_sample: {repr(sample)[:200]}")
                except Exception:
                    pass

            # 安全访问器，支持 dict 或具有属性的对象（例如 Pydantic BaseModel）
            def _get_field(obj, key, default=None):
                if obj is None:
                    return default
                if isinstance(obj, dict):
                    return obj.get(key, default)
                # 允许访问驼峰或小写属性名
                if hasattr(obj, key):
                    return getattr(obj, key)
                # 尝试小写首字母访问（relativePath -> relative_path）
                alt = key[0].lower() + key[1:] if len(key) > 1 else key.lower()
                if hasattr(obj, alt):
                    return getattr(obj, alt)
                # 尝试 dict-like .dict() for pydantic
                if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
                    try:
                        return obj.dict().get(key, obj.dict().get(alt, default))
                    except Exception:
                        pass
                return default

            indexed_files = 0
            failed_files = 0

            for file_info in code_files:
                try:
                    file_path = _get_field(file_info, 'path')
                    relative_path = _get_field(file_info, 'relativePath') or _get_field(file_info, 'relative_path')
                    extension = _get_field(file_info, 'extension')
                    file_size = _get_field(file_info, 'size')

                    # 如果必要字段缺失，记录并跳过
                    if not file_path:
                        logger.warning(f"跳过无效的 file_info 条目（缺少 path）：{repr(file_info)[:200]}")
                        failed_files += 1
                        continue
                    
                    # 跳过过大的文件（超过1MB）
                    if file_size > 1024 * 1024:
                        logger.warning(f"跳过过大文件: {relative_path} ({file_size} bytes)")
                        continue
                    
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 跳过空文件
                    if not content.strip():
                        continue
                    
                    # 创建元数据
                    metadata = {
                        'source': relative_path,
                        'type': 'code_file',
                        'extension': extension,
                        'size': file_size,
                        'workspace': workspace_path
                    }
                    
                    # 生成嵌入向量
                    embedding = None
                    if self.embedding_service:
                        try:
                            import asyncio, inspect
                            if inspect.iscoroutinefunction(self.embedding_service.embed_text):
                                embedding = await self.embedding_service.embed_text(content)
                            else:
                                embedding = self.embedding_service.embed_text(content)
                        except Exception as e:
                            logger.warning(f"使用外部嵌入服务失败: {e}")
                            embedding = None
                    
                    # 如果没有外部嵌入服务，使用占位符
                    if embedding is None:
                        embedding = [0.0] * 768  # 默认维度
                    
                    # 添加到向量数据库
                    success = await self.add_document(
                        content=content,
                        embedding=embedding,
                        metadata=metadata
                    )
                    
                    if success:
                        indexed_files += 1
                        if indexed_files % 10 == 0:
                            logger.info(f"已索引 {indexed_files} 个文件...")
                    else:
                        failed_files += 1
                except Exception as e:
                    rel = _get_field(file_info, 'relativePath') or _get_field(file_info, 'relative_path') or 'unknown'
                    logger.warning(f"索引文件失败 {rel}: {e}")
                    failed_files += 1
            
            logger.info(f"代码库索引完成: 成功 {indexed_files} 个，失败 {failed_files} 个")
            return True
            
        except Exception as e:
            logger.error(f"索引代码库失败: {e}")
            return False