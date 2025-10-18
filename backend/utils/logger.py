"""
日志配置模块
"""

import logging
import sys
from datetime import datetime
import os

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果已经配置了 handler，设置好 propagate 并直接返回，避免重复添加
    if logger.handlers:
        logger.propagate = False
        return logger

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建模块专用的控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 确保 root logger 也有控制台 handler（这样当第三方库或 uvicorn 使用 root logger 时也能看到输出）
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_console = logging.StreamHandler(sys.stdout)
        root_console.setLevel(level)
        root_console.setFormatter(formatter)
        root_logger.addHandler(root_console)
    root_logger.setLevel(level)

    # 创建文件处理器
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 防止日志向上传播到 root 导致重复输出
    logger.propagate = False

    # 兼容 uvicorn / fastapi：确保它们的日志级别不会把 INFO 隐藏
    for ln in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        lg = logging.getLogger(ln)
        try:
            lg.setLevel(level)
            # 如果这些 logger 没有 handler，让它们向上（root）传播以使用 root 的控制台 handler
            if not lg.handlers:
                lg.propagate = True
        except Exception:
            # 容错：某些环境下设置 logger 可能失败，不阻塞主流程
            pass

    return logger
