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

REM 读取当前版本
set /p CURRENT_VERSION=<version.txt
echo 当前版本: v%CURRENT_VERSION%
echo.

REM 输入新版本号
set /p NEW_VERSION=请输入新版本号 (直接回车使用当前版本):

if "%NEW_VERSION%"=="" (
    set NEW_VERSION=%CURRENT_VERSION%
)

echo.
echo 即将发布版本: v%NEW_VERSION%
echo.

REM 确认发布
set /p CONFIRM=确认发布? (Y/N):
if /i not "%CONFIRM%"=="Y" (
    echo 已取消发布
    pause
    exit /b 0
)

REM 更新版本文件
echo %NEW_VERSION%> version.txt

echo.
echo [1/5] 更新版本号到 %NEW_VERSION%...
echo [2/5] 添加所有文件到暂存区...
git add .

echo [3/5] 提交更改...
git commit -m "Release v%NEW_VERSION%"

echo [4/5] 创建版本标签...
git tag -a "v%NEW_VERSION%" -m "Release v%NEW_VERSION%"

echo [5/5] 推送到远程仓库...
git push origin main
git push origin "v%NEW_VERSION%"

echo.
echo ========================================
echo    发布成功!
echo ========================================
echo.
echo 版本 v%NEW_VERSION% 已发布
echo GitHub Actions 将自动构建 Release
echo.
echo 请稍等片刻，然后访问查看:
echo https://github.com/your-username/backup-tool/releases
echo.

pause
