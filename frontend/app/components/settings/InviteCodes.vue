<script setup lang="ts">
import { Plus, Trash2, Copy, Check, Users, AlertTriangle, RefreshCw } from 'lucide-vue-next'

const { t } = useI18n()
const { getInviteCodes, createInviteCode, deleteInviteCode, getInviteCodeUsages } = useApi()
const toast = useToast()

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
    } catch (e: any) {
        console.error('加载邀请码失败', e)
        toast.error(e.data?.detail || t('admin.invites.loadFailed'))
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
        toast.error(e.data?.detail || t('admin.createFailed'))
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
        toast.error(e.data?.detail || t('admin.deleteFailed'))
    } finally {
        deleting.value = false
    }
}

const copyCode = async (code: InviteCode) => {
    await copyToClipboard(code.code)
    copiedId.value = code.id
    setTimeout(() => copiedId.value = null, 2000)
}

const formatExpireDate = (date: string | null) => {
    if (!date) return t('admin.invites.neverExpires')
    return new Date(date).toLocaleDateString('zh-CN')
}

// formatDateTime 来自 utils/format.ts (Nuxt 自动导入)

const showUsages = async (code: InviteCode) => {
    selectedCode.value = code
    showUsageModal.value = true
    loadingUsages.value = true
    try {
        usages.value = await getInviteCodeUsages(code.id)
    } catch (e: any) {
        console.error('加载使用记录失败', e)
        toast.error(e.data?.detail || t('admin.invites.loadUsagesFailed'))
        usages.value = []
    } finally {
        loadingUsages.value = false
    }
}

// 判断邀请码状态
const getCodeStatus = (code: InviteCode) => {
    if (code.deleted_at) return { text: t('admin.invites.statusDeleted'), class: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500' }
    if (code.expires_at && new Date(code.expires_at) < new Date()) return { text: t('admin.invites.statusExpired'), class: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' }
    if (code.max_uses > 0 && code.used_count >= code.max_uses) return { text: t('admin.invites.statusUsedUp'), class: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400' }
    return { text: t('admin.invites.statusAvailable'), class: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' }
}

onMounted(loadCodes)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">{{ t('admin.invites.title') }}</h2>

        <!-- 创建新邀请码 -->
        <div class="card p-6">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">{{ t('admin.invites.createTitle') }}</h3>
            <div class="flex flex-wrap gap-4 items-end">
                <div class="space-y-1">
                    <label class="text-sm text-gray-500">{{ t('admin.invites.maxUses') }}</label>
                    <input v-model.number="newCode.maxUses" type="number" min="0" class="input-field w-32"
                        :placeholder="t('admin.invites.maxUsesPlaceholder')">
                </div>
                <div class="space-y-1">
                    <label class="text-sm text-gray-500">{{ t('admin.invites.validDays') }}</label>
                    <input v-model.number="newCode.expiresDays" type="number" min="0" class="input-field w-32"
                        :placeholder="t('admin.invites.validDaysPlaceholder')">
                </div>
                <button @click="handleCreate" :disabled="creating" class="btn-primary flex items-center gap-2">
                    <Plus class="w-4 h-4" />
                    {{ creating ? t('admin.creating') : t('admin.create') }}
                </button>
            </div>
        </div>

        <!-- 邀请码列表 -->
        <div class="card overflow-hidden">
            <div v-if="loading" class="p-8 text-center text-gray-500">{{ t('common.loading') }}</div>
            <div v-else-if="codes.length === 0" class="p-8 text-center text-gray-500">{{ t('admin.invites.empty') }}</div>
            <table v-else class="w-full">
                <thead class="bg-gray-50 dark:bg-gray-800/50">
                    <tr>
                        <th class="th">{{ t('admin.invites.code') }}</th>
                        <th class="th">{{ t('admin.invites.usage') }}</th>
                        <th class="th">{{ t('admin.invites.expiresAt') }}</th>
                        <th class="th">
                            <div class="flex items-center justify-between">
                                <span>{{ t('admin.actions') }}</span>
                                <button @click="loadCodes" :disabled="loading" class="icon-btn" :title="t('admin.invites.refreshList')">
                                    <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
                                </button>
                            </div>
                        </th>
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
                                <span :class="['px-2 py-0.5 rounded-full text-xs whitespace-nowrap', getCodeStatus(code).class]">
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
                                :title="t('admin.invites.viewUsageTitle')"
                            >
                                {{ code.used_count }} / {{ code.max_uses || '∞' }}
                                <Users class="w-3.5 h-3.5" />
                            </button>
                            <span v-else :class="code.max_uses > 0 && code.used_count >= code.max_uses ? 'text-red-500' : ''">
                                {{ code.used_count }} / {{ code.max_uses || '∞' }}
                            </span>
                        </td>
                        <td class="td text-gray-500">{{ formatExpireDate(code.expires_at) }}</td>
                        <td class="td">
                            <div class="flex gap-2">
                                <button @click="copyCode(code)" class="icon-btn" :title="t('admin.invites.copy')">
                                    <Check v-if="copiedId === code.id" class="w-4 h-4 text-green-500" />
                                    <Copy v-else class="w-4 h-4" />
                                </button>
                                <button v-if="!code.deleted_at" @click="confirmDelete(code)" class="icon-btn text-red-500" :title="t('common.delete')">
                                    <Trash2 class="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 使用详情弹窗 -->
        <CommonModal v-model="showUsageModal" :title="t('admin.invites.usageModalTitle', { code: selectedCode?.code })">
            <div v-if="loadingUsages" class="py-8 text-center text-gray-500">{{ t('common.loading') }}</div>
            <div v-else-if="usages.length === 0" class="py-8 text-center text-gray-500">{{ t('admin.invites.noUsages') }}</div>
            <div v-else class="space-y-3 max-h-80 overflow-y-auto">
                <div v-for="usage in usages" :key="usage.id"
                    class="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div class="font-medium text-gray-900 dark:text-white">{{ usage.user_email }}</div>
                    <div class="text-sm text-gray-500">{{ formatDateTime(usage.used_at) }}</div>
                </div>
            </div>
            <template #footer>
                <button @click="showUsageModal = false" class="btn-primary">{{ t('common.close') }}</button>
            </template>
        </CommonModal>

        <!-- 删除确认弹窗 -->
        <CommonModal v-model="showDeleteModal" :title="t('admin.confirmDelete')">
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                    <AlertTriangle class="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <div>
                    <p class="text-gray-900 dark:text-white font-medium mb-2">{{ t('admin.invites.deleteConfirmMessage') }}</p>
                    <p class="text-sm text-gray-500">
                        {{ t('admin.invites.code') }} <code class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono">{{ codeToDelete?.code }}</code>
                        {{ t('admin.invites.deleteWarning') }}
                    </p>
                    <p v-if="codeToDelete?.used_count" class="text-sm text-gray-500 mt-2">
                        {{ t('admin.invites.usedTimes', { n: codeToDelete.used_count }) }}
                    </p>
                </div>
            </div>
            <template #footer>
                <button @click="showDeleteModal = false" class="btn-secondary" :disabled="deleting">{{ t('common.cancel') }}</button>
                <button @click="handleDelete" class="btn-danger" :disabled="deleting">
                    {{ deleting ? t('admin.deleting') : t('admin.confirmDelete') }}
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