const vscode = require('vscode');
const ApiClient = require('./apiClient');

/**
 * 问答面板类
 * 负责创建和管理VSCode中的问答界面，该界面将在右侧编辑器组中独立显示。
 */
class QAPanel {
    /**
     * @param {vscode.ExtensionUri} extensionUri 插件的根目录URI
     * @param {ApiClient} apiClient API客户端实例
     */
    constructor(extensionUri, apiClient) {
        this._extensionUri = extensionUri;
        this._apiClient = apiClient;
        this._panel = undefined; // 使用 _panel 来遵循私有属性约定
        this._conversationHistory = []; // 存储对话历史
    }

    /**
     * 显示或创建问答面板。
     * 如果面板已存在，则激活它。否则，创建一个新的面板。
     */
    show() {
        // 如果面板已经存在，就激活它，而不是创建一个新的
        if (this._panel) {
            this._panel.reveal(vscode.ViewColumn.Two);
            return;
        }

        // 创建一个新的面板
        this._panel = vscode.window.createWebviewPanel(
            'qaChat', // 内部ID，用于在 `package.json` 中引用
            'QA Chat', // 面板向用户显示的标题
            {
                // 强制在第二个编辑器列（通常是右侧）中显示面板
                viewColumn: vscode.ViewColumn.Two,
                // 保留面板的上下文，即使它失去了焦点
                preserveFocus: true 
            },
            {
                // 启用脚本
                enableScripts: true,
                // 限制Webview只能访问特定目录的资源
                localResourceRoots: [this._extensionUri]
            }
        );

        // 设置面板的初始HTML内容
        this._panel.webview.html = this._getWebviewContent(this._panel.webview);

        // 恢复对话历史
        const savedHistory = this._panel.webview.state?.conversationHistory || [];
        this._conversationHistory = savedHistory;

        // 消息处理：接收来自Webview的消息
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'askQuestion':
                        this._handleAskQuestion(message.text);
                        return;
                    case 'clearHistory':
                        this._handleClearHistory();
                        return;
                }
            },
            undefined,
            // 这里的 `this` 上下文很重要
            []
        );

        // 面板被用户关闭时的事件处理
        this._panel.onDidDispose(
            () => {
                // 保存对话历史到状态中
                if (this._panel && this._conversationHistory.length > 0) {
                    this._panel.webview.state = { 
                        ...this._panel.webview.state,
                        conversationHistory: this._conversationHistory 
                    };
                }
                this._panel = undefined;
            },
            null,
            []
        );
    }

    /**
     * 处理用户提问
     * @param {string} question 用户的问题
     */
    async _handleAskQuestion(question) {
        if (!this._panel) {
            return; // 面板已关闭，不做处理
        }

        // 1. 显示加载状态（用户消息已在前端添加）
        this._panel.webview.postMessage({ command: 'showLoading' });

        try {
            // 2. 添加用户消息到对话历史
            this._conversationHistory.push({ role: 'user', content: question });
            
            // 3. 调用API获取回答，传递完整的对话历史
            const answer = await this._apiClient.askQuestionWithHistory(this._conversationHistory);
            
            // 4. 添加助手回答到对话历史
            this._conversationHistory.push({ role: 'assistant', content: answer });
            
            // 5. 显示AI的回答
            this._panel.webview.postMessage({ command: 'addMessage', type: 'bot', text: answer });
        } catch (error) {
            vscode.window.showErrorMessage(`API请求失败: ${error.message}`);
            // 6. 显示错误信息
            this._panel.webview.postMessage({ command: 'addError', text: '抱歉，服务暂时无法响应，请稍后再试。' });
        }
    }

    /**
     * 处理清空历史记录的请求
     */
    _handleClearHistory() {
        if (!this._panel) {
            return;
        }
        // 清空对话历史
        this._conversationHistory = [];
        // 更新面板的 state 为空数组，这会触发序列化
        this._panel.webview.state = { history: [] };
        // 通知前端清空显示
        this._panel.webview.postMessage({ command: 'clearHistory' });
    }


    /**
     * 获取Webview的HTML内容
     * @param {vscode.Webview} webview
     * @returns {string}
     */
    _getWebviewContent(webview) {
        // 使用 nonce 来提高安全性
        const nonce = getNonce();

        // 从 state 中恢复历史记录，如果没有则为空数组
        const historyState = webview.state?.history || [];
        const initialHistoryJson = JSON.stringify(historyState);

        return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://cdnjs.cloudflare.com; script-src 'nonce-${nonce}' https://cdnjs.cloudflare.com;">
    <title>QA Chat</title>
    <!-- 引入marked.js用于Markdown渲染 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
    <!-- 引入highlight.js用于代码高亮 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        body, html { margin: 0; padding: 0; font-family: var(--vscode-font-family); color: var(--vscode-foreground); background-color: var(--vscode-editor-background); height: 100vh; display: flex; flex-direction: column; }
        .chat-container { flex-grow: 1; overflow-y: auto; padding: 10px; }
        .message { margin-bottom: 15px; display: flex; flex-direction: column; }
        .message.user { align-items: flex-end; }
        .message.bot { align-items: flex-start; }
        .message-content { max-width: 80%; padding: 10px 15px; border-radius: 10px; word-wrap: break-word; }
        .message.user .message-content { background-color: var(--vscode-button-background); color: var(--vscode-button-foreground); }
        .message.bot .message-content { background-color: var(--vscode-input-background); border: 1px solid var(--vscode-input-border); }
        
        /* Markdown样式 */
        .message-content h1, .message-content h2, .message-content h3, .message-content h4, .message-content h5, .message-content h6 {
            margin: 10px 0 5px 0;
            color: var(--vscode-foreground);
        }
        .message-content p { margin: 5px 0; line-height: 1.5; }
        .message-content ul, .message-content ol { margin: 5px 0; padding-left: 20px; }
        .message-content li { margin: 2px 0; }
        .message-content blockquote { 
            margin: 10px 0; 
            padding: 10px; 
            border-left: 3px solid var(--vscode-button-background); 
            background-color: var(--vscode-editor-background); 
        }
        .message-content code { 
            background-color: var(--vscode-editor-background); 
            padding: 2px 4px; 
            border-radius: 3px; 
            font-family: var(--vscode-editor-font-family, 'Consolas', 'Monaco', monospace);
        }
        .message-content pre { 
            background-color: var(--vscode-editor-background); 
            padding: 10px; 
            border-radius: 5px; 
            overflow-x: auto; 
            margin: 10px 0;
        }
        .message-content pre code { 
            background: none; 
            padding: 0; 
        }
        .message-content table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 10px 0; 
        }
        .message-content th, .message-content td { 
            border: 1px solid var(--vscode-input-border); 
            padding: 8px; 
            text-align: left; 
        }
        .message-content th { 
            background-color: var(--vscode-input-background); 
        }
        .loading { font-style: italic; color: var(--vscode-descriptionForeground); }
        .error { color: var(--vscode-errorForeground); }
        .input-container { display: flex; padding: 10px; border-top: 1px solid var(--vscode-panel-border); }
        #questionInput { flex-grow: 1; padding: 8px; border: 1px solid var(--vscode-input-border); background-color: var(--vscode-input-background); color: var(--vscode-input-foreground); border-radius: 4px; }
        #askButton { margin-left: 10px; padding: 8px 15px; border: none; background-color: var(--vscode-button-background); color: var(--vscode-button-foreground); border-radius: 4px; cursor: pointer; }
        #askButton:hover { background-color: var(--vscode-button-hoverBackground); }
        #askButton:disabled { background-color: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); cursor: not-allowed; }
        .toolbar { padding: 5px 10px; border-bottom: 1px solid var(--vscode-panel-border); display: flex; justify-content: flex-end; }
        .toolbar button { background: none; border: none; color: var(--vscode-foreground); cursor: pointer; }
        .toolbar button:hover { background-color: var(--vscode-list-hoverBackground); }
    </style>
</head>
<body>
    <div class="toolbar">
        <button id="clearHistoryBtn" title="清空历史">🗑️ 清空</button>
    </div>
    <div class="chat-container" id="chatContainer"></div>
    <div class="input-container">
        <input type="text" id="questionInput" placeholder="输入你的问题..." />
        <button id="askButton">发送</button>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chatContainer');
        const questionInput = document.getElementById('questionInput');
        const askButton = document.getElementById('askButton');
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');

        let history = ${initialHistoryJson}; // 从后端恢复历史

        // 初始化界面
        function renderHistory() {
            chatContainer.innerHTML = '';
            history.forEach(msg => addMessageToUI(msg.type, msg.text));
        }
        renderHistory();

        function addMessageToUI(type, text) {
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${type}\`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // 如果是bot消息，使用Markdown渲染
            if (type === 'bot') {
                contentDiv.innerHTML = marked.parse(text);
                // 高亮代码块
                contentDiv.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            } else {
                // 用户消息保持纯文本
                contentDiv.textContent = text;
            }
            
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showLoadingUI() {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot loading';
            loadingDiv.id = 'loading-indicator';
            loadingDiv.textContent = 'AI正在思考中...';
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function hideLoadingUI() {
            const loadingIndicator = document.getElementById('loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }

        function showErrorUI(text) {
            hideLoadingUI();
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message bot error';
            errorDiv.textContent = text;
            chatContainer.appendChild(errorDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function ask() {
            const question = questionInput.value.trim();
            if (!question) return;

            // 添加用户消息到历史和UI
            history.push({ type: 'user', text: question });
            addMessageToUI('user', question);
            questionInput.value = '';
            askButton.disabled = true;

            // 通知后端（不重复添加用户消息）
            vscode.postMessage({ command: 'askQuestion', text: question });
        }

        askButton.addEventListener('click', ask);
        questionInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { ask(); } });

        clearHistoryBtn.addEventListener('click', () => {
            vscode.postMessage({ command: 'clearHistory' });
        });

        // 监听来自后端的消息
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'addMessage':
                    // 只添加bot消息，避免重复添加用户消息
                    if (message.type === 'bot') {
                        history.push({ type: message.type, text: message.text });
                        hideLoadingUI();
                        addMessageToUI(message.type, message.text);
                        askButton.disabled = false;
                    }
                    break;
                case 'showLoading':
                    showLoadingUI();
                    break;
                case 'addError':
                    showErrorUI(message.text);
                    askButton.disabled = false;
                    break;
                case 'clearHistory':
                    history = [];
                    renderHistory();
                    break;
            }
        });

        // 在状态变化时（如页面刷新前）保存历史
        window.addEventListener('beforeunload', () => {
            vscode.setState({ history: history });
        });
    </script>
</body>
</html>`;
    }
}

/**
 * 生成一个随机的 nonce 字符串，用于CSP
 */
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

module.exports = { QAPanel };
