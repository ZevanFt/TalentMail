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
    await loadEmails()
    // 启动实时同步（WebSocket + 备用轮询）
    startAutoSync()
  }
})

onUnmounted(() => {
  stopAutoSync()
})
</script>

<template>
  <div class="w-80 h-full bg-white dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">
    <!-- 标题栏 -->
    <div class="px-4 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
      <span class="truncate flex-1">{{ currentFolderName }} ({{ emails.length }})</span>
      <div class="flex items-center gap-1 shrink-0">
        <button v-if="isSearching" @click="clearSearch" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-primary" title="清除搜索">
          <X class="w-4 h-4" />
        </button>
        <!-- 批量选择按钮 -->
        <button @click="toggleSelectionMode"
          class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          :class="{ 'bg-primary/10 text-primary': isSelectionMode }"
          :title="isSelectionMode ? '退出选择' : '批量选择'">
          <SquareCheck class="w-4 h-4" />
        </button>
        <button @click="sync" :disabled="syncing" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <Loader2 v-if="syncing" class="w-4 h-4 animate-spin" />
          <RefreshCw v-else class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 批量操作工具栏 -->
    <div v-if="isSelectionMode && selectedEmailIds.size > 0"
      class="px-3 py-2 bg-primary/5 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
      <!-- 全选 -->
      <button @click="toggleSelectAll" class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" :title="isAllSelected ? '取消全选' : '全选'">
        <SquareCheck v-if="isAllSelected" class="w-4 h-4 text-primary" />
        <Square v-else class="w-4 h-4 text-gray-500" />
      </button>
      <span class="text-xs text-gray-600 dark:text-gray-400">{{ selectedEmailIds.size }} 封</span>
      <div class="flex-1"></div>
      <!-- 批量操作按钮 -->
      <button @click="handleBulkMarkRead(true)" :disabled="bulkLoading" class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="标记已读">
        <CheckCheck class="w-4 h-4 text-gray-600 dark:text-gray-400" />
      </button>
      <button @click="handleBulkArchive" :disabled="bulkLoading" class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="归档">
        <Archive class="w-4 h-4 text-gray-600 dark:text-gray-400" />
      </button>
      <button @click="handleBulkDelete" :disabled="bulkLoading" class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="删除">
        <Trash2 class="w-4 h-4 text-red-500" />
      </button>
      <!-- 更多操作下拉 -->
      <div class="relative">
        <button @click="showBulkMenu = !showBulkMenu" class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="更多操作">
          <MoreHorizontal class="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
        <div v-if="showBulkMenu"
          class="absolute right-0 top-full mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 py-1">
          <button @click="handleBulkMarkRead(false); showBulkMenu = false"
            class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
            <CircleDot class="w-4 h-4" /> 标记未读
          </button>
          <button @click="handleBulkMarkSpam(); showBulkMenu = false"
            class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-orange-600">
            <X class="w-4 h-4" /> 标记垃圾邮件
          </button>
          <button v-if="isSpamFolder" @click="handleBulkMarkNotSpam(); showBulkMenu = false"
            class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-green-600">
            <CheckCircle class="w-4 h-4" /> 不是垃圾邮件
          </button>
        </div>
      </div>
      <!-- Loading 指示器 -->
      <Loader2 v-if="bulkLoading" class="w-4 h-4 animate-spin text-primary" />
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <Loader2 class="w-6 h-6 animate-spin text-gray-400" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="emails.length === 0" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
      暂无邮件
    </div>

    <!-- 邮件列表 -->
    <div v-else class="flex-1 overflow-y-auto">
      <div v-for="email in emails" :key="email.id" @click="selectEmail(email.id)"
        class="px-4 py-3 border-b border-gray-50 dark:border-gray-800 cursor-pointer transition-all hover:bg-gray-50 dark:hover:bg-gray-800/50 relative group"
        :class="{ 'bg-blue-50/30 dark:bg-gray-800': selectedEmailId === email.id }">
        <div v-if="selectedEmailId === email.id" class="absolute left-0 top-0 bottom-0 w-[3px] bg-primary"></div>
        
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
            <!-- 未读蓝点 -->
            <div class="w-2 h-2 rounded-full shrink-0" :class="email.is_read ? 'bg-transparent' : 'bg-blue-500'"></div>
          </template>
          <!-- 头像 -->
          <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs text-white font-bold shadow-sm shrink-0">
            {{ getAvatar(email.sender) }}
          </div>
          <!-- 发件人 -->
          <div class="flex-1 min-w-0">
            <div class="text-sm text-gray-900 dark:text-white leading-tight truncate" :class="{ 'font-bold': !email.is_read }">
              {{ email.sender }}
            </div>
          </div>
          <!-- 快捷操作按钮：未读、待办、星标 -->
          <div class="flex items-center gap-1 shrink-0">
            <!-- 未读/已读 -->
            <button @click.stop="toggleRead(email.id, !email.is_read)"
              class="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
              :title="email.is_read ? '标记为未读' : '标记为已读'">
              <Circle class="w-3.5 h-3.5" :class="email.is_read ? 'text-gray-400' : 'fill-blue-500 text-blue-500'" />
            </button>
            <!-- 待办 -->
            <button @click.stop="openSnoozeModal(email.id)"
              class="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
              title="待办">
              <Clock class="w-3.5 h-3.5 text-gray-400" />
            </button>
            <!-- 星标（常亮时始终显示） -->
            <button @click.stop="toggleStar(email.id, !email.is_starred)"
              class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
              :class="email.is_starred ? '' : 'opacity-0 group-hover:opacity-100'"
              title="星标">
              <Star class="w-3.5 h-3.5" :class="email.is_starred ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'" />
            </button>
          </div>
        </div>
        
        <!-- 第二行：主题 -->
        <div class="ml-[42px] mt-1">
          <div class="text-xs text-gray-700 dark:text-gray-300 truncate" :class="{ 'font-semibold': !email.is_read }">
            {{ email.subject }}
          </div>
        </div>
        
        <!-- 第三行：摘要 + 附件/投递状态/追踪 + 时间 -->
        <div class="ml-[42px] mt-1 flex items-end justify-between gap-2">
          <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 leading-relaxed flex-1">{{ email.snippet }}</p>
          <div class="flex items-center gap-1.5 shrink-0">
            <!-- 附件图标 -->
            <span v-if="email.has_attachments" class="text-gray-400" title="有附件">
              <Paperclip class="w-3 h-3" />
            </span>
            <!-- 已发送文件夹：显示投递状态 -->
            <template v-if="isSentFolder">
              <span v-if="email.delivery_status === 'pending'" class="text-gray-400" title="等待发送">
                <Loader2 class="w-3 h-3 animate-spin" />
              </span>
              <span v-else-if="email.delivery_status === 'sending'" class="text-blue-500" title="发送中">
                <Loader2 class="w-3 h-3 animate-spin" />
              </span>
              <span v-else-if="email.delivery_status === 'sent'" class="text-green-500" title="已发送">
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
            <span class="text-[10px] text-gray-400 font-medium">{{ formatTime(email.received_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 待办时间选择对话框 -->
    <CommonModal v-model="showSnoozeModal" title="设置待办提醒" width-class="w-full max-w-sm">
      <div v-if="!showCustomPicker" class="space-y-1">
        <!-- 快捷选项 -->
        <button @click="handleSnooze('later')"
          class="w-full px-4 py-3 text-left hover:bg-primary/10 rounded-lg transition-colors flex items-center gap-3 group">
          <div class="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
            <Clock class="w-5 h-5 text-orange-500" />
          </div>
          <div>
            <div class="font-medium group-hover:text-primary">今天晚些时候</div>
            <div class="text-xs text-gray-500">3小时后提醒</div>
          </div>
        </button>
        
        <button @click="handleSnooze('tomorrow')"
          class="w-full px-4 py-3 text-left hover:bg-primary/10 rounded-lg transition-colors flex items-center gap-3 group">
          <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
            <span class="text-blue-500 font-bold text-sm">明</span>
          </div>
          <div>
            <div class="font-medium group-hover:text-primary">明天</div>
            <div class="text-xs text-gray-500">明天早上 9:00</div>
          </div>
        </button>
        
        <button @click="handleSnooze('nextWeek')"
          class="w-full px-4 py-3 text-left hover:bg-primary/10 rounded-lg transition-colors flex items-center gap-3 group">
          <div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
            <span class="text-purple-500 font-bold text-sm">周一</span>
          </div>
          <div>
            <div class="font-medium group-hover:text-primary">下周一</div>
            <div class="text-xs text-gray-500">下周一早上 9:00</div>
          </div>
        </button>

        <!-- 分割线 -->
        <div class="border-t border-gray-200 dark:border-gray-700 my-3"></div>

        <!-- 自定义时间按钮 -->
        <button @click="showCustomPicker = true"
          class="w-full px-4 py-3 text-left hover:bg-primary/10 rounded-lg transition-colors flex items-center gap-3 group">
          <div class="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
            <span class="text-gray-500 text-lg">📅</span>
          </div>
          <div>
            <div class="font-medium group-hover:text-primary">选择日期和时间</div>
            <div class="text-xs text-gray-500">自定义提醒时间</div>
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