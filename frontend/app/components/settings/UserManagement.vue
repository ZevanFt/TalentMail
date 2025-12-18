<script setup lang="ts">
import { Search, RefreshCw } from 'lucide-vue-next'

const { getUsers, updateUserPermissions } = useApi()

interface User {
    id: number
    email: string
    display_name: string | null
    role: string
    pool_enabled: boolean | null
    created_at: string
}

const users = ref<User[]>([])
const total = ref(0)
const loading = ref(false)
const searchQuery = ref('')
const page = ref(1)
const limit = ref(20)
const limitOptions = [10, 20, 50, 100]

const loadUsers = async () => {
    loading.value = true
    try {
        const res = await getUsers(searchQuery.value || undefined, page.value, limit.value)
        users.value = res.items
        total.value = res.total
    } catch (e) {
        console.error('加载用户失败', e)
    } finally {
        loading.value = false
    }
}

const updateRole = async (user: User, newRole: string) => {
    try {
        await updateUserPermissions(user.id, { role: newRole })
        user.role = newRole
        if (newRole === 'admin') user.pool_enabled = true
    } catch (e: any) {
        alert(e.data?.detail || '操作失败')
    }
}

const togglePool = async (user: User) => {
    const newValue = !(user.pool_enabled ?? false)
    try {
        await updateUserPermissions(user.id, { pool_enabled: newValue })
        user.pool_enabled = newValue
    } catch (e: any) {
        alert(e.data?.detail || '操作失败')
    }
}

const handleSearch = () => {
    page.value = 1
    loadUsers()
}

const changeLimit = (newLimit: number) => {
    limit.value = newLimit
    page.value = 1
    loadUsers()
}

const totalPages = computed(() => Math.ceil(total.value / limit.value))

onMounted(loadUsers)
</script>

<template>
    <div class="h-full flex flex-col">
        <!-- 固定头部 -->
        <div class="shrink-0 space-y-6 pb-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">用户权限管理</h2>
            
            <!-- 搜索栏 -->
            <div class="flex items-center gap-3">
                <div class="relative flex-1 max-w-md">
                    <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input 
                        v-model="searchQuery" 
                        @keyup.enter="handleSearch" 
                        type="text" 
                        placeholder="搜索邮箱或名称..."
                        class="w-full pl-12 pr-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white placeholder-gray-400"
                    >
                </div>
                <button @click="handleSearch" class="px-5 py-3 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20">
                    搜索
                </button>
                <button @click="loadUsers" class="p-3 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors" title="刷新">
                    <RefreshCw class="w-5 h-5" :class="{ 'animate-spin': loading }" />
                </button>
            </div>
        </div>

        <!-- 表格容器 -->
        <div class="flex-1 min-h-0 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden flex flex-col">
            <!-- 固定表头 -->
            <div class="shrink-0 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                <div class="grid grid-cols-12 gap-4 px-6 py-3">
                    <div class="col-span-5 text-xs font-bold text-gray-500 uppercase tracking-wider">用户</div>
                    <div class="col-span-2 text-xs font-bold text-gray-500 uppercase tracking-wider">角色</div>
                    <div class="col-span-2 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">账号池</div>
                    <div class="col-span-3 text-xs font-bold text-gray-500 uppercase tracking-wider">注册时间</div>
                </div>
            </div>

            <!-- 可滚动内容 -->
            <div class="flex-1 overflow-y-auto custom-scrollbar">
                <!-- 骨架屏 -->
                <div v-if="loading" class="divide-y divide-gray-100 dark:divide-gray-800">
                    <div v-for="i in 8" :key="i" class="grid grid-cols-12 gap-4 px-6 py-4 items-center animate-pulse">
                        <div class="col-span-5 space-y-2">
                            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48"></div>
                        </div>
                        <div class="col-span-2">
                            <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                        </div>
                        <div class="col-span-2 flex justify-center">
                            <div class="w-12 h-7 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                        </div>
                        <div class="col-span-3">
                            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                        </div>
                    </div>
                </div>
                <div v-else-if="users.length === 0" class="p-12 text-center text-gray-500">暂无用户</div>
                <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
                    <div v-for="user in users" :key="user.id" 
                        class="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors items-center">
                        <!-- 用户信息 -->
                        <div class="col-span-5">
                            <div class="font-medium text-gray-900 dark:text-white truncate">{{ user.display_name || '-' }}</div>
                            <div class="text-sm text-gray-500 truncate">{{ user.email }}</div>
                        </div>
                        <!-- 角色 -->
                        <div class="col-span-2">
                            <select :value="user.role" @change="updateRole(user, ($event.target as HTMLSelectElement).value)"
                                class="px-2 py-1 text-xs font-medium rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 outline-none cursor-pointer"
                                :class="user.role === 'admin' ? 'text-purple-700 dark:text-purple-400' : 'text-gray-600 dark:text-gray-400'">
                                <option value="user">用户</option>
                                <option value="admin">管理员</option>
                            </select>
                        </div>
                        <!-- 账号池开关 -->
                        <div class="col-span-2 flex justify-center">
                            <CommonToggle :model-value="user.pool_enabled ?? false" @update:model-value="togglePool(user)" />
                        </div>
                        <!-- 注册时间 -->
                        <div class="col-span-3 text-sm text-gray-500">
                            {{ user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) : '-' }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- 分页 -->
            <div v-if="total > 0" class="shrink-0 flex items-center justify-between px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/30">
                <div class="flex items-center gap-4">
                    <span class="text-sm text-gray-500">共 {{ total }} 个用户</span>
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-gray-500">每页</span>
                        <select v-model="limit" @change="changeLimit(Number(limit))"
                            class="px-2 py-1 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 outline-none">
                            <option v-for="opt in limitOptions" :key="opt" :value="opt">{{ opt }}</option>
                        </select>
                        <span class="text-sm text-gray-500">条</span>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button @click="page--; loadUsers()" :disabled="page <= 1"
                        class="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        上一页
                    </button>
                    <span class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400">{{ page }} / {{ totalPages }}</span>
                    <button @click="page++; loadUsers()" :disabled="page >= totalPages"
                        class="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        下一页
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #4b5563;
}
</style>