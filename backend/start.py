#!/usr/bin/env python3
"""
后端服务启动脚本
用于启动FastAPI服务器
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(project_root))
    
    # 从环境变量获取配置
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    log_level = os.getenv('LOG_LEVEL', 'info')
    
    print(f"正在启动代码库智能问答与文档生成服务...")
    print(f"服务器地址: http://{host}:{port}")
    print(f"调试模式: {debug}")
    print(f"日志级别: {log_level}")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()
