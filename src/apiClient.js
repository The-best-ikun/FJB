const axios = require('axios');

/**
 * API客户端类
 * 负责与Python后端服务进行HTTP通信
 */
class ApiClient {
    constructor() {
        // 后端服务的基础URL，默认使用本地开发服务器
        this.baseURL = 'http://localhost:8000';
        
        // 创建axios实例，配置基础设置
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 30000, // 30秒超时
            headers: {
                'Content-Type': 'application/json',
            }
        });

        // 添加请求拦截器，用于日志记录
        this.client.interceptors.request.use(
            (config) => {
                console.log(`发送请求到: ${config.baseURL}${config.url}`);
                return config;
            },
            (error) => {
                console.error('请求错误:', error);
                return Promise.reject(error);
            }
        );

        // 添加响应拦截器，用于错误处理
        this.client.interceptors.response.use(
            (response) => {
                console.log(`收到响应: ${response.status}`);
                return response;
            },
            (error) => {
                console.error('响应错误:', error.message);
                if (error.code === 'ECONNREFUSED') {
                    throw new Error('无法连接到后端服务，请确保后端服务正在运行');
                }
                return Promise.reject(error);
            }
        );
    }

    /**
     * 发送问答请求到后端
     * @param {string} question 用户问题
     * @param {string} context 可选的上下文信息（如当前文件路径）
     */
    async askQuestion(question, context) {
        try {
            const response = await this.client.post('/api/ask', {
                question,
                context
            });
            
            return response.data.answer;
        } catch (error) {
            console.error('问答请求失败:', error);
            throw new Error('问答服务暂时不可用，请稍后重试');
        }
    }

    /**
     * 发送文档生成请求到后端
     * @param {string} code 要生成文档的代码
     * @param {string} language 代码语言（可选）
     */
    async generateDocument(code, language) {
        try {
            const response = await this.client.post('/api/generate-doc', {
                code,
                language
            });
            
            return response.data.documentation;
        } catch (error) {
            console.error('文档生成请求失败:', error);
            throw new Error('文档生成服务暂时不可用，请稍后重试');
        }
    }

    /**
     * 检查后端服务是否可用
     */
    async healthCheck() {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    /**
     * 更新后端服务URL
     * @param {string} newURL 新的后端服务URL
     */
    updateBaseURL(newURL) {
        this.baseURL = newURL;
        this.client.defaults.baseURL = newURL;
        console.log(`后端服务URL已更新为: ${newURL}`);
    }
}

module.exports = { ApiClient };
