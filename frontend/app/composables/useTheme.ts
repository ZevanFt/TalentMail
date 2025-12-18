export const useTheme = () => {
  const isDark = useState('isDark', () => false)
  const token = useCookie('token')

  // 初始化主题
  const initTheme = async () => {
    if (!import.meta.client) return
    
    // 优先从 localStorage 读取
    const saved = localStorage.getItem('theme')
    if (saved) {
      isDark.value = saved === 'dark'
    } else if (token.value) {
      // 从用户设置读取
      try {
        const user = await $fetch<{ theme: string }>('/api/users/me', {
          headers: { Authorization: `Bearer ${token.value}` }
        })
        isDark.value = user.theme === 'dark'
      } catch (e) {}
    }
    
    applyTheme()
  }

  // 应用主题到 DOM
  const applyTheme = () => {
    if (!import.meta.client) return
    const html = document.querySelector('html')
    if (isDark.value) {
      html?.classList.add('dark')
    } else {
      html?.classList.remove('dark')
    }
  }

  // 切换主题
  const toggleTheme = async () => {
    isDark.value = !isDark.value
    applyTheme()
    
    // 保存到 localStorage
    if (import.meta.client) {
      localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
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
          body: JSON.stringify({ theme: isDark.value ? 'dark' : 'light' })
        })
      } catch (e) {}
    }
  }

  // 设置主题（不切换）
  const setTheme = (dark: boolean) => {
    isDark.value = dark
    applyTheme()
    if (import.meta.client) {
      localStorage.setItem('theme', dark ? 'dark' : 'light')
    }
  }

  return { isDark, toggleTheme, initTheme, setTheme }
}