"""
嵌入服务模块
负责将文本转换为向量嵌入
"""

import logging
from typing import List
import numpy as np
import os
# 延迟导入 transformers 和 torch，以免在没有这些库时影响启动
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 提前设置 
logger = logging.getLogger(__name__)

# 尝试导入sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as e:
    # 记录完整异常信息，便于调试为什么导入失败（可能是缺少依赖如 torch、DLL或路径问题）
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.error("无法导入 sentence-transformers：%s", e)



class EmbeddingService:
    """嵌入服务类"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):

        model_name = os.getenv('CODE_EMBEDDING_MODEL', 'microsoft/codebert-base')
        """
        初始化嵌入服务
        
        Args:
            model_name: 嵌入模型名称
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # 默认维度
    
    async def initialize(self):
        """初始化嵌入模型"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info(f"正在加载嵌入模型: {self.model_name}")
                print(f"正在加载嵌入模型: {self.model_name}")
                # 对 CodeBERT 手动构建模块：Transformer + Pooling(CLS)
                if 'codebert' in self.model_name.lower():
                    from sentence_transformers import SentenceTransformer, models
                    word_embedding_model = models.Transformer(self.model_name)
                    pooling_model = models.Pooling(
                        word_embedding_model.get_word_embedding_dimension(),
                        pooling_mode_cls_token=True,
                        pooling_mode_mean_tokens=False,
                        pooling_mode_max_tokens=False,
                    )
                    self.model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
                    logger.info("使用 CLS pooling 策略加载 CodeBERT 模型")
                else:
                    self.model = SentenceTransformer(self.model_name)
                # 获取模型输出的向量维度
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"嵌入模型加载完成，维度: {self.dimension}")
            else:
                logger.warning("sentence-transformers未安装，使用简单的嵌入方法")
                self.model = None
                
        except Exception as e:
            logger.error(f"嵌入模型初始化失败: {e}")
            # 使用简单的嵌入方法作为后备
            self.model = None
    
    async def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            if self.model:
                # 使用sentence-transformers生成嵌入
                embedding = self.model.encode(text)
                emb_list = embedding.tolist()
            else:
                # 使用简单的嵌入方法
                emb_list = self._simple_embed(text)

            # 记录嵌入维度和是否为零向量的诊断信息（不打印完整向量以免过长）
            is_zero = all(v == 0.0 for v in emb_list)
            logger.info(f"生成嵌入: dim={len(emb_list)}, zero={is_zero}")
            return emb_list
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            # 返回零向量作为后备
            zero_vec = [0.0] * self.dimension
            logger.info(f"使用零向量作为后备: dim={len(zero_vec)}")
            return zero_vec
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            if self.model:
                # 使用sentence-transformers批量生成嵌入
                embeddings = self.model.encode(texts)
                return embeddings.tolist()
            else:
                # 使用简单的嵌入方法
                return [self._simple_embed(text) for text in texts]
                
        except Exception as e:
            logger.error(f"批量生成嵌入向量失败: {e}")
            # 返回零向量作为后备
            return [[0.0] * self.dimension for _ in texts]
    
    def _simple_embed(self, text: str) -> List[float]:
        """
        简单的嵌入方法（当sentence-transformers不可用时使用）
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
        """
        # 简单的基于字符的嵌入
        import hashlib
        
        # 使用文本的哈希值生成伪随机向量
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # 将哈希字节转换为浮点数向量
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            if len(embedding) >= self.dimension:
                break
            
            # 将4个字节转换为浮点数
            bytes_chunk = hash_bytes[i:i+4]
            if len(bytes_chunk) == 4:
                # 将字节转换为0-1之间的浮点数
                value = int.from_bytes(bytes_chunk, byteorder='big') / (2**32 - 1)
                embedding.append(value)
        
        # 如果向量长度不足，用零填充
        while len(embedding) < self.dimension:
            embedding.append(0.0)
        
        # 如果向量长度超过，截断
        return embedding[:self.dimension]
    
    def get_dimension(self) -> int:
        """获取嵌入向量的维度"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
