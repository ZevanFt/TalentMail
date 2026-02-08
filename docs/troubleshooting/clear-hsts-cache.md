# 清除浏览器 HSTS 缓存

## 问题描述

当浏览器访问 `mail.talenting.test` 时显示"此站点的安全证书不受信任"或"ERR_CONNECTION_CLOSED"错误，这是因为浏览器记住了之前的 HTTPS 访问，强制要求使用 HTTPS（HSTS - HTTP Strict Transport Security）。

## 解决方案

### Chrome/Edge 浏览器

1. 在地址栏输入：`chrome://net-internals/#hsts`
2. 在 "Delete domain security policies" 部分输入：`mail.talenting.test`
3. 点击 "Delete" 按钮
4. 关闭并重新打开浏览器
5. 访问 `http://mail.talenting.test`（确保使用 http://）

### Firefox 浏览器

1. 关闭 Firefox
2. 找到 Firefox 配置文件夹：
   - macOS: `~/Library/Application Support/Firefox/Profiles/`
   - Linux: `~/.mozilla/firefox/`
   - Windows: `%APPDATA%\Mozilla\Firefox\Profiles\`
3. 删除 `SiteSecurityServiceState.txt` 文件
4. 重新打开 Firefox
5. 访问 `http://mail.talenting.test`

### Safari 浏览器

1. 关闭 Safari
2. 打开终端，执行：
   ```bash
   rm ~/Library/Cookies/HSTS.plist
   ```
3. 重新打开 Safari
4. 访问 `http://mail.talenting.test`

## 替代方案：使用 HTTPS（推荐用于生产环境）

如果您希望继续使用 HTTPS，可以配置 Caddy 使用自签名证书：

1. 修改 `.env.caddy`：
   ```bash
   # 移除 http:// 前缀，让 Caddy 自动启用 HTTPS
   WEB_DOMAIN=mail.talenting.test
   
   # 启用本地自签名证书
   USE_LOCAL_CERTS=local_certs
   ```

2. 重启 Caddy：
   ```bash
   docker compose -f docker-compose.dev.yml restart caddy
   ```

3. 在浏览器中接受自签名证书警告

## 验证

清除 HSTS 后，在浏览器中访问：
- `http://mail.talenting.test` - 应该正常显示登录页面
- 或者直接访问 `http://localhost:3000` - 绕过域名直接访问前端

## 注意事项

- 开发环境建议使用 HTTP 以避免证书问题
- 生产环境必须使用 HTTPS 以确保安全
- 如果问题持续，尝试使用隐私/无痕模式访问