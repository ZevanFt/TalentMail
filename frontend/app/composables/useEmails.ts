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

interface AttachmentInfo {
  id: number
  filename: string
  content_type: string
  size: number
}

interface TagInfo {
  id: number
  name: string
  color: string
}

interface EmailDetail extends Email {
  recipients: string
  body_html: string | null
  body_text: string | null
  is_tracked?: boolean
  delivery_status?: string
  delivery_error?: string
  attachments?: AttachmentInfo[]
  tags?: TagInfo[]
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
  const { getEmails, getEmail, getFolders, syncEmails, markEmailRead, deleteEmail, markEmailStarred, snoozeEmail, getAllEmails, getSnoozedEmails, searchEmails, getEmailsByTag, getTags, addTagToEmail, removeTagFromEmail } = useApi()
  const toast = useToast()

  const emails = useState<Email[]>('emails', () => [])
  const tags = useState<any[]>('tags', () => [])
  // 使用默认文件夹初始化，后端返回后会更新 id 和 unread_count
  const folders = useState<Folder[]>('folders', () => [...DEFAULT_FOLDERS])
  const currentFolderId = useState<number | null>('currentFolderId', () => null)
  const selectedEmailId = useState<number | null>('selectedEmailId', () => null)
  const selectedEmailDetail = useState<EmailDetail | null>('selectedEmailDetail', () => null)
  const loading = useState('emailsLoading', () => false)
  const syncing = useState('emailsSyncing', () => false)

  // 分页状态
  const PAGE_SIZE = 50
  const emailPage = useState('emailPage', () => 1)
  const emailTotal = useState('emailTotal', () => 0)
  const loadingMore = useState('loadingMore', () => false)
  const emailHasMore = computed(() => emailPage.value * PAGE_SIZE < emailTotal.value)

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
    } catch (e: any) {
      console.error('加载文件夹失败:', e)
      toast.error(e.data?.detail || '加载文件夹失败')
    }
  }

  // 加载标签列表
  const loadTags = async () => {
    try {
      const res = await getTags()
      tags.value = res
    } catch (e: any) {
      console.error('加载标签失败:', e)
      toast.error(e.data?.detail || '加载标签失败')
    }
  }

  // 加载邮件列表
  const loadEmails = async (folderId?: number) => {
    const id = folderId || currentFolderId.value
    if (!id) return

    // 切换文件夹时清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    emailPage.value = 1

    loading.value = true
    try {
      const res = await getEmails(id, 1, PAGE_SIZE)
      emails.value = res.data.items
      emailTotal.value = res.data.total
      currentFolderId.value = id
    } catch (e: any) {
      console.error('加载邮件失败:', e)
      toast.error(e.data?.detail || '加载邮件失败')
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
    } catch (e: any) {
      console.error('加载邮件详情失败:', e)
      toast.error(e.data?.detail || '加载邮件详情失败')
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
    } catch (e: any) {
      console.error('标记已读失败:', e)
      toast.error(e.data?.detail || '标记已读失败')
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
    } catch (e: any) {
      console.error('标记星标失败:', e)
      toast.error(e.data?.detail || '标记星标失败')
    }
  }

  // 设置待办
  const snooze = async (id: number, snoozeUntil: string) => {
    try {
      await snoozeEmail(id, snoozeUntil)
      // 从当前列表移除（因为已设为待办）
      emails.value = emails.value.filter(e => e.id !== id)
    } catch (e: any) {
      console.error('设置待办失败:', e)
      toast.error(e.data?.detail || '设置待办失败')
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
    } catch (e: any) {
      console.error('删除邮件失败:', e)
      toast.error(e.data?.detail || '删除邮件失败')
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
    } catch (e: any) {
      console.error('同步邮件失败:', e)
      toast.error(e.data?.detail || '同步邮件失败')
      return 0
    } finally {
      syncing.value = false
    }
  }

  // WebSocket 实时通知
  const ws = useState<WebSocket | null>('emailWs', () => null)
  let wsRetryCount = 0
  let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
  let wsIntentionalClose = false

  const connectWebSocket = () => {
    const { token } = useApi()
    if (!token.value || ws.value) return

    wsIntentionalClose = false
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/${token.value}`

    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      wsRetryCount = 0 // 连接成功，重置重试计数
    }

    ws.value.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'new_email') {
          await loadEmails()
          await loadFolders()
        }
      } catch (e) {
        console.warn('WebSocket 消息解析失败:', e)
      }
    }

    ws.value.onclose = () => {
      ws.value = null
      if (wsIntentionalClose) return
      // 指数退避重连，最多 10 次，最大间隔 30 秒
      if (wsRetryCount < 10) {
        const delay = Math.min(3000 * Math.pow(2, wsRetryCount), 30000)
        wsReconnectTimer = setTimeout(connectWebSocket, delay)
        wsRetryCount++
      }
    }

    ws.value.onerror = () => {
      ws.value?.close()
    }
  }

  const disconnectWebSocket = () => {
    wsIntentionalClose = true
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer)
      wsReconnectTimer = null
    }
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
    emailPage.value = 1

    loading.value = true
    currentFilter.value = filter
    try {
      // 使用所有邮件 API 进行筛选
      const isRead = 'is_read' in filter ? filter.is_read : undefined
      const isStarred = 'is_starred' in filter ? filter.is_starred : undefined
      // 未读邮件只查询收件箱
      const inboxOnly = isRead === false
      const res = await getAllEmails(1, PAGE_SIZE, isRead, isStarred, inboxOnly)
      emails.value = res.data.items
      emailTotal.value = res.data.total
    } catch (e: any) {
      console.error('加载筛选邮件失败:', e)
      toast.error(e.data?.detail || '加载邮件失败')
    } finally {
      loading.value = false
    }
  }

  // 加载待办邮件
  const loadSnoozedEmails = async () => {
    // 清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    emailPage.value = 1

    loading.value = true
    try {
      const res = await getSnoozedEmails(1, PAGE_SIZE)
      emails.value = res.data.items
      emailTotal.value = res.data.total
    } catch (e: any) {
      console.error('加载待办邮件失败:', e)
      toast.error(e.data?.detail || '加载待办邮件失败')
    } finally {
      loading.value = false
    }
  }

  // 加载所有邮件
  const loadAllEmails = async () => {
    // 清空选中的邮件
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    emailPage.value = 1

    loading.value = true
    try {
      const res = await getAllEmails(1, PAGE_SIZE)
      emails.value = res.data.items
      emailTotal.value = res.data.total
    } catch (e: any) {
      console.error('加载所有邮件失败:', e)
      toast.error(e.data?.detail || '加载邮件失败')
    } finally {
      loading.value = false
    }
  }

  // 当前选中的标签名称
  const currentTagName = useState<string | null>('currentTagName', () => null)

  // 加载标签下的邮件
  const loadEmailsByTag = async (tagId: number) => {
    selectedEmailId.value = null
    selectedEmailDetail.value = null
    emailPage.value = 1
    loading.value = true
    // 设置当前标签名称
    const tag = tags.value.find(t => t.id === tagId)
    currentTagName.value = tag?.name || null
    try {
      const res = await getEmailsByTag(tagId, 1, PAGE_SIZE)
      emails.value = res.items
      emailTotal.value = res.total
    } catch (e: any) {
      console.error('加载标签邮件失败:', e)
      toast.error(e.data?.detail || '加载邮件失败')
    } finally {
      loading.value = false
    }
  }

  // 给邮件添加标签
  const addTag = async (emailId: number, tagId: number) => {
    try {
      await addTagToEmail(emailId, tagId)
      // 更新当前选中邮件的详情
      if (selectedEmailDetail.value?.id === emailId) {
        const tag = tags.value.find(t => t.id === tagId)
        if (tag) {
          if (!selectedEmailDetail.value.tags) {
            selectedEmailDetail.value.tags = []
          }
          // 避免重复添加
          if (!selectedEmailDetail.value.tags.some((t: any) => t.id === tagId)) {
            selectedEmailDetail.value.tags.push(tag)
          }
        }
      }
    } catch (e: any) {
      console.error('添加标签失败:', e)
      toast.error(e.data?.detail || '添加标签失败')
    }
  }

  // 移除邮件标签
  const removeTag = async (emailId: number, tagId: number) => {
    try {
      await removeTagFromEmail(emailId, tagId)
      // 更新当前选中邮件的详情
      if (selectedEmailDetail.value?.id === emailId && selectedEmailDetail.value.tags) {
        selectedEmailDetail.value.tags = selectedEmailDetail.value.tags.filter((t: any) => t.id !== tagId)
      }
    } catch (e: any) {
      console.error('移除标签失败:', e)
      toast.error(e.data?.detail || '移除标签失败')
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
    emailPage.value = 1
    try {
      const res = await searchEmails(query, 1, PAGE_SIZE)
      emails.value = res.data.items
      emailTotal.value = res.data.total
    } catch (e: any) {
      console.error('搜索邮件失败:', e)
      toast.error(e.data?.detail || '搜索邮件失败')
    } finally {
      loading.value = false
    }
  }

  // 加载更多邮件（追加分页）
  const selectedVirtualId = useState<string | null>('selectedVirtualId', () => null)
  const selectedTagId = useState<number | null>('selectedTagId', () => null)

  const loadMoreEmails = async () => {
    if (!emailHasMore.value || loadingMore.value) return

    loadingMore.value = true
    const nextPage = emailPage.value + 1
    try {
      let newItems: Email[] = []

      if (isSearching.value && searchQuery.value) {
        // 搜索模式
        const res = await searchEmails(searchQuery.value, nextPage, PAGE_SIZE)
        newItems = res.data.items
        emailTotal.value = res.data.total
      } else if (selectedTagId.value) {
        // 标签模式
        const res = await getEmailsByTag(selectedTagId.value, nextPage, PAGE_SIZE)
        newItems = res.items
        emailTotal.value = res.total
      } else if (selectedVirtualId.value === 'snoozed') {
        const res = await getSnoozedEmails(nextPage, PAGE_SIZE)
        newItems = res.data.items
        emailTotal.value = res.data.total
      } else if (selectedVirtualId.value === 'all') {
        const res = await getAllEmails(nextPage, PAGE_SIZE)
        newItems = res.data.items
        emailTotal.value = res.data.total
      } else if (currentFilter.value) {
        // 虚拟文件夹（未读/星标等）
        const isRead = 'is_read' in currentFilter.value ? currentFilter.value.is_read : undefined
        const isStarred = 'is_starred' in currentFilter.value ? currentFilter.value.is_starred : undefined
        const inboxOnly = isRead === false
        const res = await getAllEmails(nextPage, PAGE_SIZE, isRead, isStarred, inboxOnly)
        newItems = res.data.items
        emailTotal.value = res.data.total
      } else if (currentFolderId.value) {
        // 普通文件夹
        const res = await getEmails(currentFolderId.value, nextPage, PAGE_SIZE)
        newItems = res.data.items
        emailTotal.value = res.data.total
      }

      if (newItems.length > 0) {
        emails.value = [...emails.value, ...newItems]
        emailPage.value = nextPage
      }
    } catch (e: any) {
      console.error('加载更多邮件失败:', e)
      toast.error(e.data?.detail || '加载更多邮件失败')
    } finally {
      loadingMore.value = false
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
    emails, folders, tags, currentFolderId, selectedEmailId, selectedEmailDetail,
    loading, syncing, currentFilter, composeState, searchQuery, isSearching, currentTagName,
    emailHasMore, loadingMore, emailTotal,
    loadFolders, loadTags, loadEmails, loadEmailDetail, loadFilteredEmails, loadSnoozedEmails, loadAllEmails, loadEmailsByTag,
    loadMoreEmails,
    sync, formatTime, toggleRead, toggleStar, snooze, removeEmail, addTag, removeTag,
    startReply, startReplyAll, startForward, editDraft, resetCompose, search, clearSearch,
    startAutoSync, stopAutoSync
  }
}