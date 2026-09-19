#!/bin/bash

# 一键发布脚本 (Linux/Mac)

set -e

echo "========================================"
echo "   一键发布 Release 工具"
echo "========================================"
echo

# 检查Git
if ! command -v git &> /dev/null; then
    echo "错误: 未找到Git"
    exit 1
fi

# 检查是否在Git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "错误: 当前目录不是Git仓库"
    exit 1
fi

# 读取当前版本
CURRENT_VERSION=$(cat version.txt)
echo "当前版本: v$CURRENT_VERSION"
echo

# 输入新版本号
read -p "请输入新版本号 (直接回车使用当前版本): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    NEW_VERSION=$CURRENT_VERSION
fi

echo
echo "即将发布版本: v$NEW_VERSION"
echo

# 确认发布
read -p "确认发布? (y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "已取消发布"
    exit 0
fi

# 更新版本文件
echo "$NEW_VERSION" > version.txt

echo
echo "[1/5] 更新版本号到 v$NEW_VERSION..."
echo "[2/5] 添加所有文件到暂存区..."
git add .

echo "[3/5] 提交更改..."
git commit -m "Release v$NEW_VERSION"

echo "[4/5] 创建版本标签..."
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

echo "[5/5] 推送到远程仓库..."
git push origin main
git push origin "v$NEW_VERSION"

echo
echo "========================================"
echo "   发布成功!"
echo "========================================"
echo
echo "版本 v$NEW_VERSION 已发布"
echo "GitHub Actions 将自动构建 Release"
echo
echo "请稍等片刻，然后访问查看:"
echo "https://github.com/your-username/backup-tool/releases"
