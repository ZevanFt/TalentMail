import zhCN from '~/locales/zh-CN'
import enUS from '~/locales/en-US'

export type LocaleCode = 'zh-CN' | 'en-US'

const dictionaries: Record<LocaleCode, any> = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

const STORAGE_KEY = 'talentmail_locale'

function detectLocale(): LocaleCode {
  if (import.meta.client) {
    const saved = localStorage.getItem(STORAGE_KEY) as LocaleCode | null
    if (saved && dictionaries[saved]) return saved
    const nav = navigator.language || ''
    if (nav.toLowerCase().startsWith('en')) return 'en-US'
  }
  return 'zh-CN'
}

function resolve(obj: any, path: string): string {
  return path.split('.').reduce((acc, key) => (acc == null ? undefined : acc[key]), obj) ?? path
}

export function useI18n() {
  const locale = useState<LocaleCode>('i18n_locale', () => 'zh-CN')

  // 客户端挂载后读取偏好
  if (import.meta.client) {
    if (locale.value === 'zh-CN' && !localStorage.getItem(STORAGE_KEY)) {
      locale.value = detectLocale()
    }
  }

  const t = (key: string): string => {
    const dict = dictionaries[locale.value] || dictionaries['zh-CN']
    const hit = resolve(dict, key)
    if (hit !== key) return hit
    // 回退中文
    return resolve(dictionaries['zh-CN'], key)
  }

  const setLocale = (code: LocaleCode) => {
    if (!dictionaries[code]) return
    locale.value = code
    if (import.meta.client) localStorage.setItem(STORAGE_KEY, code)
  }

  const availableLocales = [
    { code: 'zh-CN' as LocaleCode, label: '简体中文' },
    { code: 'en-US' as LocaleCode, label: 'English' },
  ]

  return { locale, t, setLocale, availableLocales }
}
