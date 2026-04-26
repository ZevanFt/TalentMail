export interface ToastAction {
  label: string
  onClick: () => void | Promise<void>
}

export interface ToastItem {
  id: number
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration: number
  action?: ToastAction
}

interface ToastOptions {
  action?: ToastAction
}

let _nextId = 0

export const useToast = () => {
  const toasts = useState<ToastItem[]>('global-toasts', () => [])

  const MAX_TOASTS = 5

  const add = (type: ToastItem['type'], message: string, duration = 3000, options?: ToastOptions) => {
    const id = ++_nextId
    const item: ToastItem = { id, type, message, duration, action: options?.action }

    toasts.value = [...toasts.value, item]

    // 超过最大数量，移除最旧的
    if (toasts.value.length > MAX_TOASTS) {
      toasts.value = toasts.value.slice(-MAX_TOASTS)
    }

    // 自动移除（duration=0 表示手动关闭）
    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }

    return id
  }

  const remove = (id: number) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return {
    toasts: readonly(toasts),
    success: (message: string, duration?: number, options?: ToastOptions) => add('success', message, duration ?? 3000, options),
    error: (message: string, duration?: number, options?: ToastOptions) => add('error', message, duration ?? 5000, options),
    warning: (message: string, duration?: number, options?: ToastOptions) => add('warning', message, duration ?? 4000, options),
    info: (message: string, duration?: number, options?: ToastOptions) => add('info', message, duration ?? 3000, options),
    remove,
  }
}
