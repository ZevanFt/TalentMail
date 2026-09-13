# CalDAV 只读接入

TalentMail 提供 **只读 CalDAV 子集**，可用系统账号密码让 Thunderbird / Apple Calendar 等客户端同步日历。

## 支持能力

| 方法 | 说明 |
|------|------|
| OPTIONS | 声明 DAV 能力 |
| PROPFIND | principal / calendar-home / calendar-collection |
| GET | 下载整本日历 `.ics` |
| REPORT | calendar-collection 属性（简化） |

暂不支持：PUT/DELETE 写事件、sync-token 增量、VTODO/VJOURNAL。

## 客户端配置

| 项 | 值 |
|----|----|
| 服务器 URL | `https://mail.example.com/.well-known/caldav` 或 `https://mail.example.com/caldav/` |
| 用户名 | 完整邮箱，如 `alice@example.com` |
| 密码 | 登录密码（SSO 用户请先在 Web 设置密码） |
| 日历路径 | `/caldav/alice@example.com/calendar/` |

### Thunderbird

1. 日历 → 新建日历 → 在网络上
2. 位置填：`https://mail.example.com/caldav/alice@example.com/calendar/`
3. 输入邮箱与密码

### curl 自测

```bash
curl -u 'alice@example.com:password' \
  -X PROPFIND -H 'Depth: 1' \
  https://mail.example.com/caldav/

# 直接拉 ICS
curl -u 'alice@example.com:password' \
  https://mail.example.com/caldav/alice@example.com/calendar.ics
```

## 安全说明

- 走 HTTPS（生产 Caddy 已终结 TLS）
- Basic Auth，密码仅用于校验 bcrypt 哈希
- 建议为第三方客户端使用独立应用密码（后续可加）

## 相关文档

- [API Reference](../03-features/api-reference.md)
- [备份恢复](../05-operations/backup-restore.md)
