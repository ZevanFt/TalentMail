// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // 指定源码目录为 app
  srcDir: 'app',
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  // 这里的 ~ 代表 srcDir (即 app 目录)
  css: ['~/assets/css/main.css'],

  // 运行时配置 - 从环境变量动态读取
  runtimeConfig: {
    public: {
      // NUXT_PUBLIC_ 前缀的变量会自动暴露给前端
      baseDomain: process.env.NUXT_PUBLIC_BASE_DOMAIN || 'talenting.test',
    }
  },

  // 3. 开启未来版本兼容性 (这可能就是您项目结构变化的原因)
  future: {
    compatibilityVersion: 4,
  },

  // Vite server configuration for development
  vite: {
    server: {
      // Allow requests from our custom domain via Caddy
      // We also include localhost for direct access
      allowedHosts: [process.env.NUXT_PUBLIC_WEB_DOMAIN || 'localhost', 'localhost'],
      // Ensure HMR works correctly through the proxy
      hmr: {
        host: process.env.NUXT_PUBLIC_WEB_DOMAIN || 'localhost',
      }
    }
  }
})
