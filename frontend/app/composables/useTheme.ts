export const useTheme = () => {
  const isDark = useState('isDark', () => false)

  const toggleTheme = () => {
    isDark.value = !isDark.value
    if (import.meta.client) {
      const html = document.querySelector('html')
      if (isDark.value) {
        html?.classList.add('dark')
      } else {
        html?.classList.remove('dark')
      }
    }
  }

  return { isDark, toggleTheme }
}