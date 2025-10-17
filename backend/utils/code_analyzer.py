"""
代码分析器模块
负责分析代码结构，提取函数、类等信息
"""

import logging
import re
from typing import Dict, List, Any, Optional
import ast
import os

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """代码分析器类"""
    
    def __init__(self):
        """初始化代码分析器"""
        self.supported_languages = {
            'python': self._analyze_python,
            'javascript': self._analyze_javascript,
            'typescript': self._analyze_typescript,
            'java': self._analyze_java,
            'cpp': self._analyze_cpp,
            'c': self._analyze_c,
            'go': self._analyze_go,
            'rust': self._analyze_rust
        }
    
    def detect_language(self, code: str) -> str:
        """
        检测代码语言
        
        Args:
            code: 代码内容
            
        Returns:
            str: 检测到的语言
        """
        # 简单的语言检测逻辑
        patterns = {
            'python': [
                r'def\s+\w+',
                r'import\s+\w+',
                r'from\s+\w+\s+import',
                r'class\s+\w+',
                r'if\s+__name__\s*==\s*["\']__main__["\']'
            ],
            'javascript': [
                r'function\s+\w+',
                r'const\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'console\.log'
            ],
            'typescript': [
                r'interface\s+\w+',
                r'type\s+\w+\s*=',
                r'class\s+\w+',
                r'export\s+'
            ],
            'java': [
                r'public\s+class\s+\w+',
                r'private\s+\w+',
                r'public\s+\w+',
                r'import\s+java\.'
            ],
            'cpp': [
                r'#include\s*<',
                r'using\s+namespace',
                r'class\s+\w+',
                r'int\s+main\s*\('
            ],
            'c': [
                r'#include\s*<',
                r'int\s+main\s*\(',
                r'void\s+\w+\s*\('
            ],
            'go': [
                r'package\s+\w+',
                r'func\s+\w+',
                r'type\s+\w+',
                r'import\s*\('
            ],
            'rust': [
                r'fn\s+\w+',
                r'struct\s+\w+',
                r'impl\s+\w+',
                r'use\s+\w+'
            ]
        }
        
        scores = {}
        for lang, lang_patterns in patterns.items():
            score = 0
            for pattern in lang_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    score += 1
            scores[lang] = score
        
        # 返回得分最高的语言
        if scores:
            return max(scores, key=scores.get)
        
        return 'unknown'
    
    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        分析代码结构
        
        Args:
            code: 代码内容
            language: 代码语言
            
        Returns:
            Dict[str, Any]: 代码结构信息
        """
        try:
            if language in self.supported_languages:
                return self.supported_languages[language](code)
            else:
                return self._analyze_generic(code, language)
                
        except Exception as e:
            logger.error(f"分析代码时出错: {e}")
            return self._get_default_structure(code, language)
    
    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """分析Python代码"""
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'description': ast.get_docstring(node) or '无描述'
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'description': ast.get_docstring(node) or '无描述'
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            return {
                'language': 'python',
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'function_count': len(functions),
                'class_count': len(classes),
                'import_count': len(imports)
            }
            
        except Exception as e:
            logger.error(f"分析Python代码时出错: {e}")
            return self._get_default_structure(code, 'python')
    
    def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """分析JavaScript代码"""
        functions = []
        classes = []
        imports = []
        
        # 匹配函数定义
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(function_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'JavaScript函数'
            })
        
        # 匹配箭头函数
        arrow_pattern = r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        for match in re.finditer(arrow_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': '箭头函数'
            })
        
        # 匹配类定义
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, code):
            classes.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'JavaScript类'
            })
        
        # 匹配导入语句
        import_pattern = r'import\s+.*?from\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_pattern, code):
            imports.append(match.group(1))
        
        return {
            'language': 'javascript',
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'function_count': len(functions),
            'class_count': len(classes),
            'import_count': len(imports)
        }
    
    def _analyze_typescript(self, code: str) -> Dict[str, Any]:
        """分析TypeScript代码"""
        # TypeScript分析类似于JavaScript，但需要处理类型注解
        functions = []
        classes = []
        interfaces = []
        imports = []
        
        # 匹配函数定义（包括类型注解）
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*:\s*\w+'
        for match in re.finditer(function_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'TypeScript函数'
            })
        
        # 匹配接口定义
        interface_pattern = r'interface\s+(\w+)'
        for match in re.finditer(interface_pattern, code):
            interfaces.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'TypeScript接口'
            })
        
        # 匹配类定义
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, code):
            classes.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'TypeScript类'
            })
        
        return {
            'language': 'typescript',
            'functions': functions,
            'classes': classes,
            'interfaces': interfaces,
            'imports': imports,
            'function_count': len(functions),
            'class_count': len(classes),
            'interface_count': len(interfaces),
            'import_count': len(imports)
        }
    
    def _analyze_java(self, code: str) -> Dict[str, Any]:
        """分析Java代码"""
        functions = []
        classes = []
        imports = []
        
        # 匹配方法定义
        method_pattern = r'(public|private|protected)?\s*\w+\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(method_pattern, code):
            functions.append({
                'name': match.group(2),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'Java方法'
            })
        
        # 匹配类定义
        class_pattern = r'(public|private)?\s*class\s+(\w+)'
        for match in re.finditer(class_pattern, code):
            classes.append({
                'name': match.group(2),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'Java类'
            })
        
        # 匹配导入语句
        import_pattern = r'import\s+([^;]+);'
        for match in re.finditer(import_pattern, code):
            imports.append(match.group(1))
        
        return {
            'language': 'java',
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'function_count': len(functions),
            'class_count': len(classes),
            'import_count': len(imports)
        }
    
    def _analyze_cpp(self, code: str) -> Dict[str, Any]:
        """分析C++代码"""
        functions = []
        classes = []
        includes = []
        
        # 匹配函数定义
        function_pattern = r'\w+\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(function_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'C++函数'
            })
        
        # 匹配类定义
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, code):
            classes.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'C++类'
            })
        
        # 匹配包含语句
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, code):
            includes.append(match.group(1))
        
        return {
            'language': 'cpp',
            'functions': functions,
            'classes': classes,
            'includes': includes,
            'function_count': len(functions),
            'class_count': len(classes),
            'include_count': len(includes)
        }
    
    def _analyze_c(self, code: str) -> Dict[str, Any]:
        """分析C代码"""
        functions = []
        includes = []
        
        # 匹配函数定义
        function_pattern = r'\w+\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(function_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'C函数'
            })
        
        # 匹配包含语句
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        for match in re.finditer(include_pattern, code):
            includes.append(match.group(1))
        
        return {
            'language': 'c',
            'functions': functions,
            'includes': includes,
            'function_count': len(functions),
            'include_count': len(includes)
        }
    
    def _analyze_go(self, code: str) -> Dict[str, Any]:
        """分析Go代码"""
        functions = []
        types = []
        imports = []
        
        # 匹配函数定义
        function_pattern = r'func\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(function_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'Go函数'
            })
        
        # 匹配类型定义
        type_pattern = r'type\s+(\w+)'
        for match in re.finditer(type_pattern, code):
            types.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'Go类型'
            })
        
        # 匹配导入语句
        import_pattern = r'import\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_pattern, code):
            imports.append(match.group(1))
        
        return {
            'language': 'go',
            'functions': functions,
            'types': types,
            'imports': imports,
            'function_count': len(functions),
            'type_count': len(types),
            'import_count': len(imports)
        }
    
    def _analyze_rust(self, code: str) -> Dict[str, Any]:
        """分析Rust代码"""
        functions = []
        structs = []
        imports = []
        
        # 匹配函数定义
        function_pattern = r'fn\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(function_pattern, code):
            functions.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'Rust函数'
            })
        
        # 匹配结构体定义
        struct_pattern = r'struct\s+(\w+)'
        for match in re.finditer(struct_pattern, code):
            structs.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1,
                'description': 'Rust结构体'
            })
        
        # 匹配导入语句
        import_pattern = r'use\s+([^;]+);'
        for match in re.finditer(import_pattern, code):
            imports.append(match.group(1))
        
        return {
            'language': 'rust',
            'functions': functions,
            'structs': structs,
            'imports': imports,
            'function_count': len(functions),
            'struct_count': len(structs),
            'import_count': len(imports)
        }
    
    def _analyze_generic(self, code: str, language: str) -> Dict[str, Any]:
        """通用代码分析"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        return {
            'language': language,
            'total_lines': len(lines),
            'non_empty_lines': len(non_empty_lines),
            'functions': [],
            'classes': [],
            'imports': [],
            'function_count': 0,
            'class_count': 0,
            'import_count': 0
        }
    
    def _get_default_structure(self, code: str, language: str) -> Dict[str, Any]:
        """获取默认的代码结构"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        return {
            'language': language,
            'total_lines': len(lines),
            'non_empty_lines': len(non_empty_lines),
            'functions': [],
            'classes': [],
            'imports': [],
            'function_count': 0,
            'class_count': 0,
            'import_count': 0,
            'error': '代码分析失败'
        }
    
    def analyze_api_structure(self, code: str, language: str) -> Dict[str, Any]:
        """分析API结构"""
        structure = self.analyze_code(code, language)
        
        # 添加API特定的分析
        api_info = {
            'endpoints': [],
            'methods': [],
            'parameters': []
        }
        
        # 这里可以添加更复杂的API分析逻辑
        # 例如分析REST API端点、GraphQL查询等
        
        structure['api_info'] = api_info
        return structure
    
    def analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """分析项目结构"""
        try:
            structure = {
                'path': project_path,
                'files': [],
                'directories': [],
                'total_files': 0,
                'total_directories': 0
            }
            
            for root, dirs, files in os.walk(project_path):
                # 跳过隐藏目录和常见的不需要分析的目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'build', 'dist']]
                
                for file in files:
                    if not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_path)
                        
                        structure['files'].append({
                            'name': file,
                            'path': relative_path,
                            'extension': os.path.splitext(file)[1]
                        })
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(dir_path, project_path)
                    
                    structure['directories'].append({
                        'name': dir_name,
                        'path': relative_path
                    })
            
            structure['total_files'] = len(structure['files'])
            structure['total_directories'] = len(structure['directories'])
            
            return structure
            
        except Exception as e:
            logger.error(f"分析项目结构时出错: {e}")
            return {
                'path': project_path,
                'files': [],
                'directories': [],
                'total_files': 0,
                'total_directories': 0,
                'error': str(e)
            }
