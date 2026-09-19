# 更新日志

本文档记录了项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2024-01-19

### 新增
- ✨ 多用户系统（注册/登录/JWT认证）
- ✨ 备份任务管理（创建/执行/删除）
- ✨ 实时进度显示（WebSocket）
- ✨ 文件管理（下载/验证/删除）
- ✨ 定时备份配置（Cron表达式）
- ✨ 操作日志记录
- ✨ 系统仪表盘（统计图表）
- ✨ Docker容器化部署
- ✨ GitHub Actions CI/CD
- ✨ 一键发布Release功能

### 技术栈
- 后端：Python FastAPI
- 前端：HTML5 + CSS3 + JavaScript
- 数据库：SQLite
- 认证：JWT + bcrypt
- 部署：Docker + GitHub Actions

## 版本说明

- **主版本号 (Major)**: 不兼容的API变更
- **次版本号 (Minor)**: 向后兼容的功能性新增
- **修订号 (Patch)**: 向后兼容的问题修正
