"""
文档格式化模块
负责格式化生成的文档内容
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DocFormatter:
    """文档格式化器类"""
    
    def __init__(self):
        """初始化文档格式化器"""
        pass
    
    def format_documentation(self, content: str, structure: Dict[str, Any], language: str) -> str:
        """
        格式化代码文档
        
        Args:
            content: 原始文档内容
            structure: 代码结构信息
            language: 代码语言
            
        Returns:
            str: 格式化后的文档
        """
        try:
            # 创建文档头部
            header = self._create_header(structure, language)
            
            # 创建目录
            toc = self._create_table_of_contents(structure)
            
            # 格式化主要内容
            formatted_content = self._format_content(content)
            
            # 创建代码结构部分
            structure_section = self._create_structure_section(structure)
            
            # 创建使用示例部分
            examples_section = self._create_examples_section(structure, language)
            
            # 创建注意事项部分
            notes_section = self._create_notes_section(language)
            
            # 组合所有部分
            documentation = "\n\n".join([
                header,
                toc,
                formatted_content,
                structure_section,
                examples_section,
                notes_section,
                self._create_footer()
            ])
            
            return documentation
            
        except Exception as e:
            logger.error(f"格式化文档时出错: {e}")
            return self._create_fallback_documentation(content, structure, language)
    
    def _create_header(self, structure: Dict[str, Any], language: str) -> str:
        """创建文档头部"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        header = f"""# {language.upper()} 代码文档

## 基本信息
- **语言**: {language}
- **函数数量**: {structure.get('function_count', 0)}
- **类数量**: {structure.get('class_count', 0)}
- **导入数量**: {structure.get('import_count', 0)}
- **生成时间**: {timestamp}

---
"""
        return header
    
    def _create_table_of_contents(self, structure: Dict[str, Any]) -> str:
        """创建目录"""
        toc_items = ["## 目录"]
        
        if structure.get('functions'):
            toc_items.append("- [函数列表](#函数列表)")
        
        if structure.get('classes'):
            toc_items.append("- [类列表](#类列表)")
        
        if structure.get('imports'):
            toc_items.append("- [导入模块](#导入模块)")
        
        toc_items.extend([
            "- [使用方法](#使用方法)",
            "- [使用示例](#使用示例)",
            "- [注意事项](#注意事项)"
        ])
        
        return "\n".join(toc_items)
    
    def _format_content(self, content: str) -> str:
        """格式化主要内容"""
        if not content or content.strip() == "":
            return "## 功能描述\n\n暂无详细描述。"
        
        # 确保内容以适当的标题开始
        if not content.startswith('#'):
            content = "## 功能描述\n\n" + content
        
        return content
    
    def _create_structure_section(self, structure: Dict[str, Any]) -> str:
        """创建代码结构部分"""
        sections = []
        
        # 函数列表
        functions = structure.get('functions', [])
        if functions:
            sections.append("## 函数列表")
            for func in functions:
                name = func.get('name', 'unknown')
                description = func.get('description', '无描述')
                line = func.get('line', 0)
                sections.append(f"- **{name}()** (第{line}行): {description}")
            sections.append("")
        
        # 类列表
        classes = structure.get('classes', [])
        if classes:
            sections.append("## 类列表")
            for cls in classes:
                name = cls.get('name', 'unknown')
                description = cls.get('description', '无描述')
                line = cls.get('line', 0)
                sections.append(f"- **{name}** (第{line}行): {description}")
            sections.append("")
        
        # 导入模块
        imports = structure.get('imports', [])
        if imports:
            sections.append("## 导入模块")
            for imp in imports[:10]:  # 限制显示数量
                sections.append(f"- `{imp}`")
            if len(imports) > 10:
                sections.append(f"- ... 还有 {len(imports) - 10} 个模块")
            sections.append("")
        
        return "\n".join(sections)
    
    def _create_examples_section(self, structure: Dict[str, Any], language: str) -> str:
        """创建使用示例部分"""
        examples = ["## 使用示例"]
        
        # 根据语言生成不同的示例
        if language.lower() == 'python':
            examples.extend([
                "```python",
                "# 导入模块",
                "from your_module import YourClass",
                "",
                "# 创建实例",
                "instance = YourClass()",
                "",
                "# 调用方法",
                "result = instance.your_method()",
                "```"
            ])
        elif language.lower() in ['javascript', 'typescript']:
            examples.extend([
                "```javascript",
                "// 导入模块",
                "import { YourClass } from './your-module';",
                "",
                "// 创建实例",
                "const instance = new YourClass();",
                "",
                "// 调用方法",
                "const result = instance.yourMethod();",
                "```"
            ])
        elif language.lower() == 'java':
            examples.extend([
                "```java",
                "// 导入类",
                "import com.example.YourClass;",
                "",
                "// 创建实例",
                "YourClass instance = new YourClass();",
                "",
                "// 调用方法",
                "String result = instance.yourMethod();",
                "```"
            ])
        else:
            examples.extend([
                f"```{language}",
                "// 使用示例",
                "// 请根据具体语言语法调整",
                "```"
            ])
        
        return "\n".join(examples)
    
    def _create_notes_section(self, language: str) -> str:
        """创建注意事项部分"""
        notes = [
            "## 注意事项",
            "",
            "### 通用注意事项",
            "- 请确保传入正确的参数类型",
            "- 注意异常处理和错误检查",
            "- 建议在使用前阅读相关文档",
            "",
            "### 性能考虑",
            "- 注意内存使用情况",
            "- 避免不必要的循环和递归",
            "- 考虑使用缓存优化性能",
            "",
            "### 安全考虑",
            "- 验证输入参数",
            "- 避免SQL注入等安全问题",
            "- 使用适当的权限控制"
        ]
        
        # 添加语言特定的注意事项
        if language.lower() == 'python':
            notes.extend([
                "",
                "### Python特定注意事项",
                "- 注意Python版本兼容性",
                "- 使用虚拟环境管理依赖",
                "- 遵循PEP 8编码规范"
            ])
        elif language.lower() in ['javascript', 'typescript']:
            notes.extend([
                "",
                "### JavaScript/TypeScript特定注意事项",
                "- 注意异步操作的处理",
                "- 使用严格模式",
                "- 注意作用域和闭包"
            ])
        
        return "\n".join(notes)
    
    def _create_footer(self) -> str:
        """创建文档尾部"""
        return f"""
---

## 文档信息
- **生成工具**: 代码库智能问答与文档生成插件
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **版本**: 1.0.0

> 此文档由AI自动生成，如有疑问请参考源代码或联系开发团队。
"""
    
    def _create_fallback_documentation(self, content: str, structure: Dict[str, Any], language: str) -> str:
        """创建后备文档"""
        return f"""# {language.upper()} 代码文档

## 概述
此文档由代码库智能问答与文档生成插件自动生成。

## 基本信息
- **语言**: {language}
- **函数数量**: {structure.get('function_count', 0)}
- **类数量**: {structure.get('class_count', 0)}

## 原始内容
{content}

## 说明
由于格式化过程中出现错误，此文档可能不完整。请参考源代码获取更多信息。

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def format_api_documentation(self, api_structure: Dict[str, Any], language: str) -> str:
        """格式化API文档"""
        try:
            header = f"""# API 文档

## 基本信息
- **语言**: {language}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
"""
            
            # 这里可以添加更复杂的API文档格式化逻辑
            # 例如分析REST端点、GraphQL查询等
            
            content = "## API 端点\n\n暂无API端点信息。"
            
            footer = self._create_footer()
            
            return "\n\n".join([header, content, footer])
            
        except Exception as e:
            logger.error(f"格式化API文档时出错: {e}")
            return f"# API 文档\n\n格式化API文档时出现错误: {e}"
    
    def format_readme(self, project_structure: Dict[str, Any]) -> str:
        """格式化README文档"""
        try:
            header = f"""# 项目文档

## 项目概述
此项目包含以下文件和目录结构。

## 基本信息
- **项目路径**: {project_structure.get('path', 'unknown')}
- **文件总数**: {project_structure.get('total_files', 0)}
- **目录总数**: {project_structure.get('total_directories', 0)}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
"""
            
            # 文件结构
            files_section = "## 文件结构\n\n"
            files = project_structure.get('files', [])
            if files:
                # 按扩展名分组
                file_groups = {}
                for file_info in files:
                    ext = file_info.get('extension', 'no_extension')
                    if ext not in file_groups:
                        file_groups[ext] = []
                    file_groups[ext].append(file_info)
                
                for ext, file_list in file_groups.items():
                    files_section += f"### {ext} 文件\n\n"
                    for file_info in file_list[:10]:  # 限制显示数量
                        files_section += f"- `{file_info.get('path', 'unknown')}`\n"
                    if len(file_list) > 10:
                        files_section += f"- ... 还有 {len(file_list) - 10} 个文件\n"
                    files_section += "\n"
            else:
                files_section += "暂无文件信息。\n\n"
            
            # 目录结构
            directories_section = "## 目录结构\n\n"
            directories = project_structure.get('directories', [])
            if directories:
                for dir_info in directories[:20]:  # 限制显示数量
                    directories_section += f"- `{dir_info.get('path', 'unknown')}/`\n"
                if len(directories) > 20:
                    directories_section += f"- ... 还有 {len(directories) - 20} 个目录\n"
            else:
                directories_section += "暂无目录信息。\n"
            
            # 使用说明
            usage_section = """
## 使用说明

1. 确保已安装所需的依赖包
2. 按照项目结构组织代码
3. 参考相关文档进行开发

## 注意事项

- 请遵循项目的编码规范
- 注意版本兼容性
- 定期更新依赖包

---
"""
            
            footer = self._create_footer()
            
            return "\n".join([header, files_section, directories_section, usage_section, footer])
            
        except Exception as e:
            logger.error(f"格式化README时出错: {e}")
            return f"# 项目文档\n\n格式化README时出现错误: {e}"
