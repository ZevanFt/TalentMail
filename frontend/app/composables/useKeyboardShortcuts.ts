/**
 * 键盘快捷键系统
 * 
 * 快捷键列表：
 * - j/k: 上/下选择邮件
 * - Enter: 打开选中的邮件
 * - r: 回复
 * - a: 回复全部
 * - f: 转发
 * - e: 归档
 * - #/Delete: 删除
 * - s: 切换星标
 * - u: 切换已读/未读
 * - c: 写新邮件
 * - /: 聚焦搜索框
 * - Escape: 关闭弹窗/取消选择
 * - ?: 显示快捷键帮助
 */

interface ShortcutDefinition {
  key: string
  label: string
  description: string
  category: string
}

// 快捷键定义
export const SHORTCUTS: ShortcutDefinition[] = [
  // 导航
  { key: 'j', label: 'J', description: '选择下一封邮件', category: '导航' },
  { key: 'k', label: 'K', description: '选择上一封邮件', category: '导航' },
  { key: 'Enter', label: 'Enter', description: '打开选中的邮件', category: '导航' },
  { key: '/', label: '/', description: '聚焦搜索框', category: '导航' },
  { key: 'Escape', label: 'Esc', description: '关闭弹窗/取消', category: '导航' },
  
  // 操作
  { key: 'c', label: 'C', description: '写新邮件', category: '操作' },
  { key: 'r', label: 'R', description: '回复', category: '操作' },
  { key: 'a', label: 'A', description: '回复全部', category: '操作' },
  { key: 'f', label: 'F', description: '转发', category: '操作' },
  
  // 邮件管理
  { key: 's', label: 'S', description: '切换星标', category: '邮件管理' },
  { key: 'u', label: 'U', description: '切换已读/未读', category: '邮件管理' },
  { key: 'e', label: 'E', description: '归档', category: '邮件管理' },
  { key: '#', label: '#', description: '删除', category: '邮件管理' },
  { key: 'Delete', label: 'Delete', description: '删除', category: '邮件管理' },
  
  // 帮助
  { key: '?', label: '?', description: '显示快捷键帮助', category: '帮助' },
]

// 按分类分组
export const getShortcutsByCategory = () => {
  const categories: Record<string, ShortcutDefinition[]> = {}
  for (const shortcut of SHORTCUTS) {
    if (!categories[shortcut.category]) {
      categories[shortcut.category] = []
    }
    categories[shortcut.category]!.push(shortcut)
  }
  return categories
}

export const useKeyboardShortcuts = () => {
  const { emails, selectedEmailId, selectedEmailDetail, loadEmailDetail, toggleRead, toggleStar, removeEmail, startReply, startReplyAll, startForward } = useEmails()
  const { isComposeOpen } = useGlobalModal()
  const { bulkArchiveEmails } = useApi()
  
  // 快捷键帮助弹窗状态
  const showShortcutsHelp = useState('showShortcutsHelp', () => false)
  
  // 快捷键是否启用（在输入框中禁用）
  const isEnabled = ref(true)
  
  // 检查是否在输入元素中
  const isInputActive = () => {
    const activeElement = document.activeElement
    if (!activeElement) return false
    const tagName = activeElement.tagName.toLowerCase()
    return tagName === 'input' || tagName === 'textarea' || (activeElement as HTMLElement).isContentEditable
  }
  
  // 获取当前选中邮件的索引
  const getCurrentIndex = () => {
    if (!selectedEmailId.value) return -1
    return emails.value.findIndex(e => e.id === selectedEmailId.value)
  }
  
  // 选择邮件（通过索引）
  const selectEmailByIndex = (index: number) => {
    if (index >= 0 && index < emails.value.length) {
      const email = emails.value[index]
      if (!email) return
      const emailId = email.id
      selectedEmailId.value = emailId
      loadEmailDetail(emailId)
      
      // 滚动到可见区域
      nextTick(() => {
        const emailElement = document.querySelector(`[data-email-id="${emailId}"]`)
        emailElement?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      })
    }
  }
  
  // 选择下一封邮件 (j)
  const selectNextEmail = () => {
    const currentIndex = getCurrentIndex()
    if (currentIndex < emails.value.length - 1) {
      selectEmailByIndex(currentIndex + 1)
    } else if (currentIndex === -1 && emails.value.length > 0) {
      // 如果没有选中，选择第一封
      selectEmailByIndex(0)
    }
  }
  
  // 选择上一封邮件 (k)
  const selectPrevEmail = () => {
    const currentIndex = getCurrentIndex()
    if (currentIndex > 0) {
      selectEmailByIndex(currentIndex - 1)
    } else if (currentIndex === -1 && emails.value.length > 0) {
      // 如果没有选中，选择最后一封
      selectEmailByIndex(emails.value.length - 1)
    }
  }
  
  // 切换星标 (s)
  const handleToggleStar = () => {
    if (selectedEmailDetail.value) {
      toggleStar(selectedEmailDetail.value.id, !selectedEmailDetail.value.is_starred)
    }
  }
  
  // 切换已读/未读 (u)
  const handleToggleRead = () => {
    if (selectedEmailDetail.value) {
      toggleRead(selectedEmailDetail.value.id, !selectedEmailDetail.value.is_read)
    }
  }
  
  // 归档 (e)
  const handleArchive = async () => {
    if (selectedEmailDetail.value) {
      try {
        await bulkArchiveEmails([selectedEmailDetail.value.id])
        // 选择下一封或上一封
        const currentIndex = getCurrentIndex()
        if (currentIndex < emails.value.length - 1) {
          selectEmailByIndex(currentIndex) // 列表会刷新，所以保持索引
        } else if (currentIndex > 0) {
          selectEmailByIndex(currentIndex - 1)
        }
      } catch (e) {
        console.error('归档失败:', e)
      }
    }
  }
  
  // 删除 (#/Delete)
  const handleDelete = () => {
    if (selectedEmailDetail.value) {
      removeEmail(selectedEmailDetail.value.id)
    }
  }
  
  // 回复 (r)
  const handleReply = () => {
    if (selectedEmailDetail.value) {
      startReply(selectedEmailDetail.value)
      isComposeOpen.value = true
    }
  }
  
  // 回复全部 (a)
  const handleReplyAll = () => {
    if (selectedEmailDetail.value) {
      startReplyAll(selectedEmailDetail.value)
      isComposeOpen.value = true
    }
  }
  
  // 转发 (f)
  const handleForward = () => {
    if (selectedEmailDetail.value) {
      startForward(selectedEmailDetail.value)
      isComposeOpen.value = true
    }
  }
  
  // 写新邮件 (c)
  const handleCompose = () => {
    isComposeOpen.value = true
  }
  
  // 聚焦搜索框 (/)
  const handleFocusSearch = () => {
    const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement
    if (searchInput) {
      searchInput.focus()
    }
  }
  
  // 显示/隐藏帮助 (?)
  const toggleHelp = () => {
    showShortcutsHelp.value = !showShortcutsHelp.value
  }
  
  // 关闭弹窗 (Escape)
  const handleEscape = () => {
    if (showShortcutsHelp.value) {
      showShortcutsHelp.value = false
    } else if (isComposeOpen.value) {
      isComposeOpen.value = false
    }
  }
  
  // 键盘事件处理器
  const handleKeyDown = (event: KeyboardEvent) => {
    // 在输入框中不处理快捷键（除了 Escape）
    if (isInputActive() && event.key !== 'Escape') {
      return
    }
    
    // 如果有修饰键，不处理（允许浏览器默认行为）
    if (event.ctrlKey || event.metaKey || event.altKey) {
      return
    }
    
    switch (event.key) {
      case 'j':
        event.preventDefault()
        selectNextEmail()
        break
      case 'k':
        event.preventDefault()
        selectPrevEmail()
        break
      case 'Enter':
        // Enter 在邮件列表中打开邮件（如果有选中但未加载详情）
        if (selectedEmailId.value && !selectedEmailDetail.value) {
          event.preventDefault()
          loadEmailDetail(selectedEmailId.value)
        }
        break
      case 's':
        event.preventDefault()
        handleToggleStar()
        break
      case 'u':
        event.preventDefault()
        handleToggleRead()
        break
      case 'e':
        event.preventDefault()
        handleArchive()
        break
      case '#':
      case 'Delete':
        event.preventDefault()
        handleDelete()
        break
      case 'r':
        event.preventDefault()
        handleReply()
        break
      case 'a':
        event.preventDefault()
        handleReplyAll()
        break
      case 'f':
        event.preventDefault()
        handleForward()
        break
      case 'c':
        event.preventDefault()
        handleCompose()
        break
      case '/':
        event.preventDefault()
        handleFocusSearch()
        break
      case '?':
        event.preventDefault()
        toggleHelp()
        break
      case 'Escape':
        handleEscape()
        break
    }
  }
  
  // 注册/注销事件监听
  const register = () => {
    if (import.meta.client) {
      window.addEventListener('keydown', handleKeyDown)
    }
  }
  
  const unregister = () => {
    if (import.meta.client) {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }
  
  return {
    showShortcutsHelp,
    isEnabled,
    register,
    unregister,
    selectNextEmail,
    selectPrevEmail,
    handleToggleStar,
    handleToggleRead,
    handleArchive,
    handleDelete,
    handleReply,
    handleReplyAll,
    handleForward,
    handleCompose,
    handleFocusSearch,
    toggleHelp,
    shortcuts: SHORTCUTS,
    getShortcutsByCategory
  }
}