const vscode = require('vscode');
const { QAPanel } = require('./qaPanel');
const { DocGenerator } = require('./docGenerator');
const { ApiClient } = require('./apiClient');

/**
 * 自动索引工作区代码库
 * @param {ApiClient} apiClient API客户端实例
 * @param {boolean} showProgress 是否显示进度条
 */
async function autoIndexWorkspace(apiClient, showProgress = false) {
    try {
        // 获取工作区信息
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            console.log('没有检测到工作区，跳过自动索引');
            return;
        }

        const workspacePath = workspaceFolders[0].uri.fsPath;
        console.log(`检测到工作区: ${workspacePath}`);

        // 获取工作区中的代码文件
        const codeFiles = await getWorkspaceCodeFiles(workspacePath);
        console.log(`找到 ${codeFiles.length} 个代码文件`);

        // 打印样例文件以供诊断（仅前 5 个）
        try {
            console.log('codeFiles sample:', codeFiles.slice(0, 5));
        } catch (e) {
            console.warn('无法打印 codeFiles 样例', e);
        }

        if (codeFiles.length === 0) {
            console.log('工作区中没有找到代码文件');
            return;
        }

        if (showProgress) {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "正在索引代码库...",
                cancellable: false
            }, async (progress) => {
                progress.report({ message: `发现 ${codeFiles.length} 个文件，开始索引...` });
                
                // 将 codeFiles 序列化为 plain object，避免传递带方法或原型链的对象
                const payloadFiles = codeFiles.map(f => ({
                    path: f.path,
                    relativePath: f.relativePath || f.relative_path,
                    extension: f.extension,
                    size: f.size
                }));

                // 调用后端API进行索引
                const resp = await apiClient.indexCodebase(workspacePath, payloadFiles);
                console.log('indexCodebase response:', resp);
                
                progress.report({ message: "索引完成！" });
            });
            
            vscode.window.showInformationMessage(`代码库索引完成！共索引 ${codeFiles.length} 个文件`);
        } else {
            // 静默索引
            const payloadFiles = codeFiles.map(f => ({
                path: f.path,
                relativePath: f.relativePath || f.relative_path,
                extension: f.extension,
                size: f.size
            }));
            const resp = await apiClient.indexCodebase(workspacePath, payloadFiles);
            console.log(`代码库索引完成！共索引 ${codeFiles.length} 个文件`, resp);
        }

    } catch (error) {
        console.error('自动索引工作区失败:', error);
        if (showProgress) {
            vscode.window.showErrorMessage(`代码库索引失败: ${error.message}`);
        }
    }
}

/**
 * 获取工作区中的代码文件
 * @param {string} workspacePath 工作区路径
 * @returns {Promise<Array>} 代码文件列表
 */
async function getWorkspaceCodeFiles(workspacePath) {
    const fs = require('fs');
    const path = require('path');
    
    const codeExtensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb', '.swift', '.kt'];
    const excludeDirs = ['node_modules', '.git', '.vscode', '__pycache__', '.pytest_cache', 'dist', 'build', 'target'];
    
    const codeFiles = [];
    
    function scanDirectory(dirPath) {
        try {
            const items = fs.readdirSync(dirPath);
            
            for (const item of items) {
                const fullPath = path.join(dirPath, item);
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    // 跳过排除的目录
                    if (!excludeDirs.includes(item)) {
                        scanDirectory(fullPath);
                    }
                } else if (stat.isFile()) {
                    const ext = path.extname(item).toLowerCase();
                    if (codeExtensions.includes(ext)) {
                        codeFiles.push({
                            path: fullPath,
                            relativePath: path.relative(workspacePath, fullPath),
                            extension: ext,
                            size: stat.size
                        });
                    }
                }
            }
        } catch (error) {
            console.warn(`扫描目录失败: ${dirPath}, 错误: ${error.message}`);
        }
    }
    
    scanDirectory(workspacePath);
    return codeFiles;
}

/**
 * VSCode插件激活函数
 * 当插件被激活时调用，设置所有命令和视图
 */
function activate(context) {
    console.log('代码库智能问答与文档生成插件已激活');
    console.log('✅ Extension activated!'); // 查看输出面板

    // 创建API客户端实例，用于与后端服务通信
    const apiClient = new ApiClient();

    // 创建问答面板实例
    const qaPanel = new QAPanel(context.extensionUri, apiClient);

    // 创建文档生成器实例
    const docGenerator = new DocGenerator(apiClient);
    
    // 自动索引工作区代码库
    autoIndexWorkspace(apiClient);

    // 注册"智能问答"命令
    const askQuestionCommand = vscode.commands.registerCommand(
        'codebase-qa-doc-generator.askQuestion',
        async () => {
            qaPanel.show(); // 显示问答视图
            console.log('问答面板已显示'); // 查看输出面板
        }
    );

    // 注册"重新索引代码库"命令
    const reindexCommand = vscode.commands.registerCommand(
        'codebase-qa-doc-generator.reindexCodebase',
        async () => {
            await autoIndexWorkspace(apiClient, true);
        }
    );

    // 注册"生成文档"命令
    const generateDocCommand = vscode.commands.registerCommand(
        'codebase-qa-doc-generator.generateDoc',
        async () => {
            // 获取当前选中的文本或整个文件内容
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('请先打开一个文件');
                return;
            }

            const selection = editor.selection;
            let codeContent = '';

            if (selection.isEmpty) {
                // 如果没有选中文本，使用整个文件内容
                codeContent = editor.document.getText();
            } else {
                // 使用选中的文本
                codeContent = editor.document.getText(selection);
            }

            if (!codeContent.trim()) {
                vscode.window.showWarningMessage('请选择要生成文档的代码');
                return;
            }

            // 显示进度条
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "正在生成文档...",
                cancellable: false
            }, async (progress) => {
                try {
                    // 调用文档生成器
                    const doc = await docGenerator.generateDocument(codeContent);
                    
                    // 创建新文档显示生成的文档
                    const docUri = vscode.Uri.parse(`untitled:${editor.document.fileName}_doc.md`);
                    const docEditor = await vscode.workspace.openTextDocument(docUri);
                    await vscode.window.showTextDocument(docEditor);
                    
                    // 插入生成的文档内容
                    const edit = new vscode.WorkspaceEdit();
                    edit.insert(docUri, new vscode.Position(0, 0), doc);
                    await vscode.workspace.applyEdit(edit);
                    
                    vscode.window.showInformationMessage('文档生成成功！');
                } catch (error) {
                    console.error('文档生成失败:', error);
                    vscode.window.showErrorMessage(`文档生成失败: ${error}`);
                }
            });
        }
    );

    // 将命令添加到订阅列表，确保插件停用时能正确清理
    context.subscriptions.push(askQuestionCommand, generateDocCommand, reindexCommand);

    // 注册Webview面板提供者
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            'codebase-qa-doc-generator.qaView',
            qaPanel
        )
    );
}

/**
 * VSCode插件停用函数
 * 当插件被停用时调用，进行清理工作
 */
function deactivate() {
    console.log('代码库智能问答与文档生成插件已停用');
}

module.exports = {
    activate,
    deactivate
};
