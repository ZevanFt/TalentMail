<script setup lang="ts">
import {
  Mail, Star, Send, File, Trash2, Plus, Box,
  Archive, AlertOctagon, CircleDot,
  ChevronRight, ChevronDown, RotateCw,
  FolderOpen, Tag, Clock, Paperclip, Users, Cloud, PlusCircle
} from 'lucide-vue-next'

const { isComposeOpen } = useGlobalModal()
const { folders, currentFolderId, loadEmails, loadFolders, loadFilteredEmails, loadSnoozedEmails, loadAllEmails, currentFilter } = useEmails()
const { token } = useApi()
const route = useRoute()

const isOpen = reactive({ more: false, tags: true, center: true, tools: true })
const toggle = (key: keyof typeof isOpen) => { isOpen[key] = !isOpen[key] }

// 文件夹角色 -> 中文名称 & 图标映射
const folderConfig: Record<string, { name: string; icon: any; iconClass?: string }> = {
  inbox: { name: '收件箱', icon: Mail },
  sent: { name: '已发送', icon: Send },
  drafts: { name: '草稿箱', icon: File },
  trash: { name: '已删除', icon: Trash2 },
  spam: { name: '垃圾邮件', icon: AlertOctagon },
  archive: { name: '归档', icon: Archive },
}

// 虚拟文件夹（前端特有视图，不对应后端文件夹）
const virtualFolders = {
  starred: { id: 'starred', name: '红旗邮件', icon: Star, iconClass: 'text-red-500', filter: { is_starred: true } },
  unread: { id: 'unread', name: '未读邮件', icon: CircleDot, iconClass: 'text-blue-500', filter: { is_read: false } },
  snoozed: { id: 'snoozed', name: '待办邮件', icon: Clock, filter: { snoozed: true } },
}

// 获取文件夹显示名称
const getFolderName = (role: string, originalName: string) => folderConfig[role]?.name || originalName
const getFolderIcon = (role: string) => folderConfig[role]?.icon || FolderOpen

// 主要文件夹（收件箱、未读、红旗、待办、草稿、已发送）
const mainFolders = computed(() => {
  const result: any[] = []
  // 收件箱
  const inbox = folders.value.find(f => f.role === 'inbox')
  if (inbox) result.push({ ...inbox, name: getFolderName(inbox.role, inbox.name), icon: getFolderIcon(inbox.role) })
  // 未读邮件（虚拟）
  result.push(virtualFolders.unread)
  // 红旗邮件（虚拟）
  result.push(virtualFolders.starred)
  // 待办邮件（虚拟）
  result.push(virtualFolders.snoozed)
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
  { id: 'all', name: '所有邮件', icon: FolderOpen, virtual: true, unread_count: 0 }
])

// 当前选中的虚拟文件夹 ID
const selectedVirtualId = useState<string | null>('selectedVirtualId', () => null)

// 切换文件夹
const selectFolder = (folder: any) => {
  if (folder.id === 'snoozed') {
    // 待办邮件
    selectedVirtualId.value = folder.id
    loadSnoozedEmails()
  } else if (folder.id === 'all') {
    // 所有邮件
    selectedVirtualId.value = folder.id
    loadAllEmails()
  } else if (folder.filter) {
    // 其他虚拟文件夹：使用筛选
    selectedVirtualId.value = folder.id
    loadFilteredEmails(folder.filter)
  } else {
    // 真实文件夹
    selectedVirtualId.value = null
    loadEmails(folder.id)
  }
}

// 判断是否选中
const isSelected = (folder: any) => {
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
})

const tags = ref([
  { id: 1, name: '工作', color: 'bg-blue-500' },
  { id: 2, name: '财务', color: 'bg-yellow-500' },
  { id: 3, name: '紧急', color: 'bg-red-500' },
])

const tools = [
  { name: '附件中心', icon: Paperclip, to: '/attachments' },
  { name: '通讯录', icon: Users, to: '/contacts' },
  { name: '文件中转站', icon: Cloud, to: '/drive' },
]

const isActive = (path: string) => route.path === path
</script>

<template>
  <aside
    class="w-64 h-full bg-gray-50/50 dark:bg-bg-panelDark/50 border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0 transition-colors duration-200 pt-4 font-sans select-none">

    <!-- 写邮件 -->
    <div class="px-3 mb-2">
      <button @click="isComposeOpen = true"
        class="w-full bg-primary hover:bg-primary-hover active:scale-95 text-white py-2.5 rounded-lg flex items-center justify-center gap-2 font-bold shadow-md shadow-purple-500/20 transition-all duration-200 text-sm">
        <Plus class="w-4 h-4" stroke-width="2.5" />
        写邮件
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
          <span class="flex-1 truncate">更多</span>
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

      <!-- 3. 邮件标签 -->
      <div class="mt-1">
        <button @click="toggle('tags')" class="nav-item group w-full text-left">
          <component :is="isOpen.tags ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">邮件标签</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.tags" class="overflow-hidden space-y-0.5">
            <a v-for="tag in tags" :key="tag.id" href="#" class="sub-item group">
              <div :class="`w-3 h-3 rounded-sm ${tag.color} shrink-0`"></div>
              <span class="flex-1 truncate">{{ tag.name }}</span>
            </a>
          </div>
        </Transition>
      </div>

      <!-- 4. 邮箱中心 -->
      <div class="mt-1">
        <button @click="toggle('center')" class="nav-item group w-full text-left">
          <component :is="isOpen.center ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">邮箱中心</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.center" class="overflow-hidden pt-1 space-y-0.5">
            <div
              class="ml-9 mr-2 bg-blue-50/60 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-lg p-2.5 mb-1 group cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 transition-colors min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] text-gray-500 font-medium">代收中</span>
                <RotateCw class="w-3 h-3 text-blue-500 animate-spin-slow shrink-0" />
              </div>
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0"></div>
                <div class="text-xs font-bold text-gray-700 dark:text-gray-200 truncate" title="my.gmail@gmail.com">
                  my.gmail@...
                </div>
              </div>
            </div>

            <button class="sub-item text-gray-500 hover:text-primary">
              <PlusCircle class="w-4 h-4 shrink-0" />
              <span class="truncate">添加其他邮箱</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- 5. 其他工具 -->
      <div class="mt-1">
        <button @click="toggle('tools')" class="nav-item group w-full text-left">
          <component :is="isOpen.tools ? ChevronDown : ChevronRight" class="w-4 h-4 shrink-0 text-inherit" />
          <span class="flex-1 truncate">其他工具</span>
        </button>

        <Transition name="slide">
          <div v-if="isOpen.tools" class="overflow-hidden space-y-0.5">
            <NuxtLink v-for="item in tools" :key="item.name" :to="item.to" class="sub-item group" active-class="active">
              <component :is="item.icon" class="w-4 h-4 shrink-0 transition-colors text-inherit"
                :class="isActive(item.to) ? 'text-primary' : ''" />
              <span class="flex-1 truncate">{{ item.name }}</span>
            </NuxtLink>
          </div>
        </Transition>
      </div>

    </nav>

    <!-- 底部账号池 -->
    <div class="p-3 mt-auto border-t border-gray-200 dark:border-gray-800">
      <NuxtLink to="/pool"
        class="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg hover:bg-white dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 transition-all shadow-sm hover:shadow border border-gray-200/50 hover:border-gray-200 dark:border-gray-800 dark:hover:border-gray-700 group bg-white dark:bg-gray-900">
        <div class="p-1 bg-primary/10 rounded-md shrink-0">
          <Box class="w-4 h-4 text-primary group-hover:scale-105 transition-transform" />
        </div>
        <span class="font-bold text-sm truncate">账号池</span>
      </NuxtLink>
    </div>
  </aside>
</template>

<style scoped>
/* 核心样式：确保 nav-item 和 sub-item 结构稳定 */
.nav-item {
  @apply flex items-center gap-3 px-3 py-2 mx-2 rounded-md text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800 transition-colors cursor-pointer select-none font-medium;
}

.nav-item.active {
  @apply bg-white dark:bg-gray-800 text-primary dark:text-primary font-bold shadow-sm;
}

.sub-item {
  @apply flex items-center gap-3 px-3 py-1.5 pl-9 mx-2 rounded-md text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800 transition-colors cursor-pointer select-none;
}

.sub-item.active {
  @apply bg-white dark:bg-gray-800 text-primary dark:text-primary font-bold;
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