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

# 输入版本号
read -p "请输入版本号 (例如: 1.0.0): " VERSION

if [ -z "$VERSION" ]; then
    echo "错误: 版本号不能为空"
    exit 1
fi

echo
echo "即将发布版本: v$VERSION"
echo

# 确认发布
read -p "确认发布? (y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "已取消发布"
    exit 0
fi

echo
echo "[1/4] 添加所有文件到暂存区..."
git add .

echo "[2/4] 提交更改..."
git commit -m "Release v$VERSION"

echo "[3/4] 创建版本标签..."
git tag -a "v$VERSION" -m "Release v$VERSION"

echo "[4/4] 推送到远程仓库..."
git push origin main
git push origin "v$VERSION"

echo
echo "========================================"
echo "   发布成功!"
echo "========================================"
echo
echo "版本 v$VERSION 已发布"
echo "GitHub Actions 将自动构建 Release"
echo
echo "查看: https://github.com/your-username/backup-tool/releases"
