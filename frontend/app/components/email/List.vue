<script setup lang="ts">
import { Star, RefreshCw, Loader2, Circle, Clock, X, Send, CheckCircle, XCircle, Eye, Paperclip, SquareCheck, Square, Trash2, Archive, FolderInput, CheckCheck, CircleDot, MoreHorizontal } from 'lucide-vue-next'

const { emails, selectedEmailId, folders, currentFolderId, loading, syncing, loadFolders, loadEmails, loadEmailDetail, sync, formatTime, toggleRead, toggleStar, snooze, searchQuery, isSearching, clearSearch, startAutoSync, stopAutoSync, editDraft } = useEmails()
const { isComposeOpen } = useGlobalModal()
const { getEmail, bulkMarkRead, bulkMarkStarred, bulkDeleteEmails, bulkArchiveEmails, bulkMoveEmails, markAsSpam, markAsNotSpam } = useApi()

// 获取 Sidebar 中选中的虚拟文件夹 ID 和标签 ID
const selectedVirtualId = useState<string | null>('selectedVirtualId', () => null)
const selectedTagId = useState<number | null>('selectedTagId', () => null)

// ========== 批量选择功能 ==========
const isSelectionMode = ref(false)
const selectedEmailIds = ref<Set<number>>(new Set())

// 切换选择模式
const toggleSelectionMode = () => {
  isSelectionMode.value = !isSelectionMode.value
  if (!isSelectionMode.value) {
    selectedEmailIds.value.clear()
  }
}

// 切换单个邮件选择
const toggleEmailSelection = (id: number, event: Event) => {
  event.stopPropagation()
  if (selectedEmailIds.value.has(id)) {
    selectedEmailIds.value.delete(id)
  } else {
    selectedEmailIds.value.add(id)
  }
  // 触发响应式更新
  selectedEmailIds.value = new Set(selectedEmailIds.value)
}

// 全选/取消全选
const isAllSelected = computed(() =>
  emails.value.length > 0 && selectedEmailIds.value.size === emails.value.length
)
const isSomeSelected = computed(() =>
  selectedEmailIds.value.size > 0 && selectedEmailIds.value.size < emails.value.length
)
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedEmailIds.value.clear()
  } else {
    selectedEmailIds.value = new Set(emails.value.map((e: any) => e.id))
  }
}

// 批量操作 loading
const bulkLoading = ref(false)

// 批量标记已读
const handleBulkMarkRead = async (isRead: boolean) => {
  if (selectedEmailIds.value.size === 0) return
  bulkLoading.value = true
  try {
    await bulkMarkRead(Array.from(selectedEmailIds.value), isRead)
    await loadEmails()
    selectedEmailIds.value.clear()
    isSelectionMode.value = false
  } catch (e) {
    console.error('批量标记失败', e)
  } finally {
    bulkLoading.value = false
  }
}

// 批量删除
const handleBulkDelete = async () => {
  if (selectedEmailIds.value.size === 0) return
  bulkLoading.value = true
  try {
    await bulkDeleteEmails(Array.from(selectedEmailIds.value))
    await loadEmails()
    selectedEmailIds.value.clear()
    isSelectionMode.value = false
  } catch (e) {
    console.error('批量删除失败', e)
  } finally {
    bulkLoading.value = false
  }
}

// 批量归档
const handleBulkArchive = async () => {
  if (selectedEmailIds.value.size === 0) return
  bulkLoading.value = true
  try {
    await bulkArchiveEmails(Array.from(selectedEmailIds.value))
    await loadEmails()
    selectedEmailIds.value.clear()
    isSelectionMode.value = false
  } catch (e) {
    console.error('批量归档失败', e)
  } finally {
    bulkLoading.value = false
  }
}

// 批量标记为垃圾邮件
const handleBulkMarkSpam = async () => {
  if (selectedEmailIds.value.size === 0) return
  bulkLoading.value = true
  try {
    await markAsSpam(Array.from(selectedEmailIds.value))
    await loadEmails()
    selectedEmailIds.value.clear()
    isSelectionMode.value = false
  } catch (e) {
    console.error('批量标记垃圾邮件失败', e)
  } finally {
    bulkLoading.value = false
  }
}

// 批量标记为非垃圾邮件
const handleBulkMarkNotSpam = async () => {
  if (selectedEmailIds.value.size === 0) return
  bulkLoading.value = true
  try {
    await markAsNotSpam(Array.from(selectedEmailIds.value))
    await loadEmails()
    selectedEmailIds.value.clear()
    isSelectionMode.value = false
  } catch (e) {
    console.error('批量标记非垃圾邮件失败', e)
  } finally {
    bulkLoading.value = false
  }
}

// 批量操作菜单
const showBulkMenu = ref(false)

// ========== 原有功能 ==========

// 待办对话框
const showSnoozeModal = ref(false)
const snoozeEmailId = ref<number | null>(null)

const openSnoozeModal = (id: number) => {
  snoozeEmailId.value = id
  showSnoozeModal.value = true
}

// 快捷时间选项
const getSnoozeTime = (option: string) => {
  const now = new Date()
  switch (option) {
    case 'later': // 今天晚些时候（3小时后）
      return new Date(now.getTime() + 3 * 60 * 60 * 1000)
    case 'tomorrow': // 明天早上9点
      const tomorrow = new Date(now)
      tomorrow.setDate(tomorrow.getDate() + 1)
      tomorrow.setHours(9, 0, 0, 0)
      return tomorrow
    case 'nextWeek': // 下周一早上9点
      const nextMonday = new Date(now)
      nextMonday.setDate(nextMonday.getDate() + ((8 - nextMonday.getDay()) % 7 || 7))
      nextMonday.setHours(9, 0, 0, 0)
      return nextMonday
    default:
      return now
  }
}

// 自定义时间
const customDateTime = ref<Date | null>(null)
const showCustomPicker = ref(false)

const handleSnooze = async (option: string) => {
  if (snoozeEmailId.value) {
    const time = getSnoozeTime(option)
    await snooze(snoozeEmailId.value, time.toISOString())
    showSnoozeModal.value = false
  }
}

const handleCustomSnooze = async () => {
  if (snoozeEmailId.value && customDateTime.value) {
    await snooze(snoozeEmailId.value, customDateTime.value.toISOString())
    showSnoozeModal.value = false
    customDateTime.value = null
    showCustomPicker.value = false
  }
}

// 文件夹角色 -> 中文名称映射
const folderNames: Record<string, string> = {
  inbox: '收件箱', sent: '已发送', drafts: '草稿箱',
  trash: '已删除', spam: '垃圾邮件', archive: '归档'
}

// 虚拟文件夹名称映射
const virtualFolderNames: Record<string, string> = {
  starred: '红旗邮件',
  unread: '未读邮件',
  snoozed: '待办邮件',
  all: '所有邮件'
}

// 当前文件夹名称
const { currentTagName } = useEmails()
const currentFolderName = computed(() => {
  if (isSearching.value) return `搜索: ${searchQuery.value}`
  // 标签
  if (selectedTagId.value && currentTagName.value) {
    return `标签: ${currentTagName.value}`
  }
  // 虚拟文件夹
  if (selectedVirtualId.value) {
    return virtualFolderNames[selectedVirtualId.value] || selectedVirtualId.value
  }
  // 真实文件夹
  const folder = folders.value.find(f => f.id === currentFolderId.value)
  return folder ? (folderNames[folder.role] || folder.name) : '收件箱'
})

// 是否是已发送文件夹
const isSentFolder = computed(() => {
  const folder = folders.value.find(f => f.id === currentFolderId.value)
  return folder?.role === 'sent'
})

// 是否是草稿箱
const isDraftsFolder = computed(() => {
  const folder = folders.value.find(f => f.id === currentFolderId.value)
  return folder?.role === 'drafts'
})

// 是否是垃圾邮件文件夹
const isSpamFolder = computed(() => {
  const folder = folders.value.find(f => f.id === currentFolderId.value)
  return folder?.role === 'spam'
})

// 获取发件人首字母
const getAvatar = (sender: string) => {
  if (!sender) return '?'
  const match = sender.match(/^([^<]+)/) || sender.match(/<([^>]+)>/)
  const name = match?.[1]?.trim() || sender
  return name.charAt(0).toUpperCase()
}

// 选择邮件
const selectEmail = async (id: number) => {
  // 草稿箱：打开编辑弹窗
  if (isDraftsFolder.value) {
    const res = await getEmail(id)
    editDraft(res.data)
    isComposeOpen.value = true
    return
  }
  selectedEmailId.value = id
  loadEmailDetail(id)
}

// 初始化加载（只在有 token 时）
const { token } = useApi()
onMounted(async () => {
  if (token.value) {
    await loadFolders()
    // 如果已经有选中的标签或虚拟文件夹，说明是从其他页面导航过来的
    // 这种情况下不要加载默认邮件，避免覆盖标签/虚拟文件夹的邮件列表
    if (!selectedTagId.value && !selectedVirtualId.value) {
      await loadEmails()
    }
    // 启动实时同步（WebSocket + 备用轮询）
    startAutoSync()
  }
})

onUnmounted(() => {
  stopAutoSync()
})
</script>

<template>
  <div class="w-80 h-full email-list-container border-r border-gray-200/50 dark:border-border-dark/50 flex flex-col shrink-0">
    <!-- 标题栏 -->
    <div class="px-4 py-3.5 text-xs font-bold text-gray-600 dark:text-gray-400 border-b border-gray-200/50 dark:border-gray-800/50 flex items-center justify-between">
      <span class="truncate flex-1 tracking-wide">{{ currentFolderName }} <span class="text-gray-400 font-normal">({{ emails.length }})</span></span>
      <div class="flex items-center gap-1 shrink-0">
        <button v-if="isSearching" @click="clearSearch"
          class="p-1.5 hover:bg-primary/10 dark:hover:bg-primary/20 rounded-md text-primary transition-all duration-200 hover:scale-105"
          title="清除搜索">
          <X class="w-4 h-4" />
        </button>
        <!-- 批量选择按钮 - 改进交互 -->
        <button @click="toggleSelectionMode"
          class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-all duration-200 hover:scale-105"
          :class="{ 'bg-primary/10 dark:bg-primary/20 text-primary ring-1 ring-primary/30': isSelectionMode }"
          :title="isSelectionMode ? '退出选择' : '批量选择'">
          <SquareCheck class="w-4 h-4" />
        </button>
        <button @click="sync" :disabled="syncing"
          class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105">
          <Loader2 v-if="syncing" class="w-4 h-4 animate-spin text-primary" />
          <RefreshCw v-else class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 批量操作工具栏 - 防止跳动，进入选择模式即显示 -->
    <div class="bulk-toolbar-container px-3 border-b border-gray-200/50 dark:border-gray-700/50 transition-all duration-300"
      :class="isSelectionMode ? 'py-2.5 bg-gradient-to-r from-primary/5 to-primary/10 dark:from-primary/10 dark:to-primary/20' : 'py-0 h-0 overflow-hidden'">
      <div v-if="isSelectionMode" class="flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
        <!-- 全选 - 改进样式 -->
        <button @click="toggleSelectAll"
          class="p-1.5 hover:bg-white dark:hover:bg-gray-700 rounded-md transition-all duration-200 hover:scale-105"
          :title="isAllSelected ? '取消全选' : '全选'">
          <SquareCheck v-if="isAllSelected" class="w-4 h-4 text-primary" />
          <Square v-else class="w-4 h-4 text-gray-500 hover:text-primary" />
        </button>
        <span class="text-xs font-medium text-primary dark:text-primary-light">已选 {{ selectedEmailIds.size }} 封</span>
        <div class="flex-1"></div>
        <!-- 批量操作按钮 - 改进样式 -->
        <button @click="handleBulkMarkRead(true)" :disabled="bulkLoading"
          class="p-1.5 hover:bg-white dark:hover:bg-gray-700 rounded-md transition-all duration-200 hover:scale-105 disabled:opacity-50"
          title="标记已读">
          <CheckCheck class="w-4 h-4 text-gray-600 dark:text-gray-400 hover:text-green-500" />
        </button>
        <button @click="handleBulkArchive" :disabled="bulkLoading"
          class="p-1.5 hover:bg-white dark:hover:bg-gray-700 rounded-md transition-all duration-200 hover:scale-105 disabled:opacity-50"
          title="归档">
          <Archive class="w-4 h-4 text-gray-600 dark:text-gray-400 hover:text-blue-500" />
        </button>
        <button @click="handleBulkDelete" :disabled="bulkLoading"
          class="p-1.5 hover:bg-white dark:hover:bg-gray-700 rounded-md transition-all duration-200 hover:scale-105 disabled:opacity-50"
          title="删除">
          <Trash2 class="w-4 h-4 text-red-500 hover:text-red-600" />
        </button>
        <!-- 更多操作下拉 - 改进样式 -->
        <div class="relative">
          <button @click="showBulkMenu = !showBulkMenu"
            class="p-1.5 hover:bg-white dark:hover:bg-gray-700 rounded-md transition-all duration-200 hover:scale-105"
            title="更多操作">
            <MoreHorizontal class="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          <!-- 下拉菜单 - 改进样式 -->
          <div v-if="showBulkMenu"
            class="absolute right-0 top-full mt-2 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl shadow-gray-900/10 dark:shadow-black/30 z-50 py-1.5 animate-in fade-in slide-in-from-top-2 duration-200">
            <button @click="handleBulkMarkRead(false); showBulkMenu = false"
              class="w-full px-3 py-2.5 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2.5 transition-colors group">
              <CircleDot class="w-4 h-4 text-gray-500 group-hover:text-blue-500 transition-colors" />
              <span class="group-hover:text-blue-600 dark:group-hover:text-blue-400">标记未读</span>
            </button>
            <button @click="handleBulkMarkSpam(); showBulkMenu = false"
              class="w-full px-3 py-2.5 text-left text-sm hover:bg-orange-50 dark:hover:bg-orange-900/20 flex items-center gap-2.5 text-orange-600 dark:text-orange-400 transition-colors group">
              <X class="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span class="group-hover:font-medium">标记垃圾邮件</span>
            </button>
            <button v-if="isSpamFolder" @click="handleBulkMarkNotSpam(); showBulkMenu = false"
              class="w-full px-3 py-2.5 text-left text-sm hover:bg-green-50 dark:hover:bg-green-900/20 flex items-center gap-2.5 text-green-600 dark:text-green-400 transition-colors group">
              <CheckCircle class="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span class="group-hover:font-medium">不是垃圾邮件</span>
            </button>
          </div>
        </div>
        <!-- Loading 指示器 -->
        <Loader2 v-if="bulkLoading" class="w-4 h-4 animate-spin text-primary" />
      </div>
    </div>

    <!-- 加载状态 - 改进样式 -->
    <div v-if="loading" class="flex-1 flex flex-col items-center justify-center gap-3">
      <div class="relative">
        <Loader2 class="w-8 h-8 animate-spin text-primary" />
        <div class="absolute inset-0 w-8 h-8 animate-ping text-primary opacity-20">
          <Loader2 class="w-8 h-8" />
        </div>
      </div>
      <span class="text-sm text-gray-500 dark:text-gray-400 animate-pulse">加载中...</span>
    </div>

    <!-- 空状态 - 改进样式 -->
    <div v-else-if="emails.length === 0" class="flex-1 flex flex-col items-center justify-center text-gray-400 text-sm gap-3 px-8">
      <div class="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
        <span class="text-3xl opacity-50">📭</span>
      </div>
      <div class="text-center">
        <p class="font-medium text-gray-600 dark:text-gray-400">暂无邮件</p>
        <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
          {{ isSearching ? '未找到匹配的邮件' : '收件箱是空的' }}
        </p>
      </div>
    </div>

    <!-- 邮件列表 -->
    <div v-else class="flex-1 overflow-y-auto px-2 py-1">
      <div v-for="email in emails" :key="email.id" @click="selectEmail(email.id)"
        :data-email-id="email.id"
        class="email-item px-3 py-3 mb-1.5 cursor-pointer rounded-lg transition-all duration-200 relative group"
        :class="{
          'email-item-selected !bg-primary/10 dark:!bg-primary/20 shadow-sm ring-1 ring-primary/30': selectedEmailId === email.id,
          'hover:!bg-gray-100/70 dark:hover:!bg-gray-800/50 hover:shadow-sm': selectedEmailId !== email.id
        }">
        <div v-if="selectedEmailId === email.id" class="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full"></div>
        
        <!-- 第一行：头像、发件人、快捷操作 -->
        <div class="flex items-center gap-2.5">
          <!-- 选择模式：复选框；非选择模式：未读蓝点 -->
          <template v-if="isSelectionMode">
            <button @click="toggleEmailSelection(email.id, $event)" class="shrink-0">
              <SquareCheck v-if="selectedEmailIds.has(email.id)" class="w-4 h-4 text-primary" />
              <Square v-else class="w-4 h-4 text-gray-400 hover:text-gray-600" />
            </button>
          </template>
          <template v-else>
            <!-- 未读蓝点 - 增强视觉效果 -->
            <div class="w-2 h-2 rounded-full shrink-0 transition-all duration-200"
              :class="email.is_read ? 'bg-transparent' : 'bg-blue-500 shadow-sm shadow-blue-500/50 ring-2 ring-blue-100 dark:ring-blue-900/30'"></div>
          </template>
          <!-- 头像 - 改进阴影和渐变 -->
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-primary-hover flex items-center justify-center text-xs text-white font-bold shadow-md shadow-primary/20 shrink-0 transition-transform duration-200 group-hover:scale-105">
            {{ getAvatar(email.sender) }}
          </div>
          <!-- 发件人 -->
          <div class="flex-1 min-w-0">
            <div class="text-sm text-gray-900 dark:text-white leading-tight truncate" :class="{ 'font-bold': !email.is_read }">
              {{ email.sender }}
            </div>
          </div>
          <!-- 快捷操作按钮：未读、待办、星标 - 改进动画和样式 -->
          <div class="flex items-center gap-0.5 shrink-0">
            <!-- 未读/已读 -->
            <button @click.stop="toggleRead(email.id, !email.is_read)"
              class="p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-white dark:hover:bg-gray-700/80 transition-all duration-200 hover:scale-110 shadow-sm"
              :title="email.is_read ? '标记为未读' : '标记为已读'">
              <Circle class="w-3.5 h-3.5 transition-colors" :class="email.is_read ? 'text-gray-400 hover:text-blue-500' : 'fill-blue-500 text-blue-500'" />
            </button>
            <!-- 待办 -->
            <button @click.stop="openSnoozeModal(email.id)"
              class="p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-white dark:hover:bg-gray-700/80 transition-all duration-200 hover:scale-110 shadow-sm"
              title="待办">
              <Clock class="w-3.5 h-3.5 text-gray-400 hover:text-orange-500 transition-colors" />
            </button>
            <!-- 星标（常亮时始终显示） -->
            <button @click.stop="toggleStar(email.id, !email.is_starred)"
              class="p-1.5 rounded-md hover:bg-white dark:hover:bg-gray-700/80 transition-all duration-200 hover:scale-110 shadow-sm"
              :class="email.is_starred ? '' : 'opacity-0 group-hover:opacity-100'"
              title="星标">
              <Star class="w-3.5 h-3.5 transition-all duration-200"
                :class="email.is_starred ? 'fill-yellow-400 text-yellow-400 drop-shadow-sm' : 'text-gray-400 hover:text-yellow-500'" />
            </button>
          </div>
        </div>
        
        <!-- 第二行：主题 - 改进排版 -->
        <div class="ml-[44px] mt-1.5">
          <div class="text-[13px] text-gray-800 dark:text-gray-200 truncate leading-snug transition-colors"
            :class="{ 'font-semibold text-gray-900 dark:text-white': !email.is_read }">
            {{ email.subject }}
          </div>
        </div>

        <!-- 第三行：摘要 + 附件/投递状态/追踪 + 时间 - 改进布局 -->
        <div class="ml-[44px] mt-1.5 flex items-end justify-between gap-3">
          <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 leading-relaxed flex-1 transition-colors">{{ email.snippet }}</p>
          <div class="flex items-center gap-1.5 shrink-0">
            <!-- 附件图标 - 改进样式 -->
            <span v-if="email.has_attachments" class="text-gray-400 transition-colors group-hover:text-gray-500" title="有附件">
              <Paperclip class="w-3 h-3" />
            </span>
            <!-- 已发送文件夹：显示投递状态 - 改进颜色 -->
            <template v-if="isSentFolder">
              <span v-if="email.delivery_status === 'pending'" class="text-gray-400" title="等待发送">
                <Loader2 class="w-3 h-3 animate-spin" />
              </span>
              <span v-else-if="email.delivery_status === 'sending'" class="text-blue-500" title="发送中">
                <Loader2 class="w-3 h-3 animate-spin" />
              </span>
              <span v-else-if="email.delivery_status === 'sent'" class="text-emerald-500" title="已发送">
                <CheckCircle class="w-3 h-3" />
              </span>
              <span v-else-if="email.delivery_status === 'failed'" class="text-red-500" title="发送失败">
                <XCircle class="w-3 h-3" />
              </span>
              <!-- 追踪图标 -->
              <span v-if="email.is_tracked" class="text-purple-500" title="已启用追踪">
                <Eye class="w-3 h-3" />
              </span>
            </template>
            <!-- 时间 - 改进排版 -->
            <span class="text-[11px] text-gray-400 dark:text-gray-500 font-medium tabular-nums tracking-tight">
              {{ formatTime(email.received_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 待办时间选择对话框 -->
    <CommonModal v-model="showSnoozeModal" title="设置待办提醒" width-class="w-full max-w-sm">
      <div v-if="!showCustomPicker" class="space-y-1">
        <!-- 快捷选项 - 改进样式 -->
        <button @click="handleSnooze('later')"
          class="w-full px-4 py-3.5 text-left hover:bg-primary/10 dark:hover:bg-primary/20 rounded-xl transition-all duration-200 flex items-center gap-3.5 group hover:shadow-sm">
          <div class="w-11 h-11 rounded-full bg-gradient-to-br from-orange-100 to-orange-50 dark:from-orange-900/30 dark:to-orange-900/20 flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <Clock class="w-5 h-5 text-orange-500" />
          </div>
          <div class="flex-1">
            <div class="font-semibold group-hover:text-primary transition-colors">今天晚些时候</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">3小时后提醒</div>
          </div>
        </button>

        <button @click="handleSnooze('tomorrow')"
          class="w-full px-4 py-3.5 text-left hover:bg-primary/10 dark:hover:bg-primary/20 rounded-xl transition-all duration-200 flex items-center gap-3.5 group hover:shadow-sm">
          <div class="w-11 h-11 rounded-full bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/30 dark:to-blue-900/20 flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <span class="text-blue-500 font-bold text-sm">明</span>
          </div>
          <div class="flex-1">
            <div class="font-semibold group-hover:text-primary transition-colors">明天</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">明天早上 9:00</div>
          </div>
        </button>

        <button @click="handleSnooze('nextWeek')"
          class="w-full px-4 py-3.5 text-left hover:bg-primary/10 dark:hover:bg-primary/20 rounded-xl transition-all duration-200 flex items-center gap-3.5 group hover:shadow-sm">
          <div class="w-11 h-11 rounded-full bg-gradient-to-br from-purple-100 to-purple-50 dark:from-purple-900/30 dark:to-purple-900/20 flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <span class="text-purple-500 font-bold text-sm">周一</span>
          </div>
          <div class="flex-1">
            <div class="font-semibold group-hover:text-primary transition-colors">下周一</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">下周一早上 9:00</div>
          </div>
        </button>

        <!-- 分割线 -->
        <div class="border-t border-gray-200 dark:border-gray-700 my-3"></div>

        <!-- 自定义时间按钮 - 改进样式 -->
        <button @click="showCustomPicker = true"
          class="w-full px-4 py-3.5 text-left hover:bg-primary/10 dark:hover:bg-primary/20 rounded-xl transition-all duration-200 flex items-center gap-3.5 group hover:shadow-sm">
          <div class="w-11 h-11 rounded-full bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <span class="text-2xl">📅</span>
          </div>
          <div class="flex-1">
            <div class="font-semibold group-hover:text-primary transition-colors">选择日期和时间</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">自定义提醒时间</div>
          </div>
        </button>
      </div>

      <!-- 自定义日期时间选择器 -->
      <div v-else>
        <CommonDateTimePicker v-model="customDateTime" />
        <div class="flex gap-2 mt-4">
          <button @click="showCustomPicker = false"
            class="flex-1 px-4 py-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 rounded-lg">
            返回
          </button>
          <button @click="handleCustomSnooze" :disabled="!customDateTime"
            class="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed">
            确定
          </button>
        </div>
      </div>
    </CommonModal>
  </div>
</template>

<style scoped>
/* 批量操作工具栏容器 - 防止跳动 */
.bulk-toolbar-container {
  min-height: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.bulk-toolbar-container.py-2\.5 {
  min-height: 48px;
}

/* 邮件列表项动画 */
.email-item {
  position: relative;
  overflow: hidden;
}

.email-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.05), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.email-item:hover::before {
  transform: translateX(100%);
}

/* 选中状态动画 */
.email-item-selected {
  animation: selectPulse 0.3s ease-out;
}

@keyframes selectPulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.98);
  }
  100% {
    transform: scale(1);
  }
}

/* 自定义滚动条 */
.email-list-container ::-webkit-scrollbar {
  width: 6px;
}

.email-list-container ::-webkit-scrollbar-track {
  background: transparent;
}

.email-list-container ::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.3);
  border-radius: 3px;
  transition: background 0.2s;
}

.email-list-container ::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.5);
}

/* 暗色模式滚动条 */
.dark .email-list-container ::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.4);
}

.dark .email-list-container ::-webkit-scrollbar-thumb:hover {
  background: rgba(75, 85, 99, 0.6);
}
</style>