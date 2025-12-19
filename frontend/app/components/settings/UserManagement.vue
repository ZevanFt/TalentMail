<script setup lang="ts">
import { Search, RefreshCw, Crown, Plus, Trash2, AlertTriangle } from 'lucide-vue-next'

const { getUsers, updateUserPermissions, adminCreateUser, adminDeleteUser, getPlans } = useApi()
const config = useConfig()

interface Plan {
    id: number
    name: string
}

interface User {
    id: number
    email: string
    display_name: string | null
    role: string
    pool_enabled: boolean | null
    created_at: string
    plan_name: string | null
    plan_id: number | null
    subscription_expires_at: string | null
}

const users = ref<User[]>([])
const plans = ref<Plan[]>([])
const total = ref(0)
const loading = ref(false)
const searchQuery = ref('')
const page = ref(1)
const limit = ref(20)
const limitOptions = [10, 20, 50, 100]

// 套餐修改弹窗
const showPlanModal = ref(false)
const editingUser = ref<User | null>(null)
const selectedPlanId = ref<number>(0)
const subscriptionDays = ref(30)

// 创建用户弹窗
const showCreateModal = ref(false)
const creating = ref(false)
const createForm = reactive({
    emailPrefix: '',
    password: '',
    displayName: '',
    role: 'user',
    poolEnabled: false,
    planId: 0,
    subscriptionDays: 30
})

// 删除用户弹窗
const showDeleteModal = ref(false)
const userToDelete = ref<User | null>(null)
const deleting = ref(false)

const loadPlans = async () => {
    try {
        plans.value = await getPlans()
    } catch (e) {
        console.error('加载套餐失败', e)
    }
}

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
        if (newRole === 'admin') {
            user.pool_enabled = true
            user.plan_name = '管理员 (无限)'
        }
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

const openPlanModal = (user: User) => {
    if (user.role === 'admin') return // 管理员不能修改套餐
    editingUser.value = user
    selectedPlanId.value = user.plan_id || (plans.value[0]?.id || 0)
    subscriptionDays.value = 30
    showPlanModal.value = true
}

const savePlan = async () => {
    if (!editingUser.value || !selectedPlanId.value) return
    try {
        const res = await updateUserPermissions(editingUser.value.id, {
            plan_id: selectedPlanId.value,
            subscription_days: subscriptionDays.value
        })
        // 更新本地数据
        editingUser.value.plan_name = res.plan_name
        editingUser.value.plan_id = res.plan_id
        editingUser.value.subscription_expires_at = res.subscription_expires_at
        showPlanModal.value = false
    } catch (e: any) {
        alert(e.data?.detail || '操作失败')
    }
}

const handleSearch = () => {
    page.value = 1
    loadUsers()
}

// 创建用户
const openCreateModal = () => {
    createForm.emailPrefix = ''
    createForm.password = ''
    createForm.displayName = ''
    createForm.role = 'user'
    createForm.poolEnabled = false
    createForm.planId = plans.value[0]?.id || 0
    createForm.subscriptionDays = 30
    showCreateModal.value = true
}

const handleCreateUser = async () => {
    if (!createForm.emailPrefix.trim()) {
        alert('请输入邮箱前缀')
        return
    }
    if (!createForm.password || createForm.password.length < 6) {
        alert('密码至少6位')
        return
    }
    
    creating.value = true
    try {
        await adminCreateUser({
            email_prefix: createForm.emailPrefix.toLowerCase().trim(),
            password: createForm.password,
            display_name: createForm.displayName || undefined,
            role: createForm.role,
            pool_enabled: createForm.poolEnabled,
            plan_id: createForm.planId || undefined,
            subscription_days: createForm.subscriptionDays
        })
        showCreateModal.value = false
        await loadUsers()
    } catch (e: any) {
        alert(e.data?.detail || '创建失败')
    } finally {
        creating.value = false
    }
}

// 删除用户
const confirmDeleteUser = (user: User) => {
    userToDelete.value = user
    showDeleteModal.value = true
}

const handleDeleteUser = async () => {
    if (!userToDelete.value) return
    deleting.value = true
    try {
        await adminDeleteUser(userToDelete.value.id)
        showDeleteModal.value = false
        userToDelete.value = null
        await loadUsers()
    } catch (e: any) {
        alert(e.data?.detail || '删除失败')
    } finally {
        deleting.value = false
    }
}

const changeLimit = (newLimit: number) => {
    limit.value = newLimit
    page.value = 1
    loadUsers()
}

const formatDate = (date: string | null) => {
    if (!date) return '-'
    return new Date(date).toLocaleDateString('zh-CN')
}

const totalPages = computed(() => Math.ceil(total.value / limit.value))

onMounted(async () => {
    await loadPlans()
    await loadUsers()
})
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
                <button @click="openCreateModal" class="px-5 py-3 bg-green-600 text-white text-sm font-medium rounded-xl hover:bg-green-700 transition-colors shadow-sm flex items-center gap-2">
                    <Plus class="w-4 h-4" />
                    创建用户
                </button>
            </div>
        </div>

        <!-- 表格容器 -->
        <div class="flex-1 min-h-0 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden flex flex-col">
            <!-- 固定表头 -->
            <div class="shrink-0 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                <div class="grid grid-cols-12 gap-4 px-6 py-3">
                    <div class="col-span-3 text-xs font-bold text-gray-500 uppercase tracking-wider">用户</div>
                    <div class="col-span-2 text-xs font-bold text-gray-500 uppercase tracking-wider">角色</div>
                    <div class="col-span-2 text-xs font-bold text-gray-500 uppercase tracking-wider">套餐</div>
                    <div class="col-span-2 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">账号池</div>
                    <div class="col-span-2 text-xs font-bold text-gray-500 uppercase tracking-wider">注册时间</div>
                    <div class="col-span-1 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">操作</div>
                </div>
            </div>

            <!-- 可滚动内容 -->
            <div class="flex-1 overflow-y-auto custom-scrollbar">
                <!-- 骨架屏 -->
                <div v-if="loading" class="divide-y divide-gray-100 dark:divide-gray-800">
                    <div v-for="i in 8" :key="i" class="grid grid-cols-12 gap-4 px-6 py-4 items-center animate-pulse">
                        <div class="col-span-3 space-y-2">
                            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48"></div>
                        </div>
                        <div class="col-span-2">
                            <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                        </div>
                        <div class="col-span-2">
                            <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                        </div>
                        <div class="col-span-2 flex justify-center">
                            <div class="w-12 h-7 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                        </div>
                        <div class="col-span-2">
                            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                        </div>
                    </div>
                </div>
                <div v-else-if="users.length === 0" class="p-12 text-center text-gray-500">暂无用户</div>
                <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
                    <div v-for="user in users" :key="user.id"
                        class="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors items-center">
                        <!-- 用户信息 -->
                        <div class="col-span-3">
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
                        <!-- 套餐 -->
                        <div class="col-span-2">
                            <button
                                @click="openPlanModal(user)"
                                :disabled="user.role === 'admin'"
                                class="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-lg transition-colors"
                                :class="user.role === 'admin'
                                    ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 cursor-default'
                                    : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 cursor-pointer'"
                            >
                                <Crown v-if="user.role === 'admin'" class="w-3 h-3" />
                                {{ user.plan_name || 'Free' }}
                            </button>
                            <div v-if="user.subscription_expires_at && user.role !== 'admin'" class="text-xs text-gray-400 mt-0.5">
                                {{ formatDate(user.subscription_expires_at) }} 到期
                            </div>
                        </div>
                        <!-- 账号池开关 -->
                        <div class="col-span-2 flex justify-center">
                            <CommonToggle :model-value="user.pool_enabled ?? false" @update:model-value="togglePool(user)" />
                        </div>
                        <!-- 注册时间 -->
                        <div class="col-span-2 text-sm text-gray-500">
                            {{ formatDate(user.created_at) }}
                        </div>
                        <!-- 操作 -->
                        <div class="col-span-1 flex justify-center">
                            <button
                                @click="confirmDeleteUser(user)"
                                class="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                title="删除用户"
                            >
                                <Trash2 class="w-4 h-4" />
                            </button>
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

        <!-- 套餐修改弹窗 -->
        <CommonModal v-model="showPlanModal" title="修改用户套餐">
            <div v-if="editingUser" class="space-y-4">
                <div class="text-sm text-gray-500">
                    用户：<span class="font-medium text-gray-900 dark:text-white">{{ editingUser.email }}</span>
                </div>
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">选择套餐</label>
                    <select v-model="selectedPlanId" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary">
                        <option v-for="plan in plans" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
                    </select>
                </div>
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">订阅天数</label>
                    <input v-model.number="subscriptionDays" type="number" min="1" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary">
                    <p class="text-xs text-gray-400">如果用户已有该套餐的订阅，将在现有到期时间基础上累加</p>
                </div>
            </div>
            <template #footer>
                <button @click="showPlanModal = false" class="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">取消</button>
                <button @click="savePlan" class="px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors">保存</button>
            </template>
        </CommonModal>

        <!-- 创建用户弹窗 -->
        <CommonModal v-model="showCreateModal" title="创建新用户">
            <div class="space-y-4">
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">邮箱地址 *</label>
                    <div class="flex">
                        <input
                            v-model="createForm.emailPrefix"
                            type="text"
                            placeholder="输入邮箱前缀"
                            class="flex-1 min-w-0 px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 border-r-0 rounded-l-lg text-sm outline-none focus:border-primary"
                        >
                        <div class="px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-r-lg text-gray-500 text-sm flex items-center">
                            {{ config.emailDomain }}
                        </div>
                    </div>
                    <p class="text-xs text-gray-400">管理员创建用户可使用保留前缀</p>
                </div>
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">密码 *</label>
                    <input
                        v-model="createForm.password"
                        type="password"
                        placeholder="至少6位"
                        class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary"
                    >
                </div>
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">显示名称</label>
                    <input
                        v-model="createForm.displayName"
                        type="text"
                        placeholder="可选"
                        class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary"
                    >
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">角色</label>
                        <select v-model="createForm.role" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary">
                            <option value="user">普通用户</option>
                            <option value="admin">管理员</option>
                        </select>
                    </div>
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">套餐</label>
                        <select v-model="createForm.planId" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary">
                            <option v-for="plan in plans" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
                        </select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">订阅天数</label>
                        <input
                            v-model.number="createForm.subscriptionDays"
                            type="number"
                            min="1"
                            class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary"
                        >
                    </div>
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">账号池权限</label>
                        <div class="flex items-center h-[38px]">
                            <CommonToggle v-model="createForm.poolEnabled" />
                            <span class="ml-2 text-sm text-gray-500">{{ createForm.poolEnabled ? '开启' : '关闭' }}</span>
                        </div>
                    </div>
                </div>
            </div>
            <template #footer>
                <button @click="showCreateModal = false" class="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors" :disabled="creating">取消</button>
                <button @click="handleCreateUser" class="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors" :disabled="creating">
                    {{ creating ? '创建中...' : '创建用户' }}
                </button>
            </template>
        </CommonModal>

        <!-- 删除用户确认弹窗 -->
        <CommonModal v-model="showDeleteModal" title="确认删除用户">
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                    <AlertTriangle class="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <div>
                    <p class="text-gray-900 dark:text-white font-medium mb-2">确定要删除此用户吗？</p>
                    <p class="text-sm text-gray-500">
                        用户 <span class="font-medium text-gray-700 dark:text-gray-300">{{ userToDelete?.email }}</span>
                        将被永久删除，包括其所有邮件、订阅等数据。此操作不可恢复。
                    </p>
                </div>
            </div>
            <template #footer>
                <button @click="showDeleteModal = false" class="px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors" :disabled="deleting">取消</button>
                <button @click="handleDeleteUser" class="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors" :disabled="deleting">
                    {{ deleting ? '删除中...' : '确认删除' }}
                </button>
            </template>
        </CommonModal>
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