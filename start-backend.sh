#!/bin/bash

echo "正在启动代码库智能问答与文档生成后端服务..."
echo

cd backend

echo "检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: Python3未安装或未添加到PATH"
    exit 1
fi

echo "检查Python版本兼容性..."
python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if [ $? -ne 0 ]; then
    echo "警告: 当前Python版本可能不是3.11，建议使用Python 3.11以获得最佳兼容性"
    echo "继续运行..."
fi

echo
echo "检查依赖包..."
pip3 list | grep -q fastapi
if [ $? -ne 0 ]; then
    echo "正在安装依赖包..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 依赖包安装失败"
        exit 1
    fi
fi

echo
echo "启动服务器..."
python3 start.py
