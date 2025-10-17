#!/usr/bin/env python3
"""
API测试脚本
用于测试后端服务的各个接口
"""

import requests
import json
import time
from typing import Dict, Any

class APITester:
    """API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API测试器
        
        Args:
            base_url: 后端服务的基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'API-Tester/1.0'
        })
    
    def test_health_check(self) -> bool:
        """测试健康检查接口"""
        print("🔍 测试健康检查接口...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过: {data['status']}")
                print(f"   服务状态: {data['services']}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_ask_question(self, question: str = "你好，请介绍一下这个系统") -> bool:
        """测试问答接口"""
        print(f"🔍 测试问答接口: {question}")
        try:
            payload = {
                "question": question,
                "context": "测试环境"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/ask",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 问答接口测试通过")
                print(f"   答案: {data['answer'][:100]}...")
                print(f"   时间戳: {data['timestamp']}")
                return True
            else:
                print(f"❌ 问答接口测试失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 问答接口异常: {e}")
            return False
    
    def test_generate_doc(self, code: str = "def hello_world():\n    print('Hello, World!')") -> bool:
        """测试文档生成接口"""
        print("🔍 测试文档生成接口...")
        try:
            payload = {
                "code": code,
                "language": "python"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate-doc",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 文档生成接口测试通过")
                print(f"   文档长度: {len(data['documentation'])} 字符")
                print(f"   语言: {data['language']}")
                return True
            else:
                print(f"❌ 文档生成接口测试失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 文档生成接口异常: {e}")
            return False
    
    def test_search(self, query: str = "函数定义") -> bool:
        """测试搜索接口"""
        print(f"🔍 测试搜索接口: {query}")
        try:
            response = self.session.get(
                f"{self.base_url}/api/search",
                params={"query": query, "limit": 5},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 搜索接口测试通过")
                print(f"   查询: {data['query']}")
                print(f"   结果数量: {len(data['results'])}")
                return True
            else:
                print(f"❌ 搜索接口测试失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 搜索接口异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 开始运行API测试...")
        print("=" * 50)
        
        results = {}
        
        # 测试健康检查
        results['health'] = self.test_health_check()
        print()
        
        # 测试问答接口
        results['ask'] = self.test_ask_question()
        print()
        
        # 测试文档生成接口
        results['doc'] = self.test_generate_doc()
        print()
        
        # 测试搜索接口
        results['search'] = self.test_search()
        print()
        
        # 输出测试结果
        print("=" * 50)
        print("📊 测试结果汇总:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        passed = sum(results.values())
        total = len(results)
        print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
        
        return results

def main():
    """主函数"""
    print("代码库智能问答与文档生成 API 测试工具")
    print("=" * 50)
    
    # 创建测试器
    tester = APITester()
    
    # 运行所有测试
    results = tester.run_all_tests()
    
    # 根据结果退出
    if all(results.values()):
        print("\n🎉 所有测试通过！")
        exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查后端服务状态")
        exit(1)

if __name__ == "__main__":
    main()
