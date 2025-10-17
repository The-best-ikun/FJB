const vscode = require('vscode');
const { ApiClient } = require('./apiClient');

/**
 * 文档生成器类
 * 负责处理代码文档生成相关的功能
 */
class DocGenerator {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    /**
     * 生成代码文档
     * @param {string} code 要生成文档的代码
     * @param {string} language 代码语言（可选，会自动检测）
     */
    async generateDocument(code, language) {
        try {
            // 如果没有指定语言，尝试从当前编辑器检测
            if (!language) {
                language = this.detectLanguage(code);
            }

            // 调用后端API生成文档
            const documentation = await this.apiClient.generateDocument(code, language);
            
            // 格式化文档，添加标题和元信息
            return this.formatDocumentation(documentation, code, language);
        } catch (error) {
            console.error('文档生成失败:', error);
            throw error;
        }
    }

    /**
     * 检测代码语言
     * @param {string} code 代码内容
     */
    detectLanguage(code) {
        // 简单的语言检测逻辑
        const patterns = {
            'javascript': /function\s+\w+|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=/,
            'typescript': /interface\s+\w+|type\s+\w+\s*=|class\s+\w+/,
            'python': /def\s+\w+|class\s+\w+|import\s+\w+/,
            'java': /public\s+class\s+\w+|private\s+\w+|public\s+\w+/,
            'cpp': /#include\s*<|using\s+namespace|class\s+\w+/,
            'c': /#include\s*<|int\s+main\s*\(/,
            'go': /package\s+\w+|func\s+\w+|type\s+\w+/,
            'rust': /fn\s+\w+|struct\s+\w+|impl\s+\w+/,
        };

        for (const [lang, pattern] of Object.entries(patterns)) {
            if (pattern.test(code)) {
                return lang;
            }
        }

        return 'unknown';
    }

    /**
     * 格式化生成的文档
     * @param {string} documentation 原始文档内容
     * @param {string} code 原始代码
     * @param {string} language 代码语言
     */
    formatDocumentation(documentation, code, language) {
        const timestamp = new Date().toLocaleString('zh-CN');
        const codeLines = code.split('\n').length;
        
        return `# 代码文档

## 基本信息
- **语言**: ${language}
- **代码行数**: ${codeLines}
- **生成时间**: ${timestamp}

## 文档内容

${documentation}

## 原始代码

\`\`\`${language}
${code}
\`\`\`

---
*此文档由代码库智能问答与文档生成插件自动生成*
`;
    }

    /**
     * 批量生成文档
     * @param {vscode.Uri[]} files 文件路径列表
     */
    async generateBatchDocumentation(files) {
        const progressOptions = {
            location: vscode.ProgressLocation.Notification,
            title: "批量生成文档",
            cancellable: true
        };

        await vscode.window.withProgress(progressOptions, async (progress, token) => {
            const total = files.length;
            
            for (let i = 0; i < files.length; i++) {
                if (token.isCancellationRequested) {
                    break;
                }

                const file = files[i];
                progress.report({
                    increment: (100 / total),
                    message: `正在处理: ${file.fsPath}`
                });

                try {
                    // 读取文件内容
                    const document = await vscode.workspace.openTextDocument(file);
                    const code = document.getText();
                    
                    // 生成文档
                    const doc = await this.generateDocument(code, document.languageId);
                    
                    // 创建文档文件
                    const docPath = file.fsPath.replace(/\.[^/.]+$/, '_doc.md');
                    const docUri = vscode.Uri.file(docPath);
                    
                    // 写入文档
                    const encoder = new TextEncoder();
                    const docData = encoder.encode(doc);
                    await vscode.workspace.fs.writeFile(docUri, docData);
                    
                } catch (error) {
                    console.error(`处理文件 ${file.fsPath} 时出错:`, error);
                    vscode.window.showWarningMessage(`处理文件 ${file.fsPath} 时出错: ${error}`);
                }
            }
        });

        vscode.window.showInformationMessage('批量文档生成完成！');
    }

    /**
     * 生成项目概览文档
     * @param {vscode.WorkspaceFolder} workspaceFolder 工作区文件夹
     */
    async generateProjectOverview(workspaceFolder) {
        try {
            // 获取工作区中的所有代码文件
            const pattern = new vscode.RelativePattern(workspaceFolder, '**/*.{js,ts,py,java,cpp,c,go,rs}');
            const files = await vscode.workspace.findFiles(pattern, '**/node_modules/**', 100);

            if (files.length === 0) {
                vscode.window.showWarningMessage('工作区中没有找到代码文件');
                return;
            }

            // 生成项目概览
            const overview = await this.generateProjectOverviewContent(files);
            
            // 创建概览文档
            const overviewPath = vscode.Uri.joinPath(workspaceFolder.uri, 'PROJECT_OVERVIEW.md');
            const encoder = new TextEncoder();
            const overviewData = encoder.encode(overview);
            await vscode.workspace.fs.writeFile(overviewPath, overviewData);
            
            // 打开概览文档
            const document = await vscode.workspace.openTextDocument(overviewPath);
            await vscode.window.showTextDocument(document);
            
            vscode.window.showInformationMessage('项目概览文档生成成功！');
        } catch (error) {
            console.error('生成项目概览失败:', error);
            vscode.window.showErrorMessage(`生成项目概览失败: ${error}`);
        }
    }

    /**
     * 生成项目概览内容
     * @param {vscode.Uri[]} files 文件列表
     */
    async generateProjectOverviewContent(files) {
        const timestamp = new Date().toLocaleString('zh-CN');
        let content = `# 项目概览

## 基本信息
- **生成时间**: ${timestamp}
- **文件总数**: ${files.length}

## 文件结构

`;

        // 按文件类型分组
        const fileGroups = {};
        files.forEach(file => {
            const ext = file.path.split('.').pop() || 'unknown';
            if (!fileGroups[ext]) {
                fileGroups[ext] = [];
            }
            fileGroups[ext].push(file);
        });

        // 生成文件列表
        for (const [ext, fileList] of Object.entries(fileGroups)) {
            content += `### ${ext.toUpperCase()} 文件 (${fileList.length}个)\n\n`;
            fileList.forEach(file => {
                const relativePath = vscode.workspace.asRelativePath(file);
                content += `- \`${relativePath}\`\n`;
            });
            content += '\n';
        }

        content += `---
*此文档由代码库智能问答与文档生成插件自动生成*
`;

        return content;
    }
}

module.exports = { DocGenerator };
