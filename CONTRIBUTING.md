# 贡献指南

感谢你对本项目的关注！以下是参与贡献的指南。

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/your-username/backup-tool/issues) 页面搜索是否已有相同问题
2. 如果没有，创建一个新的 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤
   - 期望行为和实际行为
   - 环境信息（操作系统、Python版本等）

### 提交代码

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

### 代码规范

- 遵循 PEP 8 Python 编码规范
- 为新功能添加文档字符串
- 保持代码简洁明了

## 开发环境

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 启动开发服务器

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 开发

```bash
docker-compose up -d
```

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构（既不是新增功能，也不是修改bug的代码变动）
- `test`: 增加测试
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat: 添加备份文件预览功能
fix: 修复登录超时问题
docs: 更新API文档
```

## 行为准则

- 尊重每一位贡献者
- 接受建设性的批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

## 问题反馈

如有任何问题，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：your-email@example.com

感谢你的贡献！
