# TalentMail 测试指南

## 📧 邮件账户信息

### Admin 账户
- **邮箱**: `admin@talenting.test`
- **密码**: `adminpassword`

## 🧪 使用 Thunderbird 测试

### 配置账户
- IMAP: `localhost:143` (无加密)
- SMTP: `localhost:587` (STARTTLS)

### 测试步骤
1. 用 admin 账户发邮件给 `testuser_1764489698@talenting.test`
2. 切换账户检查收件箱
3. 回复邮件测试双向通信

## 🔍 检查日志
```bash
docker logs talentmail-mailserver-1 --tail 50
```

## 📊 检查用户
```bash
docker exec talentmail-mailserver-1 setup email list