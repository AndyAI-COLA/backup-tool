@echo off
chcp 65001 >nul
title 数据备份恢复工具 v2.0

echo ========================================
echo    数据备份恢复工具 v2.0
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 安装依赖
echo 正在检查依赖...
pip install pyyaml -q 2>nul

REM 启动图形界面
echo 正在启动图形界面...
python backup_gui.py

pause
