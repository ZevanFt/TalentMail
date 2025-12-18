interface Email {
  id: number
  subject: string
  sender: string
  snippet: string
  received_at: string
  is_read: boolean
  is_starred: boolean
  has_attachments: boolean
  is_tracked?: boolean
  delivery_status?: string  // pending/sending/sent/delivered/failed
}

interface EmailDetail extends Email {
  recipients: string
  body_html: string | null
  body_text: string | null
  is_tracked?: boolean
  delivery_status?: string
  delivery_error?: string
}

// 写邮件模式
type ComposeMode = 'compose' | 'reply' | 'replyAll' | 'forward' | 'draft'

interface ComposeState {
  mode: ComposeMode
  originalEmail: EmailDetail | null
}

interface Folder {
  id: number
  name: string
  role: string
  unread_count: number
}

// 默认文件夹配置（前端预设，避免等待后端返回时页面抖动）
const DEFAULT_FOLDERS: Folder[] = [
  { id: 0, name: '收件箱', role: 'inbox', unread_count: 0 },
  { id: 0, name: '已发送', role: 'sent', unread_count: 0 },
  { id: 0, name: '草稿箱', role: 'drafts', unread_count: 0 },
  { id: 0, name: '已删除', role: 'trash', unread_count: 0 },
  { id: 0, name: '垃圾邮件', role: 'spam', unread_count: 0 },
  { id: 0, name: '归档', role: 'archive', unread_count: 0 },
]

export const useEmails = () => {
  const { getEmails, getEmail, getFolders, syncEmails, markEmailRead, deleteEmail, markEmailStarred, snoozeEmail, getAllEmails, getSnoozedEmails, searchEmails } = useApi()
  
  const emails = useState<Email[]>('emails', () => [])
  // 使用默认文件夹初始化，后端返回后会更新 id 和 unread_count
  const folders = useState<Folder[]>('folders', () => [...DEFAULT_FOLDERS])
  const currentFolderId = useState<number | null>('currentFolderId', () => null)
  const selectedEmailId = useState<number | null>('selectedEmailId', () => null)
  const selectedEmailDetail = useState<EmailDetail | null>('selectedEmailDetail', () => null)
  const loading = useState('emailsLoading', () => false)
  const syncing = useState('emailsSyncing', () => false)

  // 加载文件夹列表（更新 id 和 unread_count）
  const loadFolders = async () => {
    try {
      const res = await getFolders()
      // 合并后端数据到默认文件夹（保持顺序，更新 id 和 unread_count）
      const backendFolders = res.data as Folder[]
      folders.value = DEFAULT_FOLDERS.map(df => {
        const bf = backendFolders.find(f => f.role === df.role)
        return bf ? { ...df, id: bf.id, unread_count: bf.unread_count } : df
      })
      // 默认选中收件箱
      const inbox = folders.value.find((f: Folder) => f.role === 'inbox')
      if (inbox && inbox.id && !currentFolderId.value) {
        currentFolderId.value = inbox.id
      }
    } catch (e) {
      console.error('加载文件夹失败:', e)
    }
  }

  // 加载邮件列表
  const loadEmails = async (folderId?: number) => {
    const id = folderId || currentFolderId.value
    if (!id) return
    
    // 切换文件夹时清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    
    loading.value = true
    try {
      const res = await getEmails(id)
      emails.value = res.data.items
      currentFolderId.value = id
    } catch (e) {
      console.error('加载邮件失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载邮件详情
  const loadEmailDetail = async (id: number) => {
    try {
      const res = await getEmail(id)
      selectedEmailDetail.value = res.data
      selectedEmailId.value = id
      
      // 自动标记为已读（后端已处理，这里更新本地状态）
      const email = emails.value.find(e => e.id === id)
      if (email && !email.is_read) {
        email.is_read = true
      }
    } catch (e) {
      console.error('加载邮件详情失败:', e)
    }
  }

  // 标记已读/未读
  const toggleRead = async (id: number, isRead: boolean) => {
    try {
      await markEmailRead(id, isRead)
      // 更新本地状态
      const email = emails.value.find(e => e.id === id)
      if (email) email.is_read = isRead
      if (selectedEmailDetail.value?.id === id) {
        selectedEmailDetail.value.is_read = isRead
      }
    } catch (e) {
      console.error('标记已读失败:', e)
    }
  }

  // 切换星标
  const toggleStar = async (id: number, isStarred: boolean) => {
    try {
      await markEmailStarred(id, isStarred)
      // 更新本地状态
      const email = emails.value.find(e => e.id === id)
      if (email) email.is_starred = isStarred
      if (selectedEmailDetail.value?.id === id) {
        selectedEmailDetail.value.is_starred = isStarred
      }
    } catch (e) {
      console.error('标记星标失败:', e)
    }
  }

  // 设置待办
  const snooze = async (id: number, snoozeUntil: string) => {
    try {
      await snoozeEmail(id, snoozeUntil)
      // 从当前列表移除（因为已设为待办）
      emails.value = emails.value.filter(e => e.id !== id)
    } catch (e) {
      console.error('设置待办失败:', e)
    }
  }

  // 删除邮件
  const removeEmail = async (id: number) => {
    try {
      await deleteEmail(id)
      // 从列表中移除
      emails.value = emails.value.filter(e => e.id !== id)
      // 如果删除的是当前选中的邮件，清空详情
      if (selectedEmailId.value === id) {
        selectedEmailId.value = null
        selectedEmailDetail.value = null
      }
    } catch (e) {
      console.error('删除邮件失败:', e)
    }
  }

  // 同步邮件
  const sync = async () => {
    syncing.value = true
    try {
      const res = await syncEmails()
      if (res.data.new_emails > 0) {
        await loadEmails()
        // 刷新文件夹未读数
        await loadFolders()
      }
      return res.data.new_emails
    } catch (e) {
      console.error('同步邮件失败:', e)
      return 0
    } finally {
      syncing.value = false
    }
  }

  // WebSocket 实时通知
  const ws = useState<WebSocket | null>('emailWs', () => null)
  
  const connectWebSocket = () => {
    const { token } = useApi()
    if (!token.value || ws.value) return
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/${token.value}`
    
    ws.value = new WebSocket(wsUrl)
    
    ws.value.onopen = () => {
      console.log('WebSocket 已连接')
    }
    
    ws.value.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'new_email') {
        // 收到新邮件通知，刷新列表
        await loadEmails()
        await loadFolders()
      }
    }
    
    ws.value.onclose = () => {
      console.log('WebSocket 已断开')
      ws.value = null
      // 3秒后重连
      setTimeout(connectWebSocket, 3000)
    }
    
    ws.value.onerror = () => {
      ws.value?.close()
    }
  }
  
  const disconnectWebSocket = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }
  
  // 兼容：如果 WebSocket 不可用，回退到轮询
  const autoSyncInterval = useState<ReturnType<typeof setInterval> | null>('autoSyncInterval', () => null)
  
  const startAutoSync = () => {
    // 优先使用 WebSocket
    connectWebSocket()
    
    // 备用轮询（60秒，作为保底）
    if (autoSyncInterval.value) return
    autoSyncInterval.value = setInterval(async () => {
      if (!syncing.value) {
        await sync()
      }
    }, 60000)
  }
  
  const stopAutoSync = () => {
    disconnectWebSocket()
    if (autoSyncInterval.value) {
      clearInterval(autoSyncInterval.value)
      autoSyncInterval.value = null
    }
  }

  // 格式化时间
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()
    return isToday
      ? date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      : date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  // 当前筛选条件（用于虚拟文件夹）
  const currentFilter = useState<Record<string, any> | null>('currentFilter', () => null)

  // 加载带筛选的邮件（用于虚拟文件夹）
  const loadFilteredEmails = async (filter: Record<string, any>) => {
    // 清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    
    loading.value = true
    currentFilter.value = filter
    try {
      // 使用所有邮件 API 进行筛选
      const isRead = 'is_read' in filter ? filter.is_read : undefined
      const isStarred = 'is_starred' in filter ? filter.is_starred : undefined
      // 未读邮件只查询收件箱
      const inboxOnly = isRead === false
      const res = await getAllEmails(1, 50, isRead, isStarred, inboxOnly)
      emails.value = res.data.items
    } catch (e) {
      console.error('加载筛选邮件失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载待办邮件
  const loadSnoozedEmails = async () => {
    // 清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    
    loading.value = true
    try {
      const res = await getSnoozedEmails()
      emails.value = res.data.items
    } catch (e) {
      console.error('加载待办邮件失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载所有邮件
  const loadAllEmails = async () => {
    // 清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    
    loading.value = true
    try {
      const res = await getAllEmails()
      emails.value = res.data.items
    } catch (e) {
      console.error('加载所有邮件失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 搜索状态
  const searchQuery = useState<string>('searchQuery', () => '')
  const isSearching = useState<boolean>('isSearching', () => false)

  // 搜索邮件
  const search = async (query: string) => {
    if (!query.trim()) {
      // 清空搜索，返回收件箱
      searchQuery.value = ''
      isSearching.value = false
      await loadEmails()
      return
    }
    
    loading.value = true
    searchQuery.value = query
    isSearching.value = true
    try {
      const res = await searchEmails(query)
      emails.value = res.data.items
    } catch (e) {
      console.error('搜索邮件失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 清除搜索
  const clearSearch = async () => {
    searchQuery.value = ''
    isSearching.value = false
    await loadEmails()
  }

  // 写邮件状态
  const composeState = useState<ComposeState>('composeState', () => ({
    mode: 'compose',
    originalEmail: null
  }))

  // 开始回复
  const startReply = (email: EmailDetail) => {
    composeState.value = { mode: 'reply', originalEmail: email }
  }

  // 开始回复全部
  const startReplyAll = (email: EmailDetail) => {
    composeState.value = { mode: 'replyAll', originalEmail: email }
  }

  // 开始转发
  const startForward = (email: EmailDetail) => {
    composeState.value = { mode: 'forward', originalEmail: email }
  }

  // 重置写邮件状态
  const resetCompose = () => {
    composeState.value = { mode: 'compose', originalEmail: null }
  }

  // 编辑草稿
  const editDraft = (email: EmailDetail) => {
    composeState.value = { mode: 'draft', originalEmail: email }
  }

  return {
    emails, folders, currentFolderId, selectedEmailId, selectedEmailDetail,
    loading, syncing, currentFilter, composeState, searchQuery, isSearching,
    loadFolders, loadEmails, loadEmailDetail, loadFilteredEmails, loadSnoozedEmails, loadAllEmails,
    sync, formatTime, toggleRead, toggleStar, snooze, removeEmail,
    startReply, startReplyAll, startForward, editDraft, resetCompose, search, clearSearch,
    startAutoSync, stopAutoSync
  }
}