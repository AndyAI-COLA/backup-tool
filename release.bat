@echo off
chcp 65001 >nul
title 一键发布 Release

echo ========================================
echo    一键发布 Release 工具
echo ========================================
echo.

REM 检查Git
git --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Git，请先安装Git
    pause
    exit /b 1
)

REM 检查是否在Git仓库中
git status >nul 2>&1
if errorlevel 1 (
    echo 错误: 当前目录不是Git仓库
    echo 请先运行: git init
    pause
    exit /b 1
)

REM 输入版本号
set /p VERSION=请输入版本号 (例如: 1.0.0):

if "%VERSION%"=="" (
    echo 错误: 版本号不能为空
    pause
    exit /b 1
)

echo.
echo 即将发布版本: v%VERSION%
echo.

REM 确认发布
set /p CONFIRM=确认发布? (Y/N):
if /i not "%CONFIRM%"=="Y" (
    echo 已取消发布
    pause
    exit /b 0
)

echo.
echo [1/4] 添加所有文件到暂存区...
git add .

echo [2/4] 提交更改...
git commit -m "Release v%VERSION%"

echo [3/4] 创建版本标签...
git tag -a "v%VERSION%" -m "Release v%VERSION%"

echo [4/4] 推送到远程仓库...
git push origin main
git push origin "v%VERSION%"

echo.
echo ========================================
echo    发布成功!
echo ========================================
echo.
echo 版本 v%VERSION% 已发布
echo GitHub Actions 将自动构建 Release
echo.
echo 查看: https://github.com/your-username/backup-tool/releases
echo.

pause
