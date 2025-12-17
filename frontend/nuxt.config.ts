import { readFileSync } from 'fs'
import { resolve } from 'path'

// 读取项目根目录的 config.json
const configPath = resolve(__dirname, '../config.json')
let baseDomain = 'talenting.test'
try {
  const appConfig = JSON.parse(readFileSync(configPath, 'utf-8'))
  const env = appConfig.currentEnvironment || 'development'
  baseDomain = appConfig.environments?.[env]?.baseDomain || 'talenting.test'
} catch (e) {
  console.warn('无法读取 config.json，使用默认配置')
}

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // 指定源码目录为 app
  srcDir: 'app',
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  // 这里的 ~ 代表 srcDir (即 app 目录)
  css: ['~/assets/css/main.css'],

  // 运行时配置 - 从 config.json 读取
  runtimeConfig: {
    public: {
      baseDomain,
    }
  },

  // 3. 开启未来版本兼容性 (这可能就是您项目结构变化的原因)
  future: {
    compatibilityVersion: 4,
  },

  // Vite server configuration
  vite: {
    server: {
      // Allow requests from our custom domain via Caddy
      // We also include localhost for direct access
      allowedHosts: [process.env.NUXT_PUBLIC_WEB_DOMAIN || 'mail.talenting.test', 'localhost'],
      // Ensure HMR works correctly through the proxy
      hmr: {
        host: process.env.NUXT_PUBLIC_WEB_DOMAIN || 'mail.talenting.test',
      }
    }
  }
})
