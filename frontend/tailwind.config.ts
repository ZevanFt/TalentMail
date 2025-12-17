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
                // 定义语义化颜色
                primary: {
                    DEFAULT: '#a855f7', // 紫色 (对应按钮)
                    hover: '#9333ea',
                    light: '#f3e8ff',   // 浅紫色背景 (选中态)
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