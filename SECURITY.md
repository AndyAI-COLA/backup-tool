# 安全策略

## 报告漏洞

如果你发现安全漏洞，请**不要**公开披露。请通过以下方式报告：

- 发送邮件至：security@your-domain.com
- 或通过 [GitHub Security Advisories](https://github.com/your-username/backup-tool/security/advisories) 报告

我们会在24小时内回复，并在确认漏洞后尽快修复。

## 安全更新

安全更新将通过以下方式发布：

- GitHub Releases
- 安全公告

## 最佳实践

### 部署安全

1. **使用HTTPS**
   - 生产环境必须使用HTTPS
   - 推荐使用Let's Encrypt免费证书

2. **修改默认密钥**
   - 修改 `backend/auth.py` 中的 `SECRET_KEY`
   - 使用强随机密码

3. **数据库安全**
   - 定期备份数据库
   - 限制数据库文件访问权限

4. **Docker安全**
   - 不以root用户运行
   - 使用最小基础镜像
   - 定期更新依赖

### 配置安全

```python
# 生产环境配置示例
SECRET_KEY = "your-super-secret-key-change-this"
```

### 网络安全

- 限制访问IP（如需要）
- 配置防火墙规则
- 使用反向代理（Nginx/Caddy）

## 依赖安全

我们使用以下工具检查依赖安全：

- `pip-audit` - 检查Python依赖漏洞
- `safety` - 安全依赖检查

定期运行：
```bash
pip install pip-audit
pip-audit
```

## 版本支持

| 版本 | 支持状态 |
|------|----------|
| 最新版本 | ✅ 完全支持 |
| 前一个版本 | ✅ 安全更新 |
| 更早版本 | ❌ 不支持 |

## 安全配置清单

- [ ] 修改默认SECRET_KEY
- [ ] 启用HTTPS
- [ ] 配置防火墙
- [ ] 定期备份数据
- [ ] 更新依赖版本
- [ ] 限制API访问
- [ ] 监控日志
