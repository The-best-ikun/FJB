#!/usr/bin/env python3
"""
测试对话历史功能的示例脚本
"""

import asyncio
import os
from services.llm_service import LLMService

async def test_conversation_history():
    """测试对话历史功能"""
    
    # 初始化LLM服务
    llm_service = LLMService()
    await llm_service.initialize()
    
    print("=== 测试对话历史功能 ===\n")
    
    # 模拟一个对话历史
    conversation_history = [
        {"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"},
        {"role": "user", "content": "什么是Python的装饰器？"},
        {"role": "assistant", "content": "Python装饰器是一种设计模式，它允许在不修改原函数代码的情况下，为函数添加新功能。装饰器本质上是一个接受函数作为参数并返回一个新函数的高阶函数。"},
        {"role": "user", "content": "能给我一个具体的例子吗？"},
    ]
    
    print("对话历史:")
    for msg in conversation_history:
        print(f"{msg['role']}: {msg['content']}")
    
    print("\n--- 生成回答 ---")
    
    try:
        # 使用对话历史生成回答
        response = await llm_service.generate_text_with_history(conversation_history)
        print(f"助手: {response}")
        
    except Exception as e:
        print(f"生成回答时出错: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_conversation_history())
