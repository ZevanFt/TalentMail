import type { Config } from 'tailwindcss'

export default <Partial<Config>>{
    // 开启 class 模式，通过 HTML 标签上的 class="dark" 来切换
    darkMode: 'class',

    content: [
        './app/**/*.{vue,js,ts,jsx,tsx}',
        './app/app.vue'
    ],
    theme: {
        extend: {
            colors: {
                // 品牌色走 CSS 变量，便于主题预设运行时切换
                primary: {
                    DEFAULT: 'rgb(var(--color-primary) / <alpha-value>)',
                    hover: 'rgb(var(--color-primary-hover) / <alpha-value>)',
                    light: 'rgb(var(--color-primary-light) / <alpha-value>)',
                },
                bg: {
                    light: '#ffffff',      // 浅色背景
                    dark: '#0f1014',       // 深色背景
                    panel: '#f9fafb',      // 浅色面板背景 (灰色)
                    panelDark: '#18181b',  // 深色面板背景
                },
                border: {
                    light: '#e5e7eb',      // 浅色边框
                    dark: '#27272a',       // 深色边框
                }
            }
        }
    }
}