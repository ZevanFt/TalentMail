export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}

export const useConfirmDialog = () => {
  const visible = useState('confirm-dialog-visible', () => false)
  const options = useState<ConfirmOptions | null>('confirm-dialog-options', () => null)
  const _resolver = useState<((v: boolean) => void) | null>('confirm-dialog-resolver', () => null)

  const confirm = (opts: ConfirmOptions | string): Promise<boolean> => {
    // 支持简写：confirm('确定删除？') 等价于 confirm({ message: '确定删除？' })
    const normalizedOpts = typeof opts === 'string' ? { message: opts } : opts

    return new Promise((resolve) => {
      options.value = normalizedOpts
      _resolver.value = resolve
      visible.value = true
    })
  }

  const handleConfirm = () => {
    _resolver.value?.(true)
    _resolver.value = null
    visible.value = false
  }

  const handleCancel = () => {
    _resolver.value?.(false)
    _resolver.value = null
    visible.value = false
  }

  return { visible, options, confirm, handleConfirm, handleCancel }
}
