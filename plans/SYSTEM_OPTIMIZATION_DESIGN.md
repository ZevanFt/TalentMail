# TalentMail 系统优化设计文档

## 文档信息
- **创建日期**: 2026-01-05
- **版本**: v1.0
- **状态**: 持续更新中

---

## 一、已完成的优化功能

### 1. PWA (Progressive Web App) 支持 ✅

#### 1.1 技术概述
PWA 是一种现代 Web 技术，允许用户将网页应用安装为桌面/移动应用，无需 Electron 等打包工具。

| 对比项 | PWA | Electron |
|--------|-----|----------|
| 安装包大小 | **0 MB** | 100-300 MB |
| 更新方式 | 自动（打开即最新） | 需下载新版本 |
| 开发成本 | 零额外代码 | 需维护单独项目 |
| 跨平台 | Windows/Mac/Linux/iOS/Android | 需分别打包 |
| 离线支持 | Service Worker 缓存 | 本地运行 |

#### 1.2 实现方式

**1.2.1 安装依赖**
```bash
# 宿主机安装（用于类型定义）
cd frontend && npm install @vite-pwa/nuxt@latest --save-dev

# Docker 容器内安装（用于运行时）
docker compose -f docker-compose.dev.yml exec frontend npm install @vite-pwa/nuxt@latest --save-dev

# 重启服务
docker compose -f docker-compose.dev.yml restart frontend
```

**1.2.2 配置文件**
修改 `frontend/nuxt.config.ts`:
```typescript
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss', '@vite-pwa/nuxt'],
  
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'TalentMail - 企业邮件系统',
      short_name: 'TalentMail',
      theme_color: '#7C3AED',
      display: 'standalone',
      icons: [
        { src: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
        { src: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
      ],
      shortcuts: [
        { name: '写邮件', url: '/?compose=true' },
        { name: '设置', url: '/settings' }
      ]
    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,png,svg,ico,woff2}'],
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/.*\/api\/.*$/,
          handler: 'NetworkFirst',
          options: { cacheName: 'api-cache', expiration: { maxAgeSeconds: 3600 } }
        }
      ]
    }
  }
})
```

**1.2.3 生成应用图标**
```python
# 使用 Python PIL 生成多尺寸图标
from PIL import Image
img = Image.open('logo.png')
sizes = [64, 128, 192, 256, 512]
for size in sizes:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(f'frontend/public/icons/icon-{size}x{size}.png')
```

**1.2.4 解决 TypeScript 报错**
IDE 可能显示 `pwa` 配置不存在的报错，这是因为宿主机的 `.nuxt` 目录类型定义未更新。

解决方法：
```bash
# 方法1：重新生成类型（需要 sudo 权限）
sudo rm -rf frontend/.nuxt
cd frontend && npm run prepare

# 方法2：忽略报错（不影响实际运行）
# 容器内已正确生成类型定义
```

#### 1.3 使用方式
1. **浏览器安装**: 访问应用后，地址栏右侧出现安装图标 ⬇️
2. **手机安装**: 浏览器菜单 → "添加到主屏幕"
3. **安装后**: 独立窗口运行，像原生应用一样使用

### 2. 邮箱复制按钮 ✅
在 Header 组件的用户信息卡片中，邮箱显示位置添加了一键复制按钮。

**文件**: `frontend/app/components/layout/Header.vue`
```vue
<button @click.stop="copyEmail" class="...">
  <Check v-if="copied" class="w-3 h-3 text-green-500" />
  <Copy v-else class="w-3 h-3 text-gray-400" />
</button>
```

---

## 二、待实现的优化功能

### 高优先级 🔴

| 功能 | 当前状态 | 优化目标 | 复杂度 |
|------|----------|----------|--------|
| **邮件批量操作** | 只能单选 | 多选框 + 批量删除/移动/标记 | 中 |
| **键盘快捷键** | 无 | j/k 上下邮件、r 回复、a 归档、d 删除 | 低 |
| **高级搜索** | 基础关键词搜索 | 日期范围、发件人、附件、标签过滤 | 中 |
| **撤销发送** | 无 | 发送后 5 秒内可撤销 | 中 |

### 中优先级 🟡

| 功能 | 当前状态 | 优化目标 | 复杂度 |
|------|----------|----------|--------|
| **邮件预览悬停** | 需点击查看 | 鼠标悬停显示预览卡片 | 低 |
| **附件在线预览** | 只能下载 | 图片/PDF 在线预览 | 中 |
| **会话/线程视图** | 按时间列表 | 相同主题邮件分组显示 | 高 |
| **收件人自动补全** | 无 | 历史发送 + 通讯录自动建议 | 中 |
| **模板快捷插入** | 需进模板管理 | 写邮件时快速选择常用模板 | 低 |

### 低优先级 🟢

| 功能 | 当前状态 | 优化目标 | 复杂度 |
|------|----------|----------|--------|
| **深色模式优化** | 基础支持 | 优化对比度、自动跟随系统 | 低 |
| **列表密度选项** | 固定 | 紧凑/舒适/宽松三种密度 | 低 |
| **多签名管理** | 单一签名 | 多签名切换 | 低 |
| **自定义文件夹** | 固定结构 | 用户创建自定义文件夹 | 中 |
| **邮件统计仪表盘** | 无 | 日/周/月发送接收统计 | 中 |

---

## 三、技术层面优化建议

### 3.1 性能优化

| 方面 | 建议 | 优先级 |
|------|------|--------|
| **虚拟滚动** | 大量邮件时使用虚拟列表 | 高 |
| **图片懒加载** | 附件预览图懒加载 | 中 |
| **API 响应缓存** | SWR/TanStack Query 风格缓存 | 中 |
| **WebSocket 优化** | 心跳检测、断线重连 | 中 |

### 3.2 用户体验优化

| 方面 | 建议 | 优先级 |
|------|------|--------|
| **骨架屏** | 加载时显示占位内容 | 中 |
| **乐观更新** | 操作后立即更新UI，后台同步 | 中 |
| **手势支持** | 移动端左滑删除/右滑归档 | 低 |
| **拖放排序** | 文件夹、标签拖放排序 | 低 |

### 3.3 离线支持（基于 PWA）

已配置的缓存策略：
- **静态资源**: CacheFirst（优先使用缓存）
- **API 请求**: NetworkFirst（优先使用网络，超时后使用缓存）
- **图片资源**: CacheFirst + 7天过期

扩展建议：
- IndexedDB 本地存储草稿
- 离线发送队列（恢复网络后自动发送）

---

## 四、系统工作流待讨论问题

### 4.1 当前实现状态
- ✅ 工作流编辑器 UI（Vue Flow）
- ✅ 工作流模板系统
- ✅ 数据库模型和 API
- ⚠️ 工作流运行时引擎（部分实现）
- ⚠️ 触发器与事件绑定
- ⚠️ 条件节点逻辑

### 4.2 待讨论的功能点
1. **触发器类型**
   - 邮件接收触发
   - 定时触发
   - 手动触发
   - Webhook 触发

2. **节点类型完善**
   - 发送邮件节点
   - 条件判断节点
   - 延时等待节点
   - HTTP 请求节点
   - 变量设置节点

3. **运行时问题**
   - 工作流执行日志
   - 错误处理和重试
   - 并发控制

4. **用户体验**
   - 节点配置面板
   - 变量选择器
   - 测试运行模式

### 4.3 测试协同计划
可以进行协同测试，通过读取日志发现问题：
```bash
# 查看后端日志
docker compose -f docker-compose.dev.yml logs backend --tail=100 -f

# 查看前端日志
docker compose -f docker-compose.dev.yml logs frontend --tail=100 -f
```

---

## 五、相关文件索引

| 功能模块 | 文件路径 |
|----------|----------|
| PWA 配置 | [`frontend/nuxt.config.ts`](../frontend/nuxt.config.ts:48) |
| 应用图标 | [`frontend/public/icons/`](../frontend/public/icons/) |
| Header 组件 | [`frontend/app/components/layout/Header.vue`](../frontend/app/components/layout/Header.vue) |
| 工作流编辑器 | [`frontend/app/pages/workflows/[id].vue`](../frontend/app/pages/workflows/[id].vue) |
| 工作流运行时 | [`backend/core/workflow_runtime.py`](../backend/core/workflow_runtime.py) |
| 工作流服务 | [`backend/core/workflow_service.py`](../backend/core/workflow_service.py) |
| 工作流 API | [`backend/api/workflows.py`](../backend/api/workflows.py) |

---

## 六、版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-01-05 | 初始版本，包含 PWA 实现和优化计划 |