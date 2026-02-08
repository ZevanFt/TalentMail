import { readFileSync } from 'fs'
import { resolve } from 'path'

// 从 config.json 读取当前环境配置
function loadConfig() {
  try {
    const configPath = resolve(__dirname, '../config.json')
    const config = JSON.parse(readFileSync(configPath, 'utf-8'))
    const envName = config.currentEnvironment || 'development'
    const envConfig = config.environments?.[envName] || {}
    
    const baseDomain = envConfig.baseDomain || 'talenting.test'
    const webPrefix = envConfig.webPrefix || 'mail'
    const webDomain = `${webPrefix}.${baseDomain}`
    
    return { baseDomain, webDomain, envName }
  } catch (e) {
    console.warn('无法读取 config.json，使用默认配置')
    return {
      baseDomain: 'talenting.test',
      webDomain: 'mail.talenting.test',
      envName: 'development'
    }
  }
}

const { baseDomain, webDomain, envName } = loadConfig()
console.log(`[nuxt.config] 当前环境: ${envName}, 域名: ${webDomain}`)

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // 指定源码目录为 app
  srcDir: 'app',
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss', '@vite-pwa/nuxt'],
  // 这里的 ~ 代表 srcDir (即 app 目录)
  css: ['~/assets/css/main.css'],

  // 运行时配置 - 从 config.json 动态读取
  runtimeConfig: {
    public: {
      baseDomain,
    }
  },

  // PWA 配置
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'TalentMail - 企业邮件系统',
      short_name: 'TalentMail',
      description: '全功能企业邮件系统，支持工作流自动化、邮件模板、多账号管理',
      theme_color: '#7C3AED',
      background_color: '#1F2937',
      display: 'standalone',
      orientation: 'portrait',
      scope: '/',
      start_url: '/',
      lang: 'zh-CN',
      categories: ['productivity', 'business', 'communication'],
      icons: [
        {
          src: '/icons/icon-64x64.png',
          sizes: '64x64',
          type: 'image/png'
        },
        {
          src: '/icons/icon-128x128.png',
          sizes: '128x128',
          type: 'image/png'
        },
        {
          src: '/icons/icon-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/icons/icon-256x256.png',
          sizes: '256x256',
          type: 'image/png'
        },
        {
          src: '/icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png',
          purpose: 'any maskable'
        }
      ],
      screenshots: [],
      shortcuts: [
        {
          name: '写邮件',
          short_name: '写邮件',
          description: '快速发送新邮件',
          url: '/?compose=true',
          icons: [{ src: '/icons/icon-192x192.png', sizes: '192x192' }]
        },
        {
          name: '设置',
          short_name: '设置',
          description: '管理账号和偏好',
          url: '/settings',
          icons: [{ src: '/icons/icon-192x192.png', sizes: '192x192' }]
        }
      ]
    },
    workbox: {
      // 缓存策略
      globPatterns: ['**/*.{js,css,html,png,svg,ico,woff2}'],
      // 运行时缓存 - 缓存 API 请求
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/.*\/api\/.*$/,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 // 1小时
            },
            networkTimeoutSeconds: 10
          }
        },
        {
          urlPattern: /\.(png|jpg|jpeg|svg|gif|webp)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'image-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 * 7 // 7天
            }
          }
        }
      ]
    },
    // 开发模式配置
    devOptions: {
      enabled: true,
      type: 'module'
    },
    // 客户端配置
    client: {
      installPrompt: true,
      periodicSyncForUpdates: 3600 // 每小时检查更新
    }
  },

  // 3. 开启未来版本兼容性 (这可能就是您项目结构变化的原因)
  future: {
    compatibilityVersion: 4,
  },

  // Vite server configuration for development
  // 注意：这些配置只在开发模式 (npm run dev) 下生效
  vite: {
    server: {
      // 允许来自自定义域名的请求（通过 Caddy 反向代理）
      // 域名从 config.json 的当前环境配置中动态读取
      allowedHosts: [
        webDomain,
        'localhost'
      ],
      // HMR (热模块替换) 配置
      // 开发环境：通过 Caddy 代理 WebSocket 连接实现热更新
      // 使用 mkcert 本地可信证书确保 wss:// 连接正常
      hmr: {
        // 让客户端自动检测协议（http->ws, https->wss）
        protocol: 'wss',
        // 使用配置的域名
        host: webDomain,
        // 通过 Caddy 443 端口代理
        clientPort: 443,
      }
    }
  }
})
