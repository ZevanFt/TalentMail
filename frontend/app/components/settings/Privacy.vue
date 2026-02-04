<script setup lang="ts">
import { ShieldAlert, ImageOff, Plus, X, Trash2, ShieldCheck } from 'lucide-vue-next'

const { getMe, updateMe, getBlockedSenders, addBlockedSender, removeBlockedSender, getWhitelist, addToWhitelist, removeFromWhitelist } = useApi()

const user = ref<any>(null)
const loading = ref(true)
const saving = ref(false)

// 黑名单相关
const blockedSenders = ref<Array<{ id: number; email: string; reason: string | null; created_at: string | null }>>([])
const loadingBlocklist = ref(false)
const showAddModal = ref(false)
const newBlockedEmail = ref('')
const newBlockedReason = ref('')
const addingBlocked = ref(false)
const addError = ref('')

// 白名单相关
const whitelist = ref<Array<{ id: number; email: string; sender_type: string; note: string | null; created_at: string | null }>>([])
const loadingWhitelist = ref(false)
const showAddWhitelistModal = ref(false)
const newWhitelistEmail = ref('')
const newWhitelistNote = ref('')
const addingWhitelist = ref(false)
const addWhitelistError = ref('')

const loadUser = async () => {
    loading.value = true
    try {
        user.value = await getMe()
    } catch (e) {
        console.error('加载用户信息失败', e)
    } finally {
        loading.value = false
    }
}

const loadBlocklist = async () => {
    loadingBlocklist.value = true
    try {
        blockedSenders.value = await getBlockedSenders()
    } catch (e) {
        console.error('加载黑名单失败', e)
    } finally {
        loadingBlocklist.value = false
    }
}

const loadWhitelist = async () => {
    loadingWhitelist.value = true
    try {
        whitelist.value = await getWhitelist()
    } catch (e) {
        console.error('加载白名单失败', e)
    } finally {
        loadingWhitelist.value = false
    }
}

const updateSettings = async (key: string, value: any) => {
    if (!user.value) return
    
    // 乐观更新
    const oldValue = user.value[key]
    user.value[key] = value
    
    saving.value = true
    try {
        await updateMe({ [key]: value })
    } catch (e) {
        console.error('更新设置失败', e)
        // 回滚
        user.value[key] = oldValue
    } finally {
        saving.value = false
    }
}

const handleAddBlocked = async () => {
    if (!newBlockedEmail.value.trim()) return
    
    addingBlocked.value = true
    addError.value = ''
    try {
        const result = await addBlockedSender(newBlockedEmail.value.trim(), newBlockedReason.value.trim() || undefined)
        blockedSenders.value.unshift(result)
        showAddModal.value = false
        newBlockedEmail.value = ''
        newBlockedReason.value = ''
    } catch (e: any) {
        addError.value = e.data?.detail || '添加失败'
    } finally {
        addingBlocked.value = false
    }
}

const handleRemoveBlocked = async (id: number) => {
    try {
        await removeBlockedSender(id)
        blockedSenders.value = blockedSenders.value.filter(b => b.id !== id)
    } catch (e) {
        console.error('移除失败', e)
    }
}

const handleAddWhitelist = async () => {
    if (!newWhitelistEmail.value.trim()) return

    addingWhitelist.value = true
    addWhitelistError.value = ''
    try {
        const result = await addToWhitelist(newWhitelistEmail.value.trim(), newWhitelistNote.value.trim() || undefined)
        whitelist.value.unshift(result)
        showAddWhitelistModal.value = false
        newWhitelistEmail.value = ''
        newWhitelistNote.value = ''
    } catch (e: any) {
        addWhitelistError.value = e.data?.detail || '添加失败'
    } finally {
        addingWhitelist.value = false
    }
}

const handleRemoveWhitelist = async (id: number) => {
    try {
        await removeFromWhitelist(id)
        whitelist.value = whitelist.value.filter(w => w.id !== id)
    } catch (e) {
        console.error('移除失败', e)
    }
}

const formatDate = (date: string | null) => {
    if (!date) return '-'
    return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(() => {
    loadUser()
    loadBlocklist()
    loadWhitelist()
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">隐私与拦截</h2>

        <!-- 垃圾邮件过滤 -->
        <div class="card space-y-6">
            <div class="flex gap-4">
                <div class="icon-box bg-red-100 text-red-600">
                    <ShieldAlert class="w-5 h-5" />
                </div>
                <div class="flex-1">
                    <h3 class="font-bold text-gray-900 dark:text-white">垃圾邮件过滤级别</h3>
                    <div class="mt-3 flex gap-4">
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="spam" class="accent-primary"
                                :checked="user?.spam_filter_level === 'standard'"
                                @change="updateSettings('spam_filter_level', 'standard')">
                            <span class="text-sm dark:text-gray-300">标准 (推荐)</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="spam" class="accent-primary"
                                :checked="user?.spam_filter_level === 'strict'"
                                @change="updateSettings('spam_filter_level', 'strict')">
                            <span class="text-sm dark:text-gray-300">严格</span>
                        </label>
                    </div>
                </div>
            </div>
        </div>

        <!-- 黑名单 -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-bold text-gray-900 dark:text-white">黑名单管理</h3>
                <button @click="showAddModal = true" class="text-primary text-sm font-medium flex items-center gap-1 hover:underline">
                    <Plus class="w-4 h-4" /> 添加
                </button>
            </div>
            
            <div v-if="loadingBlocklist" class="text-sm text-gray-500 p-4 text-center">
                加载中...
            </div>
            <div v-else-if="blockedSenders.length === 0" class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                暂无屏蔽的邮箱地址
            </div>
            <div v-else class="space-y-2 max-h-60 overflow-y-auto">
                <div v-for="blocked in blockedSenders" :key="blocked.id"
                    class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg group">
                    <div>
                        <div class="font-medium text-gray-900 dark:text-white text-sm">{{ blocked.email }}</div>
                        <div class="text-xs text-gray-500">
                            {{ blocked.reason || '无备注' }} · {{ formatDate(blocked.created_at) }}
                        </div>
                    </div>
                    <button @click="handleRemoveBlocked(blocked.id)"
                        class="text-red-500 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity p-1">
                        <Trash2 class="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>

        <!-- 添加黑名单弹窗 -->
        <CommonModal v-model="showAddModal" title="添加到黑名单">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮箱地址</label>
                    <input v-model="newBlockedEmail" type="email"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        placeholder="example@domain.com">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">备注（可选）</label>
                    <input v-model="newBlockedReason" type="text"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        placeholder="屏蔽原因">
                </div>
                <div v-if="addError" class="text-red-500 text-sm">{{ addError }}</div>
                <div class="flex justify-end gap-2 pt-2">
                    <button @click="showAddModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">
                        取消
                    </button>
                    <button @click="handleAddBlocked" :disabled="addingBlocked || !newBlockedEmail.trim()"
                        class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50">
                        {{ addingBlocked ? '添加中...' : '添加' }}
                    </button>
                </div>
            </div>
        </CommonModal>

        <!-- 白名单 -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <div class="flex items-center gap-2">
                    <div class="icon-box bg-green-100 text-green-600">
                        <ShieldCheck class="w-5 h-5" />
                    </div>
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white">白名单管理</h3>
                        <p class="text-xs text-gray-500">白名单中的发件人邮件将不会被标记为垃圾邮件</p>
                    </div>
                </div>
                <button @click="showAddWhitelistModal = true" class="text-primary text-sm font-medium flex items-center gap-1 hover:underline">
                    <Plus class="w-4 h-4" /> 添加
                </button>
            </div>

            <div v-if="loadingWhitelist" class="text-sm text-gray-500 p-4 text-center">
                加载中...
            </div>
            <div v-else-if="whitelist.length === 0" class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                暂无白名单邮箱地址
            </div>
            <div v-else class="space-y-2 max-h-60 overflow-y-auto">
                <div v-for="item in whitelist" :key="item.id"
                    class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg group">
                    <div>
                        <div class="font-medium text-gray-900 dark:text-white text-sm">{{ item.email }}</div>
                        <div class="text-xs text-gray-500">
                            {{ item.note || '无备注' }} · {{ formatDate(item.created_at) }}
                        </div>
                    </div>
                    <button @click="handleRemoveWhitelist(item.id)"
                        class="text-red-500 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity p-1">
                        <Trash2 class="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>

        <!-- 添加白名单弹窗 -->
        <CommonModal v-model="showAddWhitelistModal" title="添加到白名单">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮箱地址</label>
                    <input v-model="newWhitelistEmail" type="email"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        placeholder="example@domain.com">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">备注（可选）</label>
                    <input v-model="newWhitelistNote" type="text"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        placeholder="添加备注">
                </div>
                <div v-if="addWhitelistError" class="text-red-500 text-sm">{{ addWhitelistError }}</div>
                <div class="flex justify-end gap-2 pt-2">
                    <button @click="showAddWhitelistModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">
                        取消
                    </button>
                    <button @click="handleAddWhitelist" :disabled="addingWhitelist || !newWhitelistEmail.trim()"
                        class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50">
                        {{ addingWhitelist ? '添加中...' : '添加' }}
                    </button>
                </div>
            </div>
        </CommonModal>

        <!-- 外部图片 -->
        <div class="card flex items-center justify-between">
            <div class="flex gap-4">
                <div class="icon-box bg-gray-200 text-gray-600">
                    <ImageOff class="w-5 h-5" />
                </div>
                <div>
                    <div class="font-bold text-gray-900 dark:text-white">阻止外部图片</div>
                    <div class="text-sm text-gray-500">默认不加载邮件中的外部图片以保护隐私</div>
                </div>
            </div>
            <CommonToggle
                :model-value="user?.block_external_images ?? true"
                @update:model-value="updateSettings('block_external_images', $event)"
            />
        </div>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6;
}

.icon-box {
    @apply p-2 rounded-lg h-fit;
}
</style>