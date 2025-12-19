<script setup lang="ts">
import { Plus, Trash2, Copy, Check, Users, AlertTriangle } from 'lucide-vue-next'

const { getInviteCodes, createInviteCode, deleteInviteCode, getInviteCodeUsages } = useApi()

interface InviteCode {
    id: number
    code: string
    max_uses: number
    used_count: number
    expires_at: string | null
    created_at: string
    is_active: boolean
    deleted_at: string | null
}

interface InviteCodeUsage {
    id: number
    user_email: string
    used_at: string
}

const codes = ref<InviteCode[]>([])
const loading = ref(false)
const creating = ref(false)
const copiedId = ref<number | null>(null)

// 使用详情弹窗
const showUsageModal = ref(false)
const selectedCode = ref<InviteCode | null>(null)
const usages = ref<InviteCodeUsage[]>([])
const loadingUsages = ref(false)

// 删除确认弹窗
const showDeleteModal = ref(false)
const codeToDelete = ref<InviteCode | null>(null)
const deleting = ref(false)

// 创建表单
const newCode = reactive({
    maxUses: 1,
    expiresDays: 7
})

const loadCodes = async () => {
    loading.value = true
    try {
        codes.value = await getInviteCodes()
    } catch (e) {
        console.error('加载邀请码失败', e)
    } finally {
        loading.value = false
    }
}

const handleCreate = async () => {
    creating.value = true
    try {
        await createInviteCode(newCode.maxUses, newCode.expiresDays || undefined)
        await loadCodes()
    } catch (e: any) {
        alert(e.data?.detail || '创建失败')
    } finally {
        creating.value = false
    }
}

const confirmDelete = (code: InviteCode) => {
    codeToDelete.value = code
    showDeleteModal.value = true
}

const handleDelete = async () => {
    if (!codeToDelete.value) return
    deleting.value = true
    try {
        await deleteInviteCode(codeToDelete.value.id)
        await loadCodes()
        showDeleteModal.value = false
        codeToDelete.value = null
    } catch (e: any) {
        alert(e.data?.detail || '删除失败')
    } finally {
        deleting.value = false
    }
}

const copyCode = async (code: InviteCode) => {
    await navigator.clipboard.writeText(code.code)
    copiedId.value = code.id
    setTimeout(() => copiedId.value = null, 2000)
}

const formatDate = (date: string | null) => {
    if (!date) return '永不过期'
    return new Date(date).toLocaleDateString('zh-CN')
}

const formatDateTime = (date: string) => {
    return new Date(date).toLocaleString('zh-CN')
}

const showUsages = async (code: InviteCode) => {
    selectedCode.value = code
    showUsageModal.value = true
    loadingUsages.value = true
    try {
        usages.value = await getInviteCodeUsages(code.id)
    } catch (e) {
        console.error('加载使用记录失败', e)
        usages.value = []
    } finally {
        loadingUsages.value = false
    }
}

// 判断邀请码状态
const getCodeStatus = (code: InviteCode) => {
    if (code.deleted_at) return { text: '已删除', class: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500' }
    if (code.expires_at && new Date(code.expires_at) < new Date()) return { text: '已过期', class: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' }
    if (code.max_uses > 0 && code.used_count >= code.max_uses) return { text: '已用完', class: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400' }
    return { text: '可用', class: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' }
}

onMounted(loadCodes)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">邀请码管理</h2>

        <!-- 创建新邀请码 -->
        <div class="card p-6">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">创建邀请码</h3>
            <div class="flex flex-wrap gap-4 items-end">
                <div class="space-y-1">
                    <label class="text-sm text-gray-500">最大使用次数</label>
                    <input v-model.number="newCode.maxUses" type="number" min="0" class="input-field w-32"
                        placeholder="0=无限">
                </div>
                <div class="space-y-1">
                    <label class="text-sm text-gray-500">有效天数</label>
                    <input v-model.number="newCode.expiresDays" type="number" min="0" class="input-field w-32"
                        placeholder="0=永不">
                </div>
                <button @click="handleCreate" :disabled="creating" class="btn-primary flex items-center gap-2">
                    <Plus class="w-4 h-4" />
                    {{ creating ? '创建中...' : '创建' }}
                </button>
            </div>
        </div>

        <!-- 邀请码列表 -->
        <div class="card overflow-hidden">
            <div v-if="loading" class="p-8 text-center text-gray-500">加载中...</div>
            <div v-else-if="codes.length === 0" class="p-8 text-center text-gray-500">暂无邀请码</div>
            <table v-else class="w-full">
                <thead class="bg-gray-50 dark:bg-gray-800/50">
                    <tr>
                        <th class="th">邀请码</th>
                        <th class="th">使用情况</th>
                        <th class="th">过期时间</th>
                        <th class="th">操作</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                    <tr v-for="code in codes" :key="code.id"
                        class="hover:bg-gray-50 dark:hover:bg-gray-800/30"
                        :class="{ 'opacity-50': code.deleted_at }">
                        <td class="td">
                            <div class="flex items-center gap-2">
                                <code class="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono"
                                    :class="{ 'line-through': code.deleted_at }">{{ code.code }}</code>
                                <span :class="['px-2 py-0.5 rounded-full text-xs', getCodeStatus(code).class]">
                                    {{ getCodeStatus(code).text }}
                                </span>
                            </div>
                        </td>
                        <td class="td">
                            <button
                                v-if="code.used_count > 0"
                                @click="showUsages(code)"
                                class="inline-flex items-center gap-1 hover:text-primary transition-colors"
                                :class="code.max_uses > 0 && code.used_count >= code.max_uses ? 'text-red-500' : ''"
                                title="点击查看使用详情"
                            >
                                {{ code.used_count }} / {{ code.max_uses || '∞' }}
                                <Users class="w-3.5 h-3.5" />
                            </button>
                            <span v-else :class="code.max_uses > 0 && code.used_count >= code.max_uses ? 'text-red-500' : ''">
                                {{ code.used_count }} / {{ code.max_uses || '∞' }}
                            </span>
                        </td>
                        <td class="td text-gray-500">{{ formatDate(code.expires_at) }}</td>
                        <td class="td">
                            <div class="flex gap-2">
                                <button @click="copyCode(code)" class="icon-btn" title="复制">
                                    <Check v-if="copiedId === code.id" class="w-4 h-4 text-green-500" />
                                    <Copy v-else class="w-4 h-4" />
                                </button>
                                <button v-if="!code.deleted_at" @click="confirmDelete(code)" class="icon-btn text-red-500" title="删除">
                                    <Trash2 class="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 使用详情弹窗 -->
        <CommonModal v-model="showUsageModal" :title="`邀请码使用记录 - ${selectedCode?.code}`">
            <div v-if="loadingUsages" class="py-8 text-center text-gray-500">加载中...</div>
            <div v-else-if="usages.length === 0" class="py-8 text-center text-gray-500">暂无使用记录</div>
            <div v-else class="space-y-3 max-h-80 overflow-y-auto">
                <div v-for="usage in usages" :key="usage.id"
                    class="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div class="font-medium text-gray-900 dark:text-white">{{ usage.user_email }}</div>
                    <div class="text-sm text-gray-500">{{ formatDateTime(usage.used_at) }}</div>
                </div>
            </div>
            <template #footer>
                <button @click="showUsageModal = false" class="btn-primary">关闭</button>
            </template>
        </CommonModal>

        <!-- 删除确认弹窗 -->
        <CommonModal v-model="showDeleteModal" title="确认删除">
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                    <AlertTriangle class="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <div>
                    <p class="text-gray-900 dark:text-white font-medium mb-2">确定要删除此邀请码吗？</p>
                    <p class="text-sm text-gray-500">
                        邀请码 <code class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono">{{ codeToDelete?.code }}</code>
                        将被标记为已删除，但历史使用记录会保留。
                    </p>
                    <p v-if="codeToDelete?.used_count" class="text-sm text-gray-500 mt-2">
                        此邀请码已被使用 <span class="font-medium text-gray-700 dark:text-gray-300">{{ codeToDelete.used_count }}</span> 次。
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

.th {
    @apply px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider;
}

.td {
    @apply px-4 py-3 text-sm text-gray-900 dark:text-white;
}

.icon-btn {
    @apply p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500;
}
</style>