#!/usr/bin/env python3
"""
测试对话历史API的示例脚本
"""

import asyncio
import aiohttp
import json

async def test_conversation_history_api():
    """测试对话历史API"""
    
    base_url = "http://localhost:8000"
    
    # 模拟一个对话历史
    conversation_history = [
        {"role": "system", "content": "你是一个专业的代码助手，擅长分析和解释代码。"},
        {"role": "user", "content": "什么是Python的装饰器？"},
        {"role": "assistant", "content": "Python装饰器是一种设计模式，它允许在不修改原函数代码的情况下，为函数添加新功能。装饰器本质上是一个接受函数作为参数并返回一个新函数的高阶函数。"},
        {"role": "user", "content": "能给我一个具体的例子吗？"},
    ]
    
    print("=== 测试对话历史API ===\n")
    
    print("对话历史:")
    for msg in conversation_history:
        print(f"{msg['role']}: {msg['content']}")
    
    print("\n--- 发送API请求 ---")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 发送对话历史请求
            payload = {
                "conversationHistory": conversation_history
            }
            
            async with session.post(
                f"{base_url}/api/ask-with-history",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print(f"API响应状态: {response.status}")
                    print(f"助手回答: {result['answer']}")
                    print(f"时间戳: {result['timestamp']}")
                    if result.get('sources'):
                        print(f"来源: {result['sources']}")
                else:
                    error_text = await response.text()
                    print(f"API请求失败: {response.status}")
                    print(f"错误信息: {error_text}")
                    
    except Exception as e:
        print(f"请求时出错: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_conversation_history_api())
