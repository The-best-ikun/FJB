"""
文档生成服务模块
负责分析代码并生成相应的文档
"""

import logging
from typing import Optional, Dict, Any
from services.rag_engine import RAGEngine
from utils.code_analyzer import CodeAnalyzer
from utils.doc_formatter import DocFormatter

logger = logging.getLogger(__name__)

class DocService:
    """文档生成服务类"""
    
    def __init__(self, rag_engine: RAGEngine):
        """
        初始化文档生成服务
        
        Args:
            rag_engine: RAG引擎实例
        """
        # RAG引擎
        self.rag_engine = rag_engine
        # 代码分析器
        self.code_analyzer = CodeAnalyzer()
        # 文档格式化器
        self.doc_formatter = DocFormatter()
        logger.info("文档生成服务初始化完成")


    # 生成文件
    async def generate_documentation(self, code: str, language: Optional[str] = None) -> str:
        """
        生成代码文档
        
        Args:
            code: 要生成文档的代码
            language: 代码语言（可选，会自动检测）
            
        Returns:
            str: 生成的文档内容
        """
        try:
            logger.info(f"开始生成文档，代码长度: {len(code)}")
            
            # 如果没有指定语言，自动检测
            if not language:
                # 判断代码类别
                language = self.code_analyzer.detect_language(code)
                logger.info(f"检测到代码语言: {language}")
            
            # 分析代码结构
            code_structure = self.code_analyzer.analyze_code(code, language)
            logger.info(f"代码结构分析完成: {code_structure}")
            
            # 使用RAG引擎生成文档内容
            doc_content = await self._generate_doc_content(code, code_structure, language)
            
            # 格式化文档
            formatted_doc = self.doc_formatter.format_documentation(
                doc_content, code_structure, language
            )
            
            logger.info("文档生成完成")
            return formatted_doc
            
        except Exception as e:
            logger.error(f"生成文档时出错: {e}")
            # 返回处理失败的默认文档
            return self._generate_fallback_documentation(code, language or "unknown")
    # 生成文件中的文档内容
    async def _generate_doc_content(self, code: str, structure: Dict[str, Any], language: str) -> str:
        """
        使用RAG引擎生成文档内容
        
        Args:
            code: 代码内容
            structure: 代码结构信息
            language: 代码语言
            
        Returns:
            str: 文档内容
        """
        try:
            # 构建文档生成查询
            query = self._build_doc_query(code, structure, language)
            
            # 使用RAG引擎生成文档
            doc_content, _ = await self.rag_engine.query(query)
            
            # 如果RAG引擎没有返回内容，使用模板生成
            if not doc_content or doc_content.strip() == "":
                doc_content = self._generate_template_documentation(structure, language)
            
            return doc_content
            
        except Exception as e:
            logger.error(f"使用RAG生成文档内容时出错: {e}")
            return self._generate_template_documentation(structure, language)
    
    def _build_doc_query(self, code: str, structure: Dict[str, Any], language: str) -> str:
        """
        构建文档生成查询
        
        Args:
            code: 代码内容
            structure: 代码结构信息
            language: 代码语言
            
        Returns:
            str: 构建的查询
        """
        query_parts = [
            f"请为以下{language}代码生成详细的文档：",
            "",
            "代码内容：",
            code[:2000],  # 限制代码长度，避免查询过长
            "",
            "代码结构信息：",
            f"- 函数数量: {structure.get('function_count', 0)}",
            f"- 类数量: {structure.get('class_count', 0)}",
            f"- 导入模块: {', '.join(structure.get('imports', [])[:10])}",
            "",
            "请生成包含以下内容的文档：",
            "1. 功能描述",
            "2. 参数说明",
            "3. 返回值说明",
            "4. 使用示例",
            "5. 注意事项"
        ]
        
        return "\n".join(query_parts)
    
    def _generate_template_documentation(self, structure: Dict[str, Any], language: str) -> str:
        """
        生成模板文档（当RAG引擎无法生成时使用）
        
        Args:
            structure: 代码结构信息
            language: 代码语言
            
        Returns:
            str: 模板文档内容
        """
        doc_parts = [
            f"# {language.upper()} 代码文档",
            "",
            "## 概述",
            "此代码文件包含以下主要组件：",
            ""
        ]
        
        # 添加函数信息
        functions = structure.get('functions', [])
        if functions:
            doc_parts.append("### 函数列表")
            for func in functions[:5]:  # 限制显示数量
                doc_parts.append(f"- `{func.get('name', 'unknown')}()`: {func.get('description', '功能描述待补充')}")
            doc_parts.append("")
        
        # 添加类信息
        classes = structure.get('classes', [])
        if classes:
            doc_parts.append("### 类列表")
            for cls in classes[:5]:  # 限制显示数量
                doc_parts.append(f"- `{cls.get('name', 'unknown')}`: {cls.get('description', '类描述待补充')}")
            doc_parts.append("")
        
        # 添加使用说明
        doc_parts.extend([
            "## 使用方法",
            "1. 确保已安装所需的依赖包",
            "2. 导入相应的模块",
            "3. 调用相应的函数或实例化类",
            "",
            "## 注意事项",
            "- 请确保传入正确的参数类型",
            "- 注意异常处理",
            "- 建议在使用前阅读相关文档",
            ""
        ])
        
        return "\n".join(doc_parts)
    
    def _generate_fallback_documentation(self, code: str, language: str) -> str:
        """
        生成基础文档（当所有方法都失败时使用）
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            str: 基础文档内容
        """
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        return f"""# {language.upper()} 代码文档

## 基本信息
- **代码行数**: {len(lines)}
- **非空行数**: {len(non_empty_lines)}
- **语言**: {language}

## 代码内容
```{language}
{code}
```

## 说明
此文档由代码库智能问答与文档生成插件自动生成。
由于无法分析代码结构，请手动补充详细的文档说明。

## 建议
1. 为函数和类添加详细的注释
2. 说明参数和返回值的类型和含义
3. 提供使用示例
4. 添加异常处理说明
"""
    
    async def generate_api_documentation(self, code: str, language: str) -> str:
        """
        生成API文档
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            str: API文档内容
        """
        try:
            # 分析API结构
            api_structure = self.code_analyzer.analyze_api_structure(code, language)
            
            # 生成API文档
            api_doc = self.doc_formatter.format_api_documentation(api_structure, language)
            
            return api_doc
            
        except Exception as e:
            logger.error(f"生成API文档时出错: {e}")
            return self._generate_fallback_documentation(code, language)
    
    async def generate_readme(self, project_path: str) -> str:
        """
        生成项目README文档
        
        Args:
            project_path: 项目路径
            
        Returns:
            str: README文档内容
        """
        try:
            # 分析项目结构
            project_structure = self.code_analyzer.analyze_project_structure(project_path)
            
            # 生成README
            readme_content = self.doc_formatter.format_readme(project_structure)
            
            return readme_content
            
        except Exception as e:
            logger.error(f"生成README时出错: {e}")
            return "# 项目文档\n\n此文档由代码库智能问答与文档生成插件自动生成。\n"
