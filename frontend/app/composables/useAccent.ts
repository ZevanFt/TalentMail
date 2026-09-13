export type AccentCode = 'violet' | 'blue' | 'emerald' | 'rose' | 'amber' | 'cyan'

export const ACCENT_PRESETS: { code: AccentCode; label: string; swatch: string }[] = [
  { code: 'violet', label: '紫罗兰', swatch: '#a855f7' },
  { code: 'blue', label: '晴空蓝', swatch: '#3b82f6' },
  { code: 'emerald', label: '翡翠绿', swatch: '#10b981' },
  { code: 'rose', label: '玫瑰红', swatch: '#f43f5e' },
  { code: 'amber', label: '琥珀橙', swatch: '#f59e0b' },
  { code: 'cyan', label: '冰川青', swatch: '#06b6d4' },
]

const STORAGE_KEY = 'talentmail_accent'

export function useAccent() {
  const accent = useState<AccentCode>('accent_theme', () => 'violet')

  const applyAccent = (code: AccentCode) => {
    if (import.meta.client) {
      document.documentElement.setAttribute('data-accent', code)
    }
  }

  const initAccent = () => {
    if (!import.meta.client) return
    const saved = localStorage.getItem(STORAGE_KEY) as AccentCode | null
    if (saved && ACCENT_PRESETS.some(p => p.code === saved)) {
      accent.value = saved
    }
    applyAccent(accent.value)
  }

  const setAccent = (code: AccentCode) => {
    if (!ACCENT_PRESETS.some(p => p.code === code)) return
    accent.value = code
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, code)
      applyAccent(code)
    }
  }

  return { accent, setAccent, initAccent, ACCENT_PRESETS }
}
