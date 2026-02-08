# 问题解决总结 - 空白页面问题

## 问题描述

**症状**：通过域名 https://mail.talenting.test 访问时，浏览器显示空白页面

**状态**：✅ **已解决**  
**解决时间**：2026-02-07  
**根本原因**：CSS z-index 层叠问题 + HTTPS 证书信任问题

## 问题根因分析

### 主要问题
1. **CSS 渲染冲突**：全局背景层的 CSS 规则干扰了主内容的显示
2. **HTTPS 证书问题**：自签名证书导致浏览器安全警告和 WebSocket 连接失败
3. **Vite HMR 配置**：WebSocket 连接配置不正确

### 具体表现
- 浏览器显示空白页面，但 curl 能正常获取 HTML
- 控制台出现 Cookie `__Secure-BUCKET` 被拒绝错误
- WebSocket 连接失败导致 HMR 无法工作

## 解决方案

### 1. 配置 mkcert 本地可信证书 ✅

**创建自动化脚本**：
```bash
# scripts/setup-mkcert.sh
#!/bin/bash
set -e

echo "🔧 设置 mkcert 本地可信证书..."

# 检查是否已安装 mkcert
if ! command -v mkcert &> /dev/null; then
    echo "📦 安装 mkcert..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
        chmod +x mkcert-v*-linux-amd64
        sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install mkcert
    else
        echo "❌ 不支持的操作系统: $OSTYPE"
        exit 1
    fi
fi

# 安装本地 CA
echo "🔐 安装本地证书颁发机构..."
mkcert -install

# 创建证书目录
mkdir -p config/caddy/certs

# 生成证书
echo "📜 生成 mail.talenting.test 证书..."
cd config/caddy/certs
mkcert mail.talenting.test localhost 127.0.0.1 ::1

# 重命名证书文件
mv mail.talenting.test+3.pem cert.pem
mv mail.talenting.test+3-key.pem key.pem

echo "✅ mkcert 证书设置完成！"
echo "📁 证书位置: config/caddy/certs/"
echo "🌐 现在可以通过 https://mail.talenting.test 安全访问"
```

**更新 Caddy 配置**：
```caddyfile
# config/caddy/Caddyfile
{
    auto_https off
    local_certs
}

{$WEB_DOMAIN:mail.talenting.test} {
    tls /etc/caddy/certs/cert.pem /etc/caddy/certs/key.pem
    
    # 健康检查
    handle /health {
        respond "Caddy is healthy" 200
    }
    
    # WebSocket 代理 (HMR)
    @websocket {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websocket localhost:3000
    
    # 后端 API 代理
    handle /api/* {
        reverse_proxy localhost:8000
    }
    
    # 前端代理
    reverse_proxy localhost:3000
}
```

### 2. 修复 Vite HMR WebSocket 配置 ✅

**更新 Nuxt 配置**：
```typescript
// frontend/nuxt.config.ts
export default defineNuxtConfig({
  vite: {
    server: {
      hmr: {
        protocol: 'wss',
        host: 'mail.talenting.test',
        clientPort: 443
      }
    }
  }
})
```

### 3. 解决 CSS 渲染问题 ✅

**修复全局背景层**：
```vue
<!-- frontend/app/app.vue -->
<style>
.global-bg-layer {
  /* 默认隐藏，只有启用背景时才显示 */
  display: none;
  z-index: -1;
}

/* 只有设置了背景图片时才显示背景层 */
html.has-custom-bg .global-bg-layer {
  display: block;
  opacity: var(--bg-custom-opacity, 0.3);
}
</style>
```

### 4. 完善背景功能透明效果 ✅

**添加完整的透明样式**：
```css
/* Header 透明效果 */
html.has-custom-bg.bg-area-header header {
  background: rgba(255, 255, 255, var(--bg-custom-overlay, 0.8)) !important;
  backdrop-filter: blur(12px) saturate(180%);
}

/* 主内容区透明效果 */
html.has-custom-bg.bg-area-main .bg-white {
  background: rgba(255, 255, 255, var(--bg-custom-overlay, 0.8)) !important;
  backdrop-filter: blur(8px) saturate(180%);
}
```

## 验证结果

### ✅ 功能正常
- 通过 https://mail.talenting.test 正常访问
- 登录页面完整显示
- 主应用界面正常渲染
- WebSocket HMR 连接正常
- 自定义背景功能完整工作

### ✅ 技术指标
- HTTPS 证书被浏览器信任
- 无控制台错误
- WebSocket 连接稳定
- 页面加载速度正常

## 关键文件变更

### 新增文件
- `scripts/setup-mkcert.sh` - mkcert 自动化安装脚本
- `config/caddy/certs/` - 证书目录

### 修改文件
- `config/caddy/Caddyfile` - 使用 mkcert 证书
- `frontend/nuxt.config.ts` - 修复 HMR WebSocket 配置
- `frontend/app/app.vue` - 完善背景功能样式
- `docker-compose.dev.yml` - 添加证书卷挂载
- `.env.caddy` - 简化配置

## 经验总结

### 问题诊断方法
1. **分层诊断**：从服务状态 → API 响应 → 前端渲染 → 浏览器显示
2. **工具组合**：curl + 浏览器开发者工具 + Docker 日志
3. **逐步排除**：先确认后端正常，再检查前端问题

### 解决方案选择
1. **mkcert 方案**：比自签名证书更可靠，浏览器完全信任
2. **WebSocket 配置**：必须匹配 HTTPS 协议和域名
3. **CSS 调试**：使用浏览器开发者工具检查元素层叠

### 开发环境最佳实践
1. **本地 HTTPS**：使用 mkcert 而非自签名证书
2. **域名配置**：统一使用 `.test` 域名
3. **容器化**：Docker Compose 统一管理服务
4. **自动化**：脚本化证书生成和环境配置

## 相关资源

- [mkcert 官方文档](https://github.com/FiloSottile/mkcert)
- [Caddy HTTPS 配置](https://caddyserver.com/docs/caddyfile/directives/tls)
- [Vite HMR 配置](https://vitejs.dev/config/server-options.html#server-hmr)

---

**创建时间**：2026-02-07  
**更新时间**：2026-02-07  
**状态**：✅ 已解决  
**优先级**：高 → 完成