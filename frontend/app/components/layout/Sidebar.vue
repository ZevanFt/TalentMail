<script setup lang="ts">
import {
  Mail, Star, Send, File, Trash2, Plus, Box,
  Archive, AlertOctagon, CircleDot,
  ChevronRight, ChevronDown, RotateCw,
  FolderOpen, Tag, Clock, Paperclip, Users, Cloud, PlusCircle, X, Check, Pencil
} from 'lucide-vue-next'

const { isComposeOpen } = useGlobalModal()
const { folders, currentFolderId, loadEmails, loadFolders, loadFilteredEmails, loadSnoozedEmails, loadAllEmails, currentFilter } = useEmails()
const { token, getTags, createTag, updateTag, deleteTag, getExternalAccounts, createExternalAccount } = useApi()
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
  try { tags.value = await getTags() } catch {}
}

// 外部邮箱账号
const externalAccounts = ref<any[]>([])
const loadExternalAccounts = async () => {
  try { externalAccounts.value = await getExternalAccounts() } catch {}
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
    accountError.value = e.data?.detail || '添加失败'
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
  } catch {}
}

const removeTag = async (id: number) => {
  if (!confirm('确定删除此标签？')) return
  try { await deleteTag(id); await loadTags() } catch {}
}

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
const selectedTagId = useState<number | null>('selectedTagId', () => null)

// 切换文件夹
const selectFolder = async (folder: any) => {
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
  // 先设置状态，确保 EmailList 不会加载默认邮件
  selectedVirtualId.value = null
  selectedTagId.value = tag.id
  
  // 如果不在首页，先导航回首页
  if (route.path !== '/') {
    await router.push('/')
    // 等待下一个 tick 确保组件已挂载
    await nextTick()
  }
  
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
              <span class="truncate">添加标签</span>
            </button>
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
            <div v-for="account in externalAccounts" :key="account.id"
              class="ml-9 mr-2 bg-blue-50/60 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-lg p-2.5 mb-1 group cursor-pointer hover:border-blue-300 dark:hover:border-blue-700 transition-colors min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] text-gray-500 font-medium">{{ account.is_active ? '代收中' : '已停用' }}</span>
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

  <!-- 标签编辑弹窗 -->
  <Teleport to="body">
    <div v-if="showTagModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showTagModal = false">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-4 w-80 shadow-xl">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold">{{ editingTag ? '编辑标签' : '新建标签' }}</h3>
          <button @click="showTagModal = false"><X class="w-4 h-4" /></button>
        </div>
        <input v-model="tagForm.name" placeholder="标签名称" class="w-full px-3 py-2 border rounded-lg mb-3 dark:bg-gray-700 dark:border-gray-600" />
        <div class="flex gap-2 mb-4">
          <button v-for="c in tagColors" :key="c" @click="tagForm.color = c" class="w-6 h-6 rounded-full" :style="{ backgroundColor: c }" :class="tagForm.color === c ? 'ring-2 ring-offset-2 ring-primary' : ''"></button>
        </div>
        <div class="flex gap-2">
          <button v-if="editingTag" @click="removeTag(editingTag.id)" class="px-3 py-1.5 text-red-500 hover:bg-red-50 rounded-lg text-sm">删除</button>
          <div class="flex-1"></div>
          <button @click="showTagModal = false" class="px-3 py-1.5 text-gray-500 hover:bg-gray-100 rounded-lg text-sm">取消</button>
          <button @click="saveTag" class="px-3 py-1.5 bg-primary text-white rounded-lg text-sm">保存</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 添加外部账号弹窗 -->
  <Teleport to="body">
    <div v-if="showAddAccountModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showAddAccountModal = false">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-5 w-96 shadow-xl">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold text-gray-900 dark:text-white">添加外部邮箱</h3>
          <button @click="showAddAccountModal = false"><X class="w-4 h-4" /></button>
        </div>
        <div class="space-y-3 max-h-80 overflow-y-auto">
          <div>
            <label class="block text-xs text-gray-500 mb-1">邮箱服务商</label>
            <select v-model="newAccount.provider" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm">
              <optgroup label="国际邮箱">
                <option value="gmail">Gmail</option>
                <option value="outlook">Outlook / Hotmail</option>
                <option value="icloud">iCloud</option>
                <option value="yahoo">Yahoo Mail</option>
                <option value="zoho">Zoho Mail</option>
              </optgroup>
              <optgroup label="国内邮箱">
                <option value="qq">QQ 邮箱</option>
                <option value="163">网易 163 邮箱</option>
                <option value="126">网易 126 邮箱</option>
                <option value="yeah">Yeah.net 邮箱</option>
                <option value="sina">新浪邮箱</option>
                <option value="aliyun">阿里云邮箱</option>
              </optgroup>
              <optgroup label="其他">
                <option value="custom">自定义 IMAP/SMTP</option>
              </optgroup>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">邮箱地址</label>
            <input v-model="newAccount.email" type="email" placeholder="your@email.com" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">密码/应用专用密码</label>
            <input v-model="newAccount.password" type="password" placeholder="请输入密码" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
            <p class="text-[10px] text-gray-400 mt-1">Gmail/Outlook/iCloud 需使用应用专用密码</p>
          </div>
          <!-- 自定义服务器配置 -->
          <template v-if="isCustomProvider">
            <div class="border-t pt-3 mt-2">
              <p class="text-xs text-gray-500 mb-2 font-medium">IMAP 收件服务器</p>
              <div class="flex gap-2">
                <input v-model="newAccount.imap_host" type="text" placeholder="imap.example.com" class="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
                <input v-model.number="newAccount.imap_port" type="number" placeholder="993" class="w-20 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
              </div>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-2 font-medium">SMTP 发件服务器</p>
              <div class="flex gap-2">
                <input v-model="newAccount.smtp_host" type="text" placeholder="smtp.example.com" class="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
                <input v-model.number="newAccount.smtp_port" type="number" placeholder="587" class="w-20 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 text-sm" />
              </div>
            </div>
          </template>
          <div v-if="accountError" class="text-red-500 text-xs">{{ accountError }}</div>
        </div>
        <div class="flex gap-2 mt-4">
          <div class="flex-1"></div>
          <button @click="showAddAccountModal = false" class="px-3 py-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm">取消</button>
          <button @click="handleAddAccount" :disabled="addingAccount || !newAccount.email || !newAccount.password || (isCustomProvider && (!newAccount.imap_host || !newAccount.smtp_host))" class="px-3 py-1.5 bg-primary text-white rounded-lg text-sm disabled:opacity-50">
            {{ addingAccount ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
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