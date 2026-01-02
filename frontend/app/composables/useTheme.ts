export const useTheme = () => {
  const isDark = useState('isDark', () => false)
  const themeMode = useState<'light' | 'dark' | 'system'>('themeMode', () => 'system')
  const token = useCookie('token')

  // 系统主题媒体查询
  let mediaQuery: MediaQueryList | null = null

  // 初始化主题
  const initTheme = async () => {
    if (!import.meta.client) return
    
    // 监听系统主题变化
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', handleSystemThemeChange)

    // 优先从 localStorage 读取
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null
    if (saved) {
      themeMode.value = saved
    } else if (token.value) {
      // 从用户设置读取
      try {
        const user = await $fetch<{ theme: string }>('/api/users/me', {
          headers: { Authorization: `Bearer ${token.value}` }
        })
        // 兼容旧数据
        if (user.theme === 'dark') themeMode.value = 'dark'
        else if (user.theme === 'light') themeMode.value = 'light'
        else themeMode.value = 'system'
      } catch (e) {}
    }
    
    applyTheme()
  }

  // 处理系统主题变化
  const handleSystemThemeChange = (e: MediaQueryListEvent) => {
    if (themeMode.value === 'system') {
      isDark.value = e.matches
      updateDom()
    }
  }

  // 更新 DOM
  const updateDom = () => {
    if (!import.meta.client) return
    const html = document.querySelector('html')
    if (isDark.value) {
      html?.classList.add('dark')
    } else {
      html?.classList.remove('dark')
    }
  }

  // 应用主题逻辑
  const applyTheme = () => {
    if (themeMode.value === 'system') {
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    } else {
      isDark.value = themeMode.value === 'dark'
    }
    updateDom()
  }

  // 切换主题 (在 light/dark 之间切换，或者设置特定模式)
  const toggleTheme = async () => {
    // 如果当前是 system，切换到相反的固定模式
    if (themeMode.value === 'system') {
      setTheme(isDark.value ? 'light' : 'dark')
    } else {
      setTheme(themeMode.value === 'dark' ? 'light' : 'dark')
    }
  }

  // 设置主题模式
  const setTheme = async (mode: 'light' | 'dark' | 'system') => {
    themeMode.value = mode
    applyTheme()
    
    // 保存到 localStorage
    if (import.meta.client) {
      localStorage.setItem('theme', mode)
    }
    
    // 同步到后端
    if (token.value) {
      try {
        await $fetch('/api/users/me', {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${token.value}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ theme: mode })
        })
      } catch (e) {}
    }
  }

  return { isDark, themeMode, toggleTheme, initTheme, setTheme }
}