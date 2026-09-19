@echo off
chcp 65001 >nul
title 数据备份恢复工具 v3.0 - Web版

echo ========================================
echo    数据备份恢复工具 v3.0
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 正在启动Web服务...
echo 请稍候，浏览器将自动打开...
echo.

REM 启动FastAPI服务
cd backend
start "" http://localhost:8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
