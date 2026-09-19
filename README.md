# 📦 Backup Tool - 数据备份恢复工具

[![CI](https://github.com/your-username/backup-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/backup-tool/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/your-username/backup-tool)](https://github.com/your-username/backup-tool/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

一个功能完整的企业级数据备份恢复Web应用，支持多用户、实时进度、定时备份等功能。

## ✨ 功能特性

- 👥 **多用户系统** - 用户注册、登录、JWT认证
- 📋 **备份任务管理** - 创建、执行、删除备份任务
- 📊 **实时进度显示** - WebSocket实时推送备份进度
- 📁 **文件管理** - 在线预览、下载、删除备份文件
- ⏰ **定时备份** - Cron表达式配置定时任务
- 📝 **操作日志** - 完整的操作记录追踪
- 🎨 **暗色主题** - 专业UI界面

## 🚀 快速开始

### 方式一：Docker部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-username/backup-tool.git
cd backup-tool

# 启动服务
docker-compose up -d

# 访问应用
open http://localhost:8000
```

### 方式二：本地开发

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 方式三：Windows一键启动

双击 `启动Web服务.bat`

## 📸 截图

| 登录页面 | 仪表盘 |
|---------|--------|
| ![Login](docs/images/login.png) | ![Dashboard](docs/images/dashboard.png) |

| 任务管理 | 文件管理 |
|---------|--------|
| ![Tasks](docs/images/tasks.png) | ![Files](docs/images/files.png) |

## 📁 项目结构

```
backup-tool/
├── backend/              # 后端API
│   ├── main.py          # FastAPI主程序
│   ├── models.py        # 数据模型
│   ├── auth.py          # 用户认证
│   └── backup.py        # 备份核心逻辑
│
├── frontend/             # 前端页面
│   ├── index.html       # 登录页面
│   ├── dashboard.html   # 仪表盘
│   ├── tasks.html       # 备份任务
│   ├── files.html       # 文件管理
│   └── logs.html        # 操作日志
│
├── .github/workflows/   # GitHub Actions
├── Dockerfile           # Docker配置
└── docker-compose.yml   # Docker编排
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + JavaScript |
| 后端 | Python FastAPI |
| 数据库 | SQLite |
| 认证 | JWT + bcrypt |
| 通信 | WebSocket |
| 部署 | Docker + GitHub Actions |

## 📚 API文档

启动服务后访问：http://localhost:8000/docs

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/tasks` | GET/POST | 任务管理 |
| `/api/backup/execute/{id}` | POST | 执行备份 |
| `/api/backups` | GET | 备份列表 |
| `/api/backups/download/{filename}` | GET | 下载备份 |
| `/api/logs` | GET | 操作日志 |

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接 | `sqlite:///./data/backup.db` |
| `SECRET_KEY` | JWT密钥 | 需要修改 |

### 修改JWT密钥

编辑 `backend/auth.py`：

```python
SECRET_KEY = "your-super-secret-key"
```

## 🚢 部署指南

### Vercel + Railway（免费）

1. **前端部署到Vercel**
   - Fork项目
   - 在Vercel导入，选择frontend目录

2. **后端部署到Railway**
   - 创建项目
   - 连接GitHub仓库

### 阿里云/腾讯云

```bash
# 安装Docker
curl -fsSL https://get.docker.com | sh

# 克隆项目
git clone https://github.com/your-username/backup-tool.git
cd backup-tool

# 启动
docker-compose up -d
```

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新。

## 🔒 安全

报告安全漏洞请查看 [SECURITY.md](SECURITY.md)。

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Docker](https://www.docker.com/)

---

**如果觉得有用，请给个 ⭐ Star 支持一下！**
