@echo off
echo 正在启动代码库智能问答与文档生成后端服务...
echo.

cd backend

echo 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: Python未安装或未添加到PATH
    pause
    exit /b 1
)

echo 检查Python版本兼容性...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    echo 警告: 当前Python版本可能不是3.11，建议使用Python 3.11以获得最佳兼容性
    echo 继续运行...
)

echo.
echo 检查依赖包...
pip list | findstr fastapi >nul
if %errorlevel% neq 0 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动服务器...
python start.py

pause
