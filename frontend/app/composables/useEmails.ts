interface Email {
  id: number
  subject: string
  sender: string
  snippet: string
  received_at: string
  is_read: boolean
  is_starred: boolean
  has_attachments: boolean
}

interface EmailDetail extends Email {
  recipients: string
  body_html: string | null
  body_text: string | null
}

interface Folder {
  id: number
  name: string
  role: string
  unread_count: number
}

export const useEmails = () => {
  const { getEmails, getEmail, getFolders, syncEmails } = useApi()
  
  const emails = useState<Email[]>('emails', () => [])
  const folders = useState<Folder[]>('folders', () => [])
  const currentFolderId = useState<number | null>('currentFolderId', () => null)
  const selectedEmailId = useState<number | null>('selectedEmailId', () => null)
  const selectedEmailDetail = useState<EmailDetail | null>('selectedEmailDetail', () => null)
  const loading = useState('emailsLoading', () => false)
  const syncing = useState('emailsSyncing', () => false)

  // 加载文件夹列表
  const loadFolders = async () => {
    try {
      const res = await getFolders()
      folders.value = res.data
      // 默认选中收件箱
      const inbox = res.data.find((f: Folder) => f.role === 'inbox')
      if (inbox && !currentFolderId.value) {
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
    } catch (e) {
      console.error('加载邮件详情失败:', e)
    }
  }

  // 同步邮件
  const sync = async () => {
    syncing.value = true
    try {
      const res = await syncEmails()
      if (res.data.new_emails > 0) {
        await loadEmails()
      }
      return res.data.new_emails
    } catch (e) {
      console.error('同步邮件失败:', e)
      return 0
    } finally {
      syncing.value = false
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

  return {
    emails, folders, currentFolderId, selectedEmailId, selectedEmailDetail,
    loading, syncing,
    loadFolders, loadEmails, loadEmailDetail, sync, formatTime
  }
}