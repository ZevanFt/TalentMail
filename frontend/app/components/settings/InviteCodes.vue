<script setup lang="ts">
import { Plus, Trash2, Copy, Check } from 'lucide-vue-next'

const { getInviteCodes, createInviteCode, deleteInviteCode } = useApi()

interface InviteCode {
    id: number
    code: string
    max_uses: number
    used_count: number
    expires_at: string | null
    created_at: string
    is_active: boolean
}

const codes = ref<InviteCode[]>([])
const loading = ref(false)
const creating = ref(false)
const copiedId = ref<number | null>(null)

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

const handleDelete = async (id: number) => {
    if (!confirm('确定删除此邀请码？')) return
    try {
        await deleteInviteCode(id)
        await loadCodes()
    } catch (e) {
        console.error('删除失败', e)
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
                    <tr v-for="code in codes" :key="code.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                        <td class="td">
                            <code
                                class="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono">{{ code.code }}</code>
                        </td>
                        <td class="td">
                            <span :class="code.max_uses > 0 && code.used_count >= code.max_uses ? 'text-red-500' : ''">
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
                                <button @click="handleDelete(code.id)" class="icon-btn text-red-500" title="删除">
                                    <Trash2 class="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
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