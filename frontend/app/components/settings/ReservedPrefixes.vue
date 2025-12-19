<script setup lang="ts">
import { Plus, Trash2, Edit2, Search, Filter, AlertTriangle, Check, X, Tag, User } from 'lucide-vue-next'

const { getReservedPrefixes, createReservedPrefix, updateReservedPrefix, deleteReservedPrefix, getReservedPrefixCategories } = useApi()

interface ReservedPrefix {
    id: number
    prefix: string
    category: string
    description: string | null
    is_active: boolean
    is_used?: boolean
    used_by?: string | null
    created_at: string | null
    updated_at: string | null
}

const prefixes = ref<ReservedPrefix[]>([])
const categories = ref<string[]>([])
const loading = ref(false)
const totalCount = ref(0)

// 分类统计
const categoryStats = ref<Record<string, number>>({
    system: 0,
    business: 0,
    test: 0,
    security: 0,
    common: 0
})

// 筛选
const searchQuery = ref('')
const filterCategory = ref('')
const filterActive = ref<boolean | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const pageSizeOptions = [10, 20, 50, 100]

// 创建/编辑弹窗
const showEditModal = ref(false)
const editingPrefix = ref<ReservedPrefix | null>(null)
const saving = ref(false)
const formData = reactive({
    prefix: '',
    category: 'common',
    description: '',
    is_active: true
})

// 删除确认弹窗
const showDeleteModal = ref(false)
const prefixToDelete = ref<ReservedPrefix | null>(null)
const deleting = ref(false)

// 分类颜色映射
const categoryColors: Record<string, string> = {
    system: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
    business: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    test: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
    security: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
    common: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
}

// 分类中文名
const categoryNames: Record<string, string> = {
    system: '系统',
    business: '业务',
    test: '测试',
    security: '安全',
    common: '常见'
}

const loadPrefixes = async () => {
    loading.value = true
    try {
        const result = await getReservedPrefixes(
            filterCategory.value || undefined,
            filterActive.value === null ? undefined : filterActive.value,
            searchQuery.value || undefined,
            currentPage.value,
            pageSize.value
        )
        prefixes.value = result.items as ReservedPrefix[]
        totalCount.value = result.total
    } catch (e) {
        console.error('加载保留前缀失败', e)
    } finally {
        loading.value = false
    }
}

const loadCategories = async () => {
    try {
        categories.value = await getReservedPrefixCategories()
    } catch (e) {
        console.error('加载分类失败', e)
    }
}

const loadCategoryStats = async () => {
    // 获取每个分类的数量
    for (const cat of ['system', 'business', 'test', 'security', 'common']) {
        try {
            const result = await getReservedPrefixes(cat, undefined, undefined, 1, 1)
            categoryStats.value[cat] = result.total
        } catch (e) {
            categoryStats.value[cat] = 0
        }
    }
}

const openCreateModal = () => {
    editingPrefix.value = null
    formData.prefix = ''
    formData.category = 'common'
    formData.description = ''
    formData.is_active = true
    showEditModal.value = true
}

const openEditModal = (prefix: ReservedPrefix) => {
    editingPrefix.value = prefix
    formData.prefix = prefix.prefix
    formData.category = prefix.category
    formData.description = prefix.description || ''
    formData.is_active = prefix.is_active
    showEditModal.value = true
}

const handleSave = async () => {
    if (!formData.prefix.trim()) {
        alert('请输入前缀')
        return
    }
    
    saving.value = true
    try {
        if (editingPrefix.value) {
            await updateReservedPrefix(editingPrefix.value.id, {
                prefix: formData.prefix.toLowerCase().trim(),
                category: formData.category,
                description: formData.description || undefined,
                is_active: formData.is_active
            })
        } else {
            await createReservedPrefix({
                prefix: formData.prefix.toLowerCase().trim(),
                category: formData.category,
                description: formData.description || undefined
            })
        }
        showEditModal.value = false
        await loadPrefixes()
        await loadCategories()
    } catch (e: any) {
        alert(e.data?.detail || '保存失败')
    } finally {
        saving.value = false
    }
}

const confirmDelete = (prefix: ReservedPrefix) => {
    prefixToDelete.value = prefix
    showDeleteModal.value = true
}

const handleDelete = async () => {
    if (!prefixToDelete.value) return
    deleting.value = true
    try {
        await deleteReservedPrefix(prefixToDelete.value.id)
        showDeleteModal.value = false
        prefixToDelete.value = null
        await loadPrefixes()
    } catch (e: any) {
        alert(e.data?.detail || '删除失败')
    } finally {
        deleting.value = false
    }
}

const toggleActive = async (prefix: ReservedPrefix) => {
    try {
        await updateReservedPrefix(prefix.id, {
            is_active: !prefix.is_active
        })
        await loadPrefixes()
    } catch (e: any) {
        alert(e.data?.detail || '更新失败')
    }
}

const handleSearch = () => {
    currentPage.value = 1
    loadPrefixes()
}

const handleFilterChange = () => {
    currentPage.value = 1
    loadPrefixes()
}

const formatDate = (date: string | null) => {
    if (!date) return '-'
    return new Date(date).toLocaleDateString('zh-CN')
}

// 计算总页数
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// 切换每页条数
const handlePageSizeChange = () => {
    currentPage.value = 1
    loadPrefixes()
}

onMounted(() => {
    loadPrefixes()
    loadCategories()
    loadCategoryStats()
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">保留邮箱前缀管理</h2>

        <!-- 操作栏 -->
        <div class="card p-5">
            <div class="flex flex-col lg:flex-row gap-4 lg:items-center lg:justify-between">
                <!-- 搜索和筛选 -->
                <div class="flex flex-wrap items-center gap-3">
                    <div class="relative">
                        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none z-10" />
                        <input
                            v-model="searchQuery"
                            @keyup.enter="handleSearch"
                            type="text"
                            class="search-input w-52"
                            placeholder="搜索前缀..."
                        >
                    </div>
                    <select v-model="filterCategory" @change="handleFilterChange" class="input-field w-28">
                        <option value="">全部分类</option>
                        <option v-for="cat in categories" :key="cat" :value="cat">
                            {{ categoryNames[cat] || cat }}
                        </option>
                    </select>
                    <select v-model="filterActive" @change="handleFilterChange" class="input-field w-24">
                        <option :value="null">全部</option>
                        <option :value="true">启用</option>
                        <option :value="false">禁用</option>
                    </select>
                    <button @click="handleSearch" class="btn-icon" title="搜索">
                        <Filter class="w-4 h-4" />
                    </button>
                </div>
                
                <!-- 创建按钮 -->
                <button @click="openCreateModal" class="btn-primary flex items-center gap-2 shrink-0">
                    <Plus class="w-4 h-4" />
                    添加前缀
                </button>
            </div>
        </div>

        <!-- 统计信息 -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div v-for="cat in ['system', 'business', 'test', 'security', 'common']" :key="cat"
                class="card p-4 flex items-center gap-3 cursor-pointer hover:border-primary/50 transition-colors"
                @click="filterCategory = cat; handleFilterChange()">
                <div :class="['w-10 h-10 rounded-lg flex items-center justify-center', categoryColors[cat]]">
                    <Tag class="w-5 h-5" />
                </div>
                <div>
                    <div class="text-2xl font-bold text-gray-900 dark:text-white">
                        {{ categoryStats[cat] }}
                    </div>
                    <div class="text-xs text-gray-500">{{ categoryNames[cat] }}</div>
                </div>
            </div>
        </div>

        <!-- 前缀列表 -->
        <div class="card overflow-hidden">
            <div v-if="loading" class="p-8 text-center text-gray-500">加载中...</div>
            <div v-else-if="prefixes.length === 0" class="p-8 text-center text-gray-500">暂无保留前缀</div>
            <div v-else class="table-container">
                <table class="w-full">
                    <thead class="sticky top-0 z-10">
                        <tr>
                            <th class="th">前缀</th>
                            <th class="th">分类</th>
                            <th class="th">描述</th>
                            <th class="th">使用状态</th>
                            <th class="th">启用状态</th>
                            <th class="th">创建时间</th>
                            <th class="th">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                        <tr v-for="prefix in prefixes" :key="prefix.id"
                            class="hover:bg-gray-50 dark:hover:bg-gray-800/30"
                            :class="{ 'opacity-50': !prefix.is_active }">
                            <td class="td">
                                <code class="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono">
                                    {{ prefix.prefix }}
                                </code>
                            </td>
                            <td class="td">
                                <span :class="['px-2 py-0.5 rounded-full text-xs', categoryColors[prefix.category] || categoryColors.common]">
                                    {{ categoryNames[prefix.category] || prefix.category }}
                                </span>
                            </td>
                            <td class="td text-gray-500 max-w-xs truncate">
                                {{ prefix.description || '-' }}
                            </td>
                            <td class="td">
                                <div v-if="prefix.is_used" class="flex items-center gap-1.5">
                                    <User class="w-3.5 h-3.5 text-orange-500" />
                                    <span class="text-xs text-orange-600 dark:text-orange-400" :title="prefix.used_by || ''">
                                        已使用
                                    </span>
                                </div>
                                <span v-else class="text-xs text-gray-400">未使用</span>
                            </td>
                            <td class="td">
                                <button
                                    @click="toggleActive(prefix)"
                                    :class="[
                                        'px-2 py-0.5 rounded-full text-xs transition-colors',
                                        prefix.is_active
                                            ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50'
                                            : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700'
                                    ]"
                                >
                                    {{ prefix.is_active ? '启用' : '禁用' }}
                                </button>
                            </td>
                            <td class="td text-gray-500">{{ formatDate(prefix.created_at) }}</td>
                            <td class="td">
                                <div class="flex gap-2">
                                    <button @click="openEditModal(prefix)" class="icon-btn" title="编辑">
                                        <Edit2 class="w-4 h-4" />
                                    </button>
                                    <button @click="confirmDelete(prefix)" class="icon-btn text-red-500" title="删除">
                                        <Trash2 class="w-4 h-4" />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- 分页 -->
            <div class="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-800">
                <div class="flex items-center gap-4">
                    <span class="text-sm text-gray-500">
                        共 {{ totalCount }} 条记录
                    </span>
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-gray-500">每页</span>
                        <select v-model="pageSize" @change="handlePageSizeChange" class="input-field text-sm py-1 px-2 w-20">
                            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }} 条</option>
                        </select>
                    </div>
                </div>
                <div v-if="totalPages > 1" class="flex gap-2">
                    <button
                        @click="currentPage--; loadPrefixes()"
                        :disabled="currentPage <= 1"
                        class="btn-secondary text-sm px-3 py-1"
                    >
                        上一页
                    </button>
                    <span class="px-3 py-1 text-sm text-gray-600 dark:text-gray-400">
                        {{ currentPage }} / {{ totalPages }}
                    </span>
                    <button
                        @click="currentPage++; loadPrefixes()"
                        :disabled="currentPage >= totalPages"
                        class="btn-secondary text-sm px-3 py-1"
                    >
                        下一页
                    </button>
                </div>
            </div>
        </div>

        <!-- 创建/编辑弹窗 -->
        <CommonModal v-model="showEditModal" :title="editingPrefix ? '编辑保留前缀' : '添加保留前缀'">
            <div class="space-y-4">
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">前缀 *</label>
                    <input 
                        v-model="formData.prefix" 
                        type="text" 
                        class="input-field w-full" 
                        placeholder="例如: admin, support, noreply"
                        :disabled="!!editingPrefix"
                    >
                    <p class="text-xs text-gray-500">前缀将自动转为小写，创建后不可修改</p>
                </div>
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">分类 *</label>
                    <select v-model="formData.category" class="input-field w-full">
                        <option value="system">系统 - 系统级别保留</option>
                        <option value="business">业务 - 业务相关保留</option>
                        <option value="test">测试 - 测试用途保留</option>
                        <option value="security">安全 - 安全相关保留</option>
                        <option value="common">常见 - 常见名称保留</option>
                    </select>
                </div>
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">描述</label>
                    <input 
                        v-model="formData.description" 
                        type="text" 
                        class="input-field w-full" 
                        placeholder="可选，说明保留原因"
                    >
                </div>
                <div class="flex items-center gap-3">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">启用状态</label>
                    <button 
                        @click="formData.is_active = !formData.is_active"
                        :class="[
                            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                            formData.is_active ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                        ]"
                    >
                        <span 
                            :class="[
                                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                                formData.is_active ? 'translate-x-6' : 'translate-x-1'
                            ]"
                        />
                    </button>
                    <span class="text-sm text-gray-500">{{ formData.is_active ? '启用' : '禁用' }}</span>
                </div>
            </div>
            <template #footer>
                <button @click="showEditModal = false" class="btn-secondary" :disabled="saving">取消</button>
                <button @click="handleSave" class="btn-primary" :disabled="saving">
                    {{ saving ? '保存中...' : '保存' }}
                </button>
            </template>
        </CommonModal>

        <!-- 删除确认弹窗 -->
        <CommonModal v-model="showDeleteModal" title="确认删除">
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                    <AlertTriangle class="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <div>
                    <p class="text-gray-900 dark:text-white font-medium mb-2">确定要删除此保留前缀吗？</p>
                    <p class="text-sm text-gray-500">
                        前缀 <code class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono">{{ prefixToDelete?.prefix }}</code>
                        将被永久删除，删除后用户将可以使用此前缀注册邮箱。
                    </p>
                </div>
            </div>
            <template #footer>
                <button @click="showDeleteModal = false" class="btn-secondary" :disabled="deleting">取消</button>
                <button @click="handleDelete" class="btn-danger" :disabled="deleting">
                    {{ deleting ? '删除中...' : '确认删除' }}
                </button>
            </template>
        </CommonModal>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark;
}

.input-field {
    @apply px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white;
}

.btn-primary {
    @apply px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20 disabled:opacity-50;
}

.btn-secondary {
    @apply px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50;
}

.btn-danger {
    @apply px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors shadow-sm shadow-red-600/20 disabled:opacity-50;
}

.table-container {
    @apply max-h-[500px] overflow-y-auto;
}

.th {
    @apply px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider;
    background-color: #f9fafb;
}

:deep(.dark) .th,
.dark .th {
    background-color: #1f2937;
}

.td {
    @apply px-4 py-3 text-sm text-gray-900 dark:text-white;
}

.icon-btn {
    @apply p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500;
}

.btn-icon {
    @apply p-2.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors;
}

.search-input {
    @apply py-2 pr-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white;
    padding-left: 2.5rem !important;
}
</style>