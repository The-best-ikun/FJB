const vscode = require('vscode');
const { QAPanel } = require('./qaPanel');
const { DocGenerator } = require('./docGenerator');
const { ApiClient } = require('./apiClient');

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
   

    // 注册"智能问答"命令
    const askQuestionCommand = vscode.commands.registerCommand(
        'codebase-qa-doc-generator.askQuestion',
        async () => {
            qaPanel.show(); // 显示问答视图
            console.log('问答面板已显示'); // 查看输出面板
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
    context.subscriptions.push(askQuestionCommand, generateDocCommand);

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
