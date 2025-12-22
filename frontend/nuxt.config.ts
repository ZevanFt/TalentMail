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
  modules: ['@nuxtjs/tailwindcss'],
  // 这里的 ~ 代表 srcDir (即 app 目录)
  css: ['~/assets/css/main.css'],

  // 运行时配置 - 从 config.json 动态读取
  runtimeConfig: {
    public: {
      baseDomain,
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
      // Allow requests from our custom domain via Caddy
      // 域名从 config.json 的当前环境配置中读取
      allowedHosts: [
        webDomain,
        'localhost'
      ],
      // Ensure HMR works correctly through the proxy
      hmr: {
        host: webDomain,
      }
    }
  }
})
