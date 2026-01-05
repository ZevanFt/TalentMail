<script setup lang="ts">
import { Search, Moon, Sun, Settings, Mail, X, LogOut, Crown, HardDrive, Copy, Check } from 'lucide-vue-next'
const router = useRouter()
const { isDark, toggleTheme } = useTheme()
const { search, clearSearch, searchQuery, isSearching } = useEmails()
const { getMe, getStorageStats, getSubscriptionStatus, logout } = useApi()

const localQuery = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// 用户信息
const user = ref<{ email: string; display_name?: string } | null>(null)
const storage = ref<{ storage_used_bytes: number; storage_limit_bytes: number } | null>(null)
const subscription = ref<{ plan_name: string; expires_at: string | null; is_active: boolean; status: string } | null>(null)

onMounted(async () => {
  try {
    user.value = await getMe()
    storage.value = await getStorageStats()
    subscription.value = await getSubscriptionStatus()
  } catch (e) {}
})

// 获取邮箱前缀
const emailPrefix = computed(() => user.value?.email?.split('@')[0] || '')

// 存储使用百分比
const storagePercent = computed(() => {
  if (!storage.value) return 0
  // 管理员或无限配额
  if (subscription.value?.status === 'admin' || storage.value.storage_limit_bytes === -1) return 0
  return Math.round((storage.value.storage_used_bytes / storage.value.storage_limit_bytes) * 100)
})

// 格式化存储大小
const formatStorage = (bytes: number) => {
  if (bytes === -1) return '无限'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// 退出登录
const handleLogout = () => {
  logout()
  router.push('/login')
}

// 防抖搜索
const handleInput = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    search(localQuery.value)
  }, 300)
}

// 清除搜索
const handleClear = () => {
  localQuery.value = ''
  clearSearch()
}

// 回车立即搜索
const handleEnter = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  search(localQuery.value)
}

// 复制邮箱
const copied = ref(false)
const copyEmail = async () => {
  if (!user.value?.email) return
  try {
    await navigator.clipboard.writeText(user.value.email)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    console.error('复制失败:', e)
  }
}
</script>

<template>
    <header
        class="h-14 bg-white dark:bg-bg-panelDark border-b border-gray-200 dark:border-border-dark flex items-center justify-between px-4 shrink-0 transition-colors duration-200 z-20 relative">

        <!-- 左侧 Logo -->
        <NuxtLink to="/" class="w-64 flex items-center gap-2 shrink-0 hover:opacity-80 transition-opacity">
            <Mail class="w-6 h-6 text-primary fill-primary/10" stroke-width="2.5" />
            <span class="font-bold text-xl text-gray-900 dark:text-white tracking-tight font-sans">TalentMail</span>
        </NuxtLink>

        <!-- 搜索框 -->
        <div class="flex-1 flex justify-center max-w-xl px-4">
            <div class="relative w-full group">
                <Search
                    class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary transition-colors" />
                <input v-model="localQuery" @input="handleInput" @keyup.enter="handleEnter" type="text" placeholder="搜索邮件..."
                    class="w-full bg-gray-100 dark:bg-gray-800 border-transparent focus:bg-white dark:focus:bg-gray-900 border border-transparent focus:border-primary/20 rounded-lg py-1.5 pl-9 pr-9 text-sm focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all text-gray-900 dark:text-white placeholder-gray-400">
                <button v-if="localQuery" @click="handleClear" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    <X class="w-4 h-4" />
                </button>
            </div>
        </div>

        <div class="flex items-center gap-1.5 justify-end shrink-0 w-64">
            <button @click="toggleTheme"
                class="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                <Sun v-if="isDark" class="w-4 h-4" />
                <Moon v-else class="w-4 h-4" />
            </button>
            <button @click="router.push('/settings')"
                class="p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                <Settings class="w-4 h-4" />
            </button>
            
            <!-- 用户头像 + Hover 下拉卡片 -->
            <div class="relative group ml-3">
                <div class="flex items-center gap-2 cursor-pointer">
                    <span v-if="emailPrefix" class="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:block">{{ emailPrefix }}</span>
                    <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 border border-gray-100 dark:border-gray-700 shadow-sm group-hover:ring-2 group-hover:ring-primary/20 transition-all flex items-center justify-center text-white text-xs font-bold">
                        {{ emailPrefix?.[0]?.toUpperCase() || '?' }}
                    </div>
                </div>
                
                <!-- Hover 下拉卡片 -->
                <div class="absolute right-0 top-full mt-2 w-72 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    <!-- 用户信息 -->
                    <div class="p-4 border-b border-gray-100 dark:border-gray-700">
                        <div class="flex items-center gap-3">
                            <div class="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white text-lg font-bold shadow-md">
                                {{ emailPrefix?.[0]?.toUpperCase() || '?' }}
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="font-bold text-gray-900 dark:text-white truncate">{{ user?.display_name || emailPrefix }}</div>
                                <div class="flex items-center gap-1.5 group/email">
                                    <div class="text-xs text-gray-500 truncate">{{ user?.email }}</div>
                                    <button
                                        @click.stop="copyEmail"
                                        class="p-0.5 rounded opacity-0 group-hover/email:opacity-100 transition-opacity hover:bg-gray-100 dark:hover:bg-gray-700"
                                        :title="copied ? '已复制!' : '复制邮箱'"
                                    >
                                        <Check v-if="copied" class="w-3 h-3 text-green-500" />
                                        <Copy v-else class="w-3 h-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 会员状态 -->
                    <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                        <div class="flex items-center gap-2 mb-2">
                            <Crown class="w-4 h-4 text-yellow-500" />
                            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                                {{ subscription?.status === 'admin' ? '管理员无限版' : (subscription?.plan_name || '免费版') }}
                            </span>
                            <span v-if="subscription?.status === 'admin'" class="text-[10px] px-1.5 py-0.5 bg-purple-100 text-purple-600 rounded">永久</span>
                            <span v-else-if="subscription?.is_active" class="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-600 rounded">有效</span>
                        </div>
                        <div v-if="subscription?.expires_at" class="text-xs text-gray-500">
                            到期时间: {{ new Date(subscription.expires_at).toLocaleDateString('zh-CN') }}
                        </div>
                        <div v-else-if="subscription?.status === 'admin'" class="text-xs text-gray-500">
                            尊贵的管理员，您拥有无限资源
                        </div>
                    </div>
                    
                    <!-- 存储空间 -->
                    <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2">
                                <HardDrive class="w-4 h-4 text-gray-400" />
                                <span class="text-sm text-gray-600 dark:text-gray-400">存储空间</span>
                            </div>
                            <span class="text-xs text-gray-500">
                                {{ subscription?.status === 'admin' ? '无限' : storagePercent + '%' }}
                            </span>
                        </div>
                        <div v-if="subscription?.status !== 'admin'" class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div class="h-full bg-primary rounded-full transition-all" :style="{ width: storagePercent + '%' }"></div>
                        </div>
                        <div class="text-xs text-gray-500 mt-1">
                            {{ formatStorage(storage?.storage_used_bytes || 0) }} / {{ subscription?.status === 'admin' ? '无限' : formatStorage(storage?.storage_limit_bytes || 0) }}
                        </div>
                    </div>
                    
                    <!-- 操作按钮 -->
                    <div class="p-2">
                        <button @click="router.push('/settings')" class="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                            <Settings class="w-4 h-4" />
                            设置
                        </button>
                        <button @click="handleLogout" class="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
                            <LogOut class="w-4 h-4" />
                            退出登录
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </header>
</template>