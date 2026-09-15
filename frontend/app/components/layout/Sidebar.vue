<script setup lang="ts">
import {
  Mail, Star, Send, File, Trash2, Plus, Box,
  Archive, AlertOctagon, CircleDot,
  ChevronRight, ChevronDown, RotateCw,
  FolderOpen, Tag, Clock, Paperclip, Users, Cloud, CalendarDays, PlusCircle, X, Check, Pencil
} from 'lucide-vue-next'

const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { t } = useI18n()
const { isComposeOpen, requestCloseCompose, requestOpenCompose } = useGlobalModal()
const { folders, currentFolderId, loadEmails, loadFolders, loadFilteredEmails, loadSnoozedEmails, loadAllEmails, currentFilter } = useEmails()
const { token, getTags, createTag, updateTag, deleteTag, getExternalAccounts, createExternalAccount, createFolder, updateFolder, deleteFolder } = useApi()
const { isMobile, closeSidebar } = useResponsive()
const route = useRoute()
const router = useRouter()

const isOpen = reactive({ more: false, tags: true, center: true, tools: true })
const toggle = (key: keyof typeof isOpen) => { isOpen[key] = !isOpen[key] }

// 标签管理
interface TagItem { id: number; name: string; color: string; email_count: number }
const tags = ref<TagItem[]>([])
const showTagModal = ref(false)
const editingTag = ref<TagItem | null>(null)
const tagForm = reactive({ name: '', color: '#3B82F6' })
const tagColors = ['#3B82F6', '#EF4444', '#F59E0B', '#10B981', '#8B5CF6', '#EC4899', '#6B7280']

const loadTags = async () => {
  try { tags.value = await getTags() } catch (e) { console.warn('加载标签失败:', e) }
}

// 外部邮箱账号
const externalAccounts = ref<any[]>([])
const loadExternalAccounts = async () => {
  try { externalAccounts.value = await getExternalAccounts() } catch (e) { console.warn('加载外部邮箱失败:', e) }
}

// 添加外部账号弹窗
const showAddAccountModal = ref(false)
const newAccount = ref<any>({ email: '', password: '', provider: 'gmail', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587 })
const addingAccount = ref(false)
const accountError = ref('')

const isCustomProvider = computed(() => newAccount.value.provider === 'custom')

const handleAddAccount = async () => {
  if (!newAccount.value.email || !newAccount.value.password) return
  if (isCustomProvider.value && (!newAccount.value.imap_host || !newAccount.value.smtp_host)) return
  addingAccount.value = true
  accountError.value = ''
  try {
    const data: any = { email: newAccount.value.email, password: newAccount.value.password, provider: newAccount.value.provider, username: newAccount.value.email }
    if (isCustomProvider.value) {
      data.imap_host = newAccount.value.imap_host
      data.imap_port = newAccount.value.imap_port
      data.smtp_host = newAccount.value.smtp_host
      data.smtp_port = newAccount.value.smtp_port
    }
    const result = await createExternalAccount(data)
    externalAccounts.value.push(result)
    showAddAccountModal.value = false
    newAccount.value = { email: '', password: '', provider: 'gmail', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587 }
  } catch (e: any) {
    accountError.value = e.data?.detail || t('nav.account.addFailed')
  } finally {
    addingAccount.value = false
  }
}

const openTagModal = (tag?: TagItem) => {
  editingTag.value = tag || null
  tagForm.name = tag?.name || ''
  tagForm.color = tag?.color || '#3B82F6'
  showTagModal.value = true
}

const saveTag = async () => {
  if (!tagForm.name.trim()) return
  try {
    if (editingTag.value) {
      await updateTag(editingTag.value.id, { name: tagForm.name, color: tagForm.color })
    } else {
      await createTag(tagForm.name, tagForm.color)
    }
    showTagModal.value = false
    await loadTags()
  } catch (e: any) {
    console.error('保存标签失败', e)
    toast.error(e.data?.detail || t('nav.tags.saveFailed'))
  }
}

const removeTag = async (id: number) => {
  const ok = await confirmDialog({ message: t('nav.tags.deleteConfirm'), type: 'danger' })
  if (!ok) return
  try {
    await deleteTag(id)
    await loadTags()
  } catch (e: any) {
    console.error('删除标签失败', e)
    toast.error(e.data?.detail || t('nav.tags.deleteFailed'))
  }
}

// 文件夹角色 -> 图标映射（名称走 i18n）
const folderConfig: Record<string, { icon: any; iconClass?: string }> = {
  inbox: { icon: Mail },
  sent: { icon: Send },
  drafts: { icon: File },
  trash: { icon: Trash2 },
  spam: { icon: AlertOctagon },
  archive: { icon: Archive },
}

// 获取文件夹显示名称
const getFolderName = (role: string, originalName: string) => {
  const map: Record<string, string> = {
    inbox: t('nav.inbox'),
    sent: t('nav.sent'),
    drafts: t('nav.drafts'),
    trash: t('nav.trash'),
    spam: t('nav.spam'),
    archive: t('nav.archive'),
  }
  return map[role] || originalName
}
const getFolderIcon = (role: string) => folderConfig[role]?.icon || FolderOpen

// 虚拟文件夹（前端特有视图，不对应后端文件夹）
const virtualFolders = computed(() => ({
  starred: { id: 'starred', name: t('nav.starred'), icon: Star, iconClass: 'text-red-500', filter: { is_starred: true } },
  unread: { id: 'unread', name: t('nav.unread'), icon: CircleDot, iconClass: 'text-blue-500', filter: { is_read: false } },
  snoozed: { id: 'snoozed', name: t('nav.snoozed'), icon: Clock, filter: { snoozed: true } },
}))

// 主要文件夹（收件箱、未读、红旗、待办、草稿、已发送）
const mainFolders = computed(() => {
  const result: any[] = []
  // 收件箱
  const inbox = folders.value.find(f => f.role === 'inbox')
  if (inbox) result.push({ ...inbox, name: getFolderName(inbox.role, inbox.name), icon: getFolderIcon(inbox.role) })
  // 未读邮件（虚拟）
  result.push(virtualFolders.value.unread)
  // 红旗邮件（虚拟）
  result.push(virtualFolders.value.starred)
  // 待办邮件（虚拟）
  result.push(virtualFolders.value.snoozed)
  // 草稿箱
  const drafts = folders.value.find(f => f.role === 'drafts')
  if (drafts) result.push({ ...drafts, name: getFolderName(drafts.role, drafts.name), icon: getFolderIcon(drafts.role) })
  // 已发送
  const sent = folders.value.find(f => f.role === 'sent')
  if (sent) result.push({ ...sent, name: getFolderName(sent.role, sent.name), icon: getFolderIcon(sent.role) })
  return result
})

// 更多文件夹
const moreRoles = ['trash', 'spam', 'archive']
const moreFolders = computed(() => [
  ...folders.value.filter(f => moreRoles.includes(f.role)).map(f => ({
    ...f,
    name: getFolderName(f.role, f.name),
    icon: getFolderIcon(f.role)
  })),
  { id: 'all', name: t('nav.allMail'), icon: FolderOpen, virtual: true, unread_count: 0 }
])

// 用户自定义文件夹
const customFolders = computed(() =>
  folders.value.filter(f => f.role === 'user').map(f => ({
    ...f,
    icon: FolderOpen
  }))
)

// 自定义文件夹管理状态
const showCreateFolder = ref(false)
const newFolderName = ref('')
const editingFolderId = ref<number | null>(null)
const editingFolderName = ref('')

const handleCreateFolder = async () => {
  const name = newFolderName.value.trim()
  if (!name) return
  try {
    await createFolder({ name })
    newFolderName.value = ''
    showCreateFolder.value = false
    await loadFolders()
    toast.success(t('nav.folders.created'))
  } catch (e: any) {
    toast.error(e?.data?.detail || t('nav.folders.createFailed'))
  }
}

const startRenameFolder = (folder: any) => {
  editingFolderId.value = folder.id
  editingFolderName.value = folder.name
}

const handleRenameFolder = async () => {
  if (!editingFolderId.value || !editingFolderName.value.trim()) return
  try {
    await updateFolder(editingFolderId.value, { name: editingFolderName.value.trim() })
    editingFolderId.value = null
    editingFolderName.value = ''
    await loadFolders()
    toast.success(t('nav.folders.renamed'))
  } catch (e: any) {
    toast.error(e?.data?.detail || t('nav.folders.renameFailed'))
  }
}

const handleDeleteFolder = async (folder: any) => {
  const ok = await confirmDialog({
    title: t('nav.folders.deleteTitle'),
    message: t('nav.folders.deleteConfirm', { name: folder.name }),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel')
  })
  if (!ok) return
  try {
    await deleteFolder(folder.id)
    await loadFolders()
    toast.success(t('nav.folders.deleted'))
  } catch (e: any) {
    toast.error(e?.data?.detail || t('nav.folders.deleteFailed'))
  }
}

// 当前选中的虚拟文件夹 ID
const selectedVirtualId = useState<string | null>('selectedVirtualId', () => null)
const selectedTagId = useState<number | null>('selectedTagId', () => null)

const openComposePanel = async () => {
  // 如果已有 compose 打开，先走 guard（保存草稿 / 丢弃 / 取消）
  if (isComposeOpen.value) {
    const canOpen = await requestOpenCompose()
    if (!canOpen) return
  }
  selectedTagId.value = null
  selectedVirtualId.value = null
  if (route.path !== '/') {
    await router.push('/')
  }
  isComposeOpen.value = true
  closeSidebar()
}

// 导航到其他页面前检查 compose 状态
const navigateTo = async (path: string) => {
  if (isComposeOpen.value) {
    const canClose = await requestCloseCompose()
    if (!canClose) return
  }
  closeSidebar()
  router.push(path)
}

// 切换文件夹
const selectFolder = async (folder: any) => {
  if (isComposeOpen.value) {
    const canClose = await requestCloseCompose()
    if (!canClose) return
  }

  selectedTagId.value = null // 清除标签选中状态
  
  // 先设置虚拟文件夹状态
  if (folder.id === 'snoozed' || folder.id === 'all' || folder.filter) {
    selectedVirtualId.value = folder.id
  } else {
    selectedVirtualId.value = null
  }
  
  // 如果不在首页，先导航回首页
  if (route.path !== '/') {
    await router.push('/')
    // 等待下一个 tick 确保组件已挂载
    await nextTick()
  }
  
  closeSidebar()

  if (folder.id === 'snoozed') {
    // 待办邮件
    await loadSnoozedEmails()
  } else if (folder.id === 'all') {
    // 所有邮件
    await loadAllEmails()
  } else if (folder.filter) {
    // 其他虚拟文件夹：使用筛选
    await loadFilteredEmails(folder.filter)
  } else {
    // 真实文件夹
    await loadEmails(folder.id)
  }
}

// 切换标签
const { loadEmailsByTag } = useEmails()
const selectTag = async (tag: TagItem) => {
  if (isComposeOpen.value) {
    const canClose = await requestCloseCompose()
    if (!canClose) return
  }

  // 先设置状态，确保 EmailList 不会加载默认邮件
  selectedVirtualId.value = null
  selectedTagId.value = tag.id
  
  // 如果不在首页，先导航回首页
  if (route.path !== '/') {
    await router.push('/')
    // 等待下一个 tick 确保组件已挂载
    await nextTick()
  }
  
  closeSidebar()

  // 加载标签邮件
  await loadEmailsByTag(tag.id)
}

// 判断是否选中
const isSelected = (folder: any) => {
  if (selectedTagId.value) return false
  if (folder.filter || folder.virtual) {
    return selectedVirtualId.value === folder.id
  }
  return currentFolderId.value === folder.id && !selectedVirtualId.value
}

// 初始化加载文件夹
onMounted(async () => {
  if (token.value && folders.value.length === 0) {
    await loadFolders()
  }
  if (token.value) {
    await loadTags()
    await loadExternalAccounts()
  }
})

const tools = computed(() => [
  { name: t('nav.attachmentsCenter'), icon: Paperclip, to: '/attachments' },
  { name: t('nav.contacts'), icon: Users, to: '/contacts' },
  { name: t('drive.title'), icon: Cloud, to: '/drive' },
  { name: t('nav.calendar'), icon: CalendarDays, to: '/calendar' },
])

const isActive = (path: string) => route.path === path
</script>

<template>
  <aside
    role="navigation"
    :aria-label="t('nav.mailNavAria')"
    class="sidebar-glass w-64 h-full border-r border-gray-200/50 dark:border-border-dark/50 flex flex-col shrink-0 transition-colors duration-200 pt-4 font-sans select-none">

    <!-- 写邮件 -->
    <div class="px-3 mb-2">
      <button @click="openComposePanel"
        class="w-full bg-primary hover:bg-primary-hover active:scale-95 text-white py-2.5 rounded-lg flex items-center justify-center gap-2 font-bold shadow-md shadow-purple-500/20 transition-all duration-200 text-sm">
        <Plus class="w-4 h-4" stroke-width="2.5" />
        {{ t('nav.compose') }}
      </button>
    </div>

    <!-- 滚动区域 -->
    <nav class="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar space-y-0.5 mt-1 pb-4">

      <!-- 1. 核心列表 -->
      <div class="space-y-0.5">
        <button v-for="item in mainFolders" :key="item.id" @click="selectFolder(item)"
          class="nav-item group w-full text-left" :class="{ active: isSelected(item) }">
          <component :is="item.icon" class="w-4 h-4 shrink-0 transition-colors"
            :class="[isSelected(item) ? 'text-primary' : '', item.iconClass || 'text-inherit']" />
          <span class="flex-1 truncate">{{ item.name }}</span>
          <span v-if="item.unread_count" class="count-badge" :class="{ 'text-primary font-bold': isSelected(item) }">
            {{ item.unread_count }}
          </span>
        </button>
      </div>

      <!-- 2. 更多 -->
      <div class="mt-1">
        <button @click="toggle('more')" class="nav-item group w-full text-left">
          <component :is="isOpen.more ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">{{ t('nav.more') }}</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.more" class="overflow-hidden space-y-0.5">
            <button v-for="item in moreFolders" :key="item.id" @click="selectFolder(item)"
              class="sub-item group w-full text-left" :class="{ active: isSelected(item) }">
              <component :is="item.icon" class="w-4 h-4 shrink-0 transition-colors text-inherit"
                :class="isSelected(item) ? 'text-primary' : ''" />
              <span class="flex-1 truncate">{{ item.name }}</span>
              <span v-if="item.unread_count" class="text-xs text-gray-400">{{ item.unread_count }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- 2.5 自定义文件夹 -->
      <div v-if="customFolders.length > 0 || showCreateFolder" class="mt-1">
        <div class="flex items-center px-3 py-1">
          <span class="flex-1 text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ t('nav.customFolders') }}</span>
          <button @click="showCreateFolder = !showCreateFolder" class="text-gray-400 hover:text-primary transition-colors" :title="t('nav.newFolder')">
            <Plus class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 新建输入框 -->
        <div v-if="showCreateFolder" class="flex items-center gap-1 px-3 py-1">
          <input
            v-model="newFolderName"
            @keydown.enter="handleCreateFolder"
            @keydown.escape="showCreateFolder = false"
            :placeholder="t('nav.folderNamePlaceholder')"
            class="flex-1 text-sm bg-transparent border border-gray-300 dark:border-border-dark rounded px-2 py-1 focus:outline-none focus:border-primary"
            autofocus
          />
          <button @click="handleCreateFolder" class="text-green-500 hover:text-green-400"><Check class="w-4 h-4" /></button>
          <button @click="showCreateFolder = false" class="text-gray-400 hover:text-gray-300"><X class="w-4 h-4" /></button>
        </div>

        <!-- 自定义文件夹列表 -->
        <div class="space-y-0.5">
          <div v-for="folder in customFolders" :key="folder.id" class="group relative">
            <!-- 重命名模式 -->
            <div v-if="editingFolderId === folder.id" class="flex items-center gap-1 px-3 py-1">
              <input
                v-model="editingFolderName"
                @keydown.enter="handleRenameFolder"
                @keydown.escape="editingFolderId = null"
                class="flex-1 text-sm bg-transparent border border-gray-300 dark:border-border-dark rounded px-2 py-1 focus:outline-none focus:border-primary"
                autofocus
              />
              <button @click="handleRenameFolder" class="text-green-500 hover:text-green-400"><Check class="w-4 h-4" /></button>
              <button @click="editingFolderId = null" class="text-gray-400 hover:text-gray-300"><X class="w-4 h-4" /></button>
            </div>
            <!-- 正常模式 -->
            <button v-else @click="selectFolder(folder)" class="sub-item group w-full text-left" :class="{ active: isSelected(folder) }">
              <FolderOpen class="w-4 h-4 shrink-0 transition-colors text-inherit" :class="isSelected(folder) ? 'text-primary' : ''" />
              <span class="flex-1 truncate">{{ folder.name }}</span>
              <span v-if="folder.unread_count" class="text-xs text-gray-400">{{ folder.unread_count }}</span>
              <!-- 操作按钮 -->
              <span class="hidden group-hover:flex items-center gap-0.5 shrink-0">
                <button @click.stop="startRenameFolder(folder)" class="text-gray-400 hover:text-primary" :title="t('nav.rename')"><Pencil class="w-3 h-3" /></button>
                <button @click.stop="handleDeleteFolder(folder)" class="text-gray-400 hover:text-red-500" :title="t('common.delete')"><Trash2 class="w-3 h-3" /></button>
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- 新建文件夹入口（当没有自定义文件夹时也显示） -->
      <div v-if="customFolders.length === 0 && !showCreateFolder" class="mt-1 px-3">
        <button @click="showCreateFolder = true" class="text-xs text-gray-400 dark:text-gray-500 hover:text-primary transition-colors flex items-center gap-1">
          <PlusCircle class="w-3.5 h-3.5" />
          <span>{{ t('nav.newFolder') }}</span>
        </button>
      </div>

      <!-- 3. 邮件标签 -->
      <div class="mt-1">
        <button @click="toggle('tags')" class="nav-item group w-full text-left">
          <component :is="isOpen.tags ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">{{ t('nav.mailTags') }}</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.tags" class="overflow-hidden space-y-0.5">
            <button v-for="tag in tags" :key="tag.id"
              @click="selectTag(tag)"
              @contextmenu.prevent="openTagModal(tag)"
              class="sub-item group w-full text-left"
              :class="{ active: selectedTagId === tag.id }">
              <div class="w-3 h-3 rounded-sm shrink-0" :style="{ backgroundColor: tag.color }"></div>
              <span class="flex-1 truncate">{{ tag.name }}</span>
              <span class="text-xs text-gray-400">{{ tag.email_count }}</span>
              
              <!-- 悬停显示编辑按钮 -->
              <div class="opacity-0 group-hover:opacity-100 absolute right-2 bg-gray-100 dark:bg-gray-800 rounded p-0.5" @click.stop="openTagModal(tag)">
                <Pencil class="w-3 h-3 text-gray-500" />
              </div>
            </button>
            <button @click="openTagModal()" class="sub-item text-gray-500 hover:text-primary">
              <PlusCircle class="w-4 h-4 shrink-0" />
              <span class="truncate">{{ t('nav.tags.add') }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- 4. 邮箱中心 -->
      <div class="mt-1">
        <button @click="toggle('center')" class="nav-item group w-full text-left">
          <component :is="isOpen.center ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">{{ t('nav.mailCenter') }}</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.center" class="overflow-hidden pt-1 space-y-0.5">
            <div v-for="account in externalAccounts" :key="account.id"
              class="ml-9 mr-2 bg-blue-50/60 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-lg p-2.5 mb-1 group cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 transition-colors min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] text-gray-500 font-medium">{{ account.is_active ? t('nav.accountSyncing') : t('nav.accountDisabled') }}</span>
                <RotateCw v-if="account.is_active" class="w-3 h-3 text-blue-500 animate-spin-slow shrink-0" />
              </div>
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full shrink-0" :class="account.is_active ? 'bg-green-500' : 'bg-gray-400'"></div>
                <div class="text-xs font-bold text-gray-700 dark:text-gray-200 truncate" :title="account.email">
                  {{ account.email.length > 15 ? account.email.slice(0, 12) + '...' : account.email }}
                </div>
              </div>
            </div>

            <button @click="showAddAccountModal = true" class="sub-item text-gray-500 hover:text-primary">
              <PlusCircle class="w-4 h-4 shrink-0" />
              <span class="truncate">{{ t('nav.addExternalEmail') }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- 5. 其他工具 -->
      <div class="mt-1">
        <button @click="toggle('tools')" class="nav-item group w-full text-left">
          <component :is="isOpen.tools ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">{{ t('nav.otherTools') }}</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.tools" class="overflow-hidden space-y-0.5">
            <a v-for="item in tools" :key="item.name" @click="navigateTo(item.to)"
              class="sub-item group cursor-pointer" :class="{ active: isActive(item.to) }">
              <component :is="item.icon" class="w-4 h-4 shrink-0 transition-colors text-inherit"
                :class="isActive(item.to) ? 'text-primary' : ''" />
              <span class="flex-1 truncate">{{ item.name }}</span>
            </a>
          </div>
        </Transition>
      </div>

    </nav>

    <!-- 底部账号池 -->
    <div class="p-3 mt-auto border-t border-gray-200 dark:border-gray-800">
      <a @click="navigateTo('/pool')"
        class="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg hover:bg-white dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 transition-all shadow-sm hover:shadow border border-gray-200/50 hover:border-gray-200 dark:border-gray-800 dark:hover:border-gray-700 group bg-white dark:bg-gray-900 cursor-pointer">
        <div class="p-1 bg-primary/10 rounded-md shrink-0">
          <Box class="w-4 h-4 text-primary group-hover:scale-105 transition-transform" />
        </div>
        <span class="font-bold text-sm truncate">{{ t('nav.pool') }}</span>
      </a>
    </div>
  </aside>

  <!-- 标签编辑弹窗 -->
  <CommonModal v-model="showTagModal" :title="editingTag ? t('nav.tags.edit') : t('nav.tags.create')" width-class="max-w-sm">
    <input v-model="tagForm.name" :placeholder="t('nav.tags.namePlaceholder')" class="w-full px-3 py-2 border rounded-lg mb-3 dark:bg-gray-700 dark:border-gray-600" />
    <div class="flex gap-2 mb-2">
      <button v-for="c in tagColors" :key="c" @click="tagForm.color = c" class="w-6 h-6 rounded-full" :style="{ backgroundColor: c }" :class="tagForm.color === c ? 'ring-2 ring-offset-2 ring-primary' : ''"></button>
    </div>
    <template #footer>
      <button v-if="editingTag" @click="removeTag(editingTag.id)" class="px-3 py-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-sm">{{ t('common.delete') }}</button>
      <div class="flex-1"></div>
      <button @click="showTagModal = false" class="px-3 py-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm">{{ t('common.cancel') }}</button>
      <button @click="saveTag" class="px-3 py-1.5 bg-primary text-white rounded-lg text-sm">{{ t('common.save') }}</button>
    </template>
  </CommonModal>

  <!-- 添加外部账号弹窗 -->
  <CommonModal v-model="showAddAccountModal" :title="t('nav.account.title')">
    <div class="space-y-3 max-h-80 overflow-y-auto">
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ t('nav.account.provider') }}</label>
        <select v-model="newAccount.provider" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm">
          <optgroup :label="t('nav.account.international')">
            <option value="gmail">Gmail</option>
            <option value="outlook">Outlook / Hotmail</option>
            <option value="icloud">iCloud</option>
            <option value="yahoo">Yahoo Mail</option>
            <option value="zoho">Zoho Mail</option>
          </optgroup>
          <optgroup :label="t('nav.account.domestic')">
            <option value="qq">{{ t('nav.account.qq') }}</option>
            <option value="163">{{ t('nav.account.n163') }}</option>
            <option value="126">{{ t('nav.account.n126') }}</option>
            <option value="yeah">{{ t('nav.account.yeah') }}</option>
            <option value="sina">{{ t('nav.account.sina') }}</option>
            <option value="aliyun">{{ t('nav.account.aliyun') }}</option>
          </optgroup>
          <optgroup :label="t('nav.account.other')">
            <option value="custom">{{ t('nav.account.custom') }}</option>
          </optgroup>
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ t('nav.account.emailLabel') }}</label>
        <input v-model="newAccount.email" type="email" placeholder="your@email.com" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ t('nav.account.passwordLabel') }}</label>
        <input v-model="newAccount.password" type="password" :placeholder="t('nav.account.passwordPlaceholder')" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
        <p class="text-[10px] text-gray-400 mt-1">{{ t('nav.account.passwordHint') }}</p>
      </div>
      <!-- 自定义服务器配置 -->
      <template v-if="isCustomProvider">
        <div class="border-t pt-3 mt-2">
          <p class="text-xs text-gray-500 mb-2 font-medium">{{ t('nav.account.imapLabel') }}</p>
          <div class="flex gap-2">
            <input v-model="newAccount.imap_host" type="text" placeholder="imap.example.com" class="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
            <input v-model.number="newAccount.imap_port" type="number" placeholder="993" class="w-20 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
          </div>
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-2 font-medium">{{ t('nav.account.smtpLabel') }}</p>
          <div class="flex gap-2">
            <input v-model="newAccount.smtp_host" type="text" placeholder="smtp.example.com" class="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
            <input v-model.number="newAccount.smtp_port" type="number" placeholder="587" class="w-20 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
          </div>
        </div>
      </template>
      <div v-if="accountError" class="text-red-500 text-xs">{{ accountError }}</div>
    </div>
    <template #footer>
      <div class="flex-1"></div>
      <button @click="showAddAccountModal = false" class="px-3 py-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm">{{ t('common.cancel') }}</button>
      <button @click="handleAddAccount" :disabled="addingAccount || !newAccount.email || !newAccount.password || (isCustomProvider && (!newAccount.imap_host || !newAccount.smtp_host))" class="px-3 py-1.5 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
        {{ addingAccount ? t('nav.account.adding') : t('nav.account.add') }}
      </button>
    </template>
  </CommonModal>
</template>

<style scoped>
/* 核心样式：确保 nav-item 和 sub-item 结构稳定 */
.nav-item {
  @apply flex items-center gap-3 px-3 py-2 mx-2 rounded-md text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800 transition-colors cursor-pointer select-none font-medium;
}

.nav-item.active {
  @apply text-primary dark:text-primary font-bold shadow-sm;
}

.sub-item {
  @apply flex items-center gap-3 px-3 py-1.5 pl-9 mx-2 rounded-md text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800 transition-colors cursor-pointer select-none;
}

.sub-item.active {
  @apply text-primary dark:text-primary font-bold;
}

.count-badge {
  @apply text-xs text-gray-400 font-medium shrink-0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease-in-out;
  max-height: 500px;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.animate-spin-slow {
  animation: spin 3s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 0px;
  height: 0px;
}

.custom-scrollbar {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
</style>
