# TalentMail × Auth-Center 上线检查清单

> 两边可**分开上线**。Mail 不依赖 Center 也能跑（本地密码登录）；Center 仅在启用 SSO 时需要。
> Demo 应用 `demo-admin` / `demo-web` 可保留作流程验证，**不必删除**。

## A. 仅上线 TalentMail

- [ ] DNS：`mail.example.com` → 服务器；邮件域名（MX/SPF/DKIM/DMARC）按现有 mailserver 文档
- [ ] 25 / 443 / 587 / 993 放行；Web 只暴露 80/443
- [ ] `.env`：正式 `BASE_DOMAIN`、`POSTGRES_*`、`SECRET_KEY`、管理员密码
- [ ] `SSO_ENABLED=false`（或先不配 Center）
- [ ] Caddy / 反代：HTTPS 终止 → frontend + backend
- [ ] `docker compose up -d` 后检查 `/api/health` 为 healthy
- [ ] 备份：`talentmail-backup.timer` 启用；按需 `TALENTMAIL_BACKUP_ENCRYPT=1`

## B. 同时上线 Auth-Center（启用 SSO）

在 A 的基础上：

- [ ] Center 域名，例如 `auth.example.com`（HTTPS）
- [ ] `AUTH_CENTER_ENV=production`（不 seed 弱口令演示用户）
- [ ] Center 注册业务应用：`client_id` / `client_secret`，redirect 白名单含  
      `https://mail.example.com/auth/sso/callback`
- [ ] Mail `.env`：
  - `SSO_ENABLED=true`
  - `SSO_AUTH_CENTER_URL=https://auth.example.com`
  - `SSO_CLIENT_ID` / `SSO_CLIENT_SECRET` 与 Center 一致
  - `SSO_REDIRECT_URI=https://mail.example.com/auth/sso/callback`
  - `SSO_BACKCHANNEL_SECRET=<随机长串>`
- [ ] Center `.env`：
  - `AUTH_CENTER_BACKCHANNEL_SECRET=<与上面相同>`
  - `AUTH_CENTER_BACKCHANNEL_LOGOUT_URLS=https://mail.example.com/api/auth/sso/backchannel-logout`
- [ ] 两侧容器互通（或经公网 HTTPS；back-channel 超时默认 3s）
- [ ] 老用户：`python scripts/migrate_users_to_auth_center.py`（先 dry-run，再 `--apply`）
- [ ] 验证：登录页 SSO 按钮；设置 → 账号信息「关联认证中心」；Center 登出后 mail 会话失效

## C. 不依赖 Center 时的注意

| 场景 | 行为 |
|---|---|
| Center 宕机 | 本地密码登录正常；SSO 登录/关联失败 |
| 仅有 SSO、无本地密码的账号 | Center 不可用时无法登录——避免只靠 SSO 建号 |
| CalDAV | 可用登录密码或「应用专用密码」（设置 → 登录与安全） |

## D. 上线后自检

```bash
curl -fsS https://mail.example.com/api/health
# 看 status / performance / background_tasks

# CalDAV（应用专用密码）
curl -u 'user@example.com:tm_xxxx-xxxx-...' -X PROPFIND \
  -H 'Depth: 0' https://mail.example.com/caldav/user@example.com/calendar/
```

相关文档：

- [部署指南](./deployment.md)
- [生产环境部署指南](../01-getting-started/production-deployment-guide.md)
- [Auth-Center 集成](../03-features/auth-center-integration.md)
