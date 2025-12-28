<script setup lang="ts">
import { User, Plus, Trash2, ToggleLeft, ToggleRight } from 'lucide-vue-next'

const { getMe, getAliases, createAlias, updateAlias, deleteAlias, getSubscriptionStatus } = useApi()
const config = useConfig()

const loading = ref(true)
const user = ref<any>(null)
const aliases = ref<Array<{ id: number; alias_email: string; name: string | null; is_active: boolean }>>([])
const loadingAliases = ref(false)
const subscription = ref<any>(null)

// 添加别名弹窗
const showAddModal = ref(false)
const newAliasPrefix = ref('')
const newAliasName = ref('')
const addingAlias = ref(false)
const addError = ref('')

const loadUser = async () => {
    try {
        user.value = await getMe()
    } catch (e: any) {
        console.error('加载用户信息失败', e)
    } finally {
        loading.value = false
    }
}

const loadAliases = async () => {
    loadingAliases.value = true
    try {
        aliases.value = await getAliases()
    } catch (e) {
        console.error('加载别名失败', e)
    } finally {
        loadingAliases.value = false
    }
}

const loadSubscription = async () => {
    try {
        subscription.value = await getSubscriptionStatus()
    } catch (e) {
        console.error('加载订阅状态失败', e)
    }
}

const getInitial = () => {
    if (user.value?.display_name) return user.value.display_name[0].toUpperCase()
    if (user.value?.email) return user.value.email.split('@')[0][0].toUpperCase()
    return 'U'
}

const handleAddAlias = async () => {
    if (!newAliasPrefix.value.trim()) return
    
    addingAlias.value = true
    addError.value = ''
    try {
        const result = await createAlias(newAliasPrefix.value.trim(), newAliasName.value.trim() || undefined)
        aliases.value.push(result)
        showAddModal.value = false
        newAliasPrefix.value = ''
        newAliasName.value = ''
    } catch (e: any) {
        addError.value = e.data?.detail || '创建失败'
    } finally {
        addingAlias.value = false
    }
}

const handleToggleAlias = async (alias: any) => {
    try {
        const result = await updateAlias(alias.id, { is_active: !alias.is_active })
        alias.is_active = result.is_active
    } catch (e) {
        console.error('更新失败', e)
    }
}

const handleDeleteAlias = async (id: number) => {
    try {
        await deleteAlias(id)
        aliases.value = aliases.value.filter(a => a.id !== id)
    } catch (e) {
        console.error('删除失败', e)
    }
}

const canAddAlias = computed(() => {
    if (!subscription.value) return false
    const limit = subscription.value.max_aliases
    if (limit === -1) return true
    return aliases.value.length < limit
})

onMounted(() => {
    loadUser()
    loadAliases()
    loadSubscription()
})
</script>

<template>
    <div class="space-y-8">
        <div class="flex justify-between items-center">
            <h2 class="section-title mb-0">多账号管理</h2>
            <button disabled
                class="bg-gray-300 dark:bg-gray-700 text-gray-500 px-4 py-2 rounded-lg text-sm cursor-not-allowed flex items-center gap-2">
                <Plus class="w-4 h-4" /> 添加账号
            </button>
        </div>

        <div v-if="loading" class="text-gray-500">加载中...</div>

        <template v-else-if="user">
            <!-- 主账号 -->
            <div class="card border-primary/30 relative overflow-hidden">
                <div class="absolute top-0 right-0 bg-primary text-white text-xs px-2 py-1 rounded-bl-lg">当前</div>
                <div class="flex items-center gap-4">
                    <div
                        class="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-white text-xl font-bold">
                        {{ getInitial() }}</div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white text-lg">{{ user.display_name || user.email.split('@')[0] }}</div>
                        <div class="text-gray-500">{{ user.email }}</div>
                    </div>
                </div>
            </div>

            <!-- 别名管理 -->
            <div class="card">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white">邮件别名 (Aliases)</h3>
                        <p class="text-xs text-gray-500 mt-1">
                            已使用 {{ aliases.length }} / {{ subscription?.max_aliases === -1 ? '∞' : subscription?.max_aliases || 0 }}
                        </p>
                    </div>
                    <button @click="showAddModal = true" :disabled="!canAddAlias"
                        class="text-primary text-sm font-medium flex items-center gap-1 hover:underline disabled:opacity-50 disabled:cursor-not-allowed">
                        <Plus class="w-4 h-4" /> 添加别名
                    </button>
                </div>
                
                <div v-if="loadingAliases" class="text-sm text-gray-500 p-4 text-center">
                    加载中...
                </div>
                <div v-else-if="aliases.length === 0" class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                    暂无邮件别名
                </div>
                <div v-else class="space-y-2">
                    <div v-for="alias in aliases" :key="alias.id"
                        class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg group">
                        <div>
                            <div class="font-medium text-gray-900 dark:text-white text-sm flex items-center gap-2">
                                {{ alias.alias_email }}
                                <span v-if="!alias.is_active" class="text-xs bg-gray-200 dark:bg-gray-700 text-gray-500 px-1.5 py-0.5 rounded">已停用</span>
                            </div>
                            <div v-if="alias.name" class="text-xs text-gray-500">{{ alias.name }}</div>
                        </div>
                        <div class="flex items-center gap-2">
                            <button @click="handleToggleAlias(alias)"
                                class="text-gray-400 hover:text-primary transition-colors p-1" :title="alias.is_active ? '停用' : '启用'">
                                <ToggleRight v-if="alias.is_active" class="w-5 h-5 text-primary" />
                                <ToggleLeft v-else class="w-5 h-5" />
                            </button>
                            <button @click="handleDeleteAlias(alias.id)"
                                class="text-gray-400 hover:text-red-500 transition-colors p-1">
                                <Trash2 class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </template>

        <!-- 添加别名弹窗 -->
        <CommonModal v-model="showAddModal" title="添加邮件别名">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">别名地址</label>
                    <div class="flex items-center">
                        <input v-model="newAliasPrefix" type="text"
                            class="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-l-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                            placeholder="alias">
                        <span class="px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-l-0 border-gray-200 dark:border-gray-700 rounded-r-lg text-gray-500 text-sm">
                            @{{ config?.baseDomain || 'example.com' }}
                        </span>
                    </div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">备注名称（可选）</label>
                    <input v-model="newAliasName" type="text"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        placeholder="例如：工作邮箱">
                </div>
                <div v-if="addError" class="text-red-500 text-sm">{{ addError }}</div>
                <div class="flex justify-end gap-2 pt-2">
                    <button @click="showAddModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">
                        取消
                    </button>
                    <button @click="handleAddAlias" :disabled="addingAlias || !newAliasPrefix.trim()"
                        class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50">
                        {{ addingAlias ? '创建中...' : '创建' }}
                    </button>
                </div>
            </div>
        </CommonModal>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6;
}
</style>