<script setup lang="ts">
import { User, Plus, Trash2, ToggleLeft, ToggleRight, Mail, RefreshCw, Settings, Download, AlertCircle, Clock } from 'lucide-vue-next'

const { getMe, getAliases, createAlias, updateAlias, deleteAlias, getSubscriptionStatus, getExternalAccounts, createExternalAccount, deleteExternalAccount, testExternalAccount, syncExternalAccount, getProviderPresets } = useApi()
const config = useConfig()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { t } = useI18n()

const loading = ref(true)
const user = ref<AppUser | null>(null)
const aliases = ref<Array<{ id: number; alias_email: string; name: string | null; is_active: boolean }>>([])
const loadingAliases = ref(false)
const subscription = ref<Subscription | null>(null)

// 外部账号
const externalAccounts = ref<any[]>([])
const loadingExternal = ref(false)
const providers = ref<Record<string, any>>({})

// 添加别名弹窗
const showAddModal = ref(false)
const newAliasPrefix = ref('')
const newAliasName = ref('')
const addingAlias = ref(false)
const addError = ref('')

// 添加外部账号弹窗
const showAddAccountModal = ref(false)
const newAccount = ref<ExternalAccountForm>({ email: '', password: '', provider: 'gmail', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587 })
const addingAccount = ref(false)
const accountError = ref('')
const testingAccount = ref<number | null>(null)
const syncingAccount = ref<number | null>(null)

const isCustomProvider = computed(() => newAccount.value.provider === 'custom')

const loadUser = async () => {
    try {
        user.value = await getMe()
    } catch (e: any) {
        console.error('加载用户信息失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.common.loadUserFailed'))
    } finally {
        loading.value = false
    }
}

const loadAliases = async () => {
    loadingAliases.value = true
    try {
        aliases.value = await getAliases()
    } catch (e: any) {
        console.error('加载别名失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.loadAliasesFailed'))
    } finally {
        loadingAliases.value = false
    }
}

const loadSubscription = async () => {
    try {
        subscription.value = await getSubscriptionStatus()
    } catch (e: any) {
        console.error('加载订阅状态失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.loadSubFailed'))
    }
}

const loadExternalAccounts = async () => {
    loadingExternal.value = true
    try {
        externalAccounts.value = await getExternalAccounts()
    } catch (e: any) {
        console.error('加载外部账号失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.loadExternalFailed'))
    } finally {
        loadingExternal.value = false
    }
}

const loadProviders = async () => {
    try {
        providers.value = await getProviderPresets()
    } catch (e: any) {
        console.error('加载服务商失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.loadProvidersFailed'))
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
        addError.value = e.data?.detail || t('settingsSecurity.accounts.createFailed')
    } finally {
        addingAlias.value = false
    }
}

const handleToggleAlias = async (alias: any) => {
    try {
        const result = await updateAlias(alias.id, { is_active: !alias.is_active })
        alias.is_active = result.is_active
    } catch (e: any) {
        console.error('更新失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.updateFailed'))
    }
}

const handleDeleteAlias = async (id: number) => {
    const ok = await confirmDialog({ message: t('settingsSecurity.accounts.deleteAliasConfirm'), type: 'danger' })
    if (!ok) return
    try {
        await deleteAlias(id)
        aliases.value = aliases.value.filter(a => a.id !== id)
        toast.success(t('settingsSecurity.accounts.aliasDeleted'))
    } catch (e: any) {
        console.error('删除失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.deleteAliasFailed'))
    }
}

const canAddAlias = computed(() => {
    if (!subscription.value) return false
    const limit = subscription.value.max_aliases
    if (limit === -1) return true
    return aliases.value.length < limit
})

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
        accountError.value = e.data?.detail || t('settingsSecurity.accounts.addFailed')
    } finally {
        addingAccount.value = false
    }
}

const handleDeleteAccount = async (id: number) => {
    const ok = await confirmDialog({ message: t('settingsSecurity.accounts.deleteAccountConfirm'), type: 'danger' })
    if (!ok) return
    try {
        await deleteExternalAccount(id)
        externalAccounts.value = externalAccounts.value.filter(a => a.id !== id)
        toast.success(t('settingsSecurity.accounts.accountDeleted'))
    } catch (e: any) {
        console.error('删除失败', e)
        toast.error(e.data?.detail || t('settingsSecurity.accounts.deleteFailed'))
    }
}

const handleTestAccount = async (id: number) => {
    testingAccount.value = id
    try {
        const result = await testExternalAccount(id)
        if (result.success) {
            toast.success(t('settingsSecurity.accounts.connectSuccess'))
        } else {
            toast.error(t('settingsSecurity.accounts.connectFailed', { msg: result.message }))
        }
    } catch (e: any) {
        toast.error(t('settingsSecurity.accounts.testFailed', { msg: e.data?.detail || t('settingsSecurity.accounts.unknownError') }))
    } finally {
        testingAccount.value = null
    }
}

const handleSyncAccount = async (id: number) => {
    syncingAccount.value = id
    try {
        const result = await syncExternalAccount(id)
        if (result.synced > 0) {
            toast.success(t('settingsSecurity.accounts.syncedWithCount', { n: result.synced }))
        } else {
            toast.success(t('settingsSecurity.accounts.syncedNone'))
        }
        // 更新本地状态
        const account = externalAccounts.value.find(a => a.id === id)
        if (account) {
            account.last_sync_at = result.last_sync_at
            account.sync_error = result.sync_error
        }
    } catch (e: any) {
        toast.error(t('settingsSecurity.accounts.syncFailed', { msg: e.data?.detail || t('settingsSecurity.accounts.unknownError') }))
    } finally {
        syncingAccount.value = null
    }
}

const formatSyncTime = (dateStr: string | null) => {
    if (!dateStr) return t('settingsSecurity.accounts.neverSynced')
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return t('settingsSecurity.common.justNow')
    if (diffMin < 60) return t('settingsSecurity.common.minutesAgo', { n: diffMin })
    const diffHours = Math.floor(diffMin / 60)
    if (diffHours < 24) return t('settingsSecurity.common.hoursAgo', { n: diffHours })
    const diffDays = Math.floor(diffHours / 24)
    return t('settingsSecurity.common.daysAgo', { n: diffDays })
}

const getProviderName = (provider: string) => {
    const names: Record<string, string> = { gmail: 'Gmail', outlook: 'Outlook', icloud: 'iCloud', yahoo: 'Yahoo', qq: t('settingsSecurity.accounts.providerQQ'), '163': t('settingsSecurity.accounts.provider163'), '126': t('settingsSecurity.accounts.provider126'), yeah: 'Yeah.net', sina: t('settingsSecurity.accounts.providerSina'), aliyun: t('settingsSecurity.accounts.providerAliyun'), zoho: 'Zoho', custom: t('settingsSecurity.accounts.providerCustom') }
    return names[provider] || provider
}

onMounted(() => {
    loadUser()
    loadAliases()
    loadSubscription()
    loadExternalAccounts()
    loadProviders()
})
</script>

<template>
    <div class="space-y-8">
        <div class="flex justify-between items-center">
            <h2 class="section-title mb-0">{{ t('settingsSecurity.accounts.title') }}</h2>
            <button @click="showAddAccountModal = true"
                class="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-hover flex items-center gap-2">
                <Plus class="w-4 h-4" /> {{ t('settingsSecurity.accounts.addAccount') }}
            </button>
        </div>

        <div v-if="loading" class="text-gray-500">{{ t('common.loading') }}</div>

        <template v-else-if="user">
            <!-- 主账号 -->
            <div class="card bg-white dark:bg-bg-panelDark border-primary/30 relative overflow-hidden">
                <div class="absolute top-0 right-0 bg-primary text-white text-xs px-2 py-1 rounded-bl-lg">{{ t('settingsSecurity.accounts.current') }}</div>
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

            <!-- 外部邮箱账号 -->
            <div class="card bg-white dark:bg-bg-panelDark">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">{{ t('settingsSecurity.accounts.externalAccounts') }}</h3>
                <div v-if="loadingExternal" class="text-sm text-gray-500 p-4 text-center">{{ t('common.loading') }}</div>
                <div v-else-if="externalAccounts.length === 0" class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                    {{ t('settingsSecurity.accounts.noExternal') }}
                </div>
                <div v-else class="space-y-2">
                    <div v-for="account in externalAccounts" :key="account.id"
                        class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <Mail class="w-5 h-5 text-gray-400" />
                                <div>
                                    <div class="font-medium text-gray-900 dark:text-white text-sm">{{ account.email }}</div>
                                    <div class="text-xs text-gray-500">{{ getProviderName(account.provider) }}</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                <button @click="handleSyncAccount(account.id)" :disabled="syncingAccount === account.id"
                                    class="text-gray-400 hover:text-green-500 transition-colors p-1" :title="t('settingsSecurity.accounts.syncNow')">
                                    <Download class="w-4 h-4" :class="{ 'animate-bounce': syncingAccount === account.id }" />
                                </button>
                                <button @click="handleTestAccount(account.id)" :disabled="testingAccount === account.id"
                                    class="text-gray-400 hover:text-primary transition-colors p-1" :title="t('settingsSecurity.accounts.testConnection')">
                                    <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': testingAccount === account.id }" />
                                </button>
                                <button @click="handleDeleteAccount(account.id)"
                                    class="text-gray-400 hover:text-red-500 transition-colors p-1">
                                    <Trash2 class="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                        <!-- 同步状态行 -->
                        <div class="mt-2 flex items-center gap-3 text-xs">
                            <span class="flex items-center gap-1 text-gray-400">
                                <Clock class="w-3 h-3" />
                                {{ formatSyncTime(account.last_sync_at) }}
                            </span>
                            <span v-if="account.sync_error" class="flex items-center gap-1 text-red-400" :title="account.sync_error">
                                <AlertCircle class="w-3 h-3" />
                                {{ t('settingsSecurity.accounts.syncError') }}
                            </span>
                            <span v-if="!account.sync_enabled" class="text-orange-400">
                                {{ t('settingsSecurity.accounts.syncPaused') }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 别名管理 -->
            <div class="card bg-white dark:bg-bg-panelDark">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white">{{ t('settingsSecurity.accounts.aliasesTitle') }}</h3>
                        <p class="text-xs text-gray-500 mt-1">
                            {{ t('settingsSecurity.accounts.aliasUsage', { used: aliases.length, total: subscription?.max_aliases === -1 ? '∞' : subscription?.max_aliases || 0 }) }}
                        </p>
                    </div>
                    <button @click="showAddModal = true" :disabled="!canAddAlias"
                        class="text-primary text-sm font-medium flex items-center gap-1 hover:underline disabled:opacity-50 disabled:cursor-not-allowed">
                        <Plus class="w-4 h-4" /> {{ t('settingsSecurity.accounts.addAlias') }}
                    </button>
                </div>
                
                <div v-if="loadingAliases" class="text-sm text-gray-500 p-4 text-center">
                    {{ t('common.loading') }}
                </div>
                <div v-else-if="aliases.length === 0" class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                    {{ t('settingsSecurity.accounts.noAliases') }}
                </div>
                <div v-else class="space-y-2">
                    <div v-for="alias in aliases" :key="alias.id"
                        class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg group">
                        <div>
                            <div class="font-medium text-gray-900 dark:text-white text-sm flex items-center gap-2">
                                {{ alias.alias_email }}
                                <span v-if="!alias.is_active" class="text-xs bg-gray-200 dark:bg-gray-700 text-gray-500 px-1.5 py-0.5 rounded">{{ t('settingsSecurity.accounts.inactive') }}</span>
                            </div>
                            <div v-if="alias.name" class="text-xs text-gray-500">{{ alias.name }}</div>
                        </div>
                        <div class="flex items-center gap-2">
                            <button @click="handleToggleAlias(alias)"
                                class="text-gray-400 hover:text-primary transition-colors p-1" :title="alias.is_active ? t('settingsSecurity.accounts.disable') : t('settingsSecurity.accounts.enable')">
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
        <CommonModal v-model="showAddModal" :title="t('settingsSecurity.accounts.addAliasModalTitle')">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.common.aliasAddress') }}</label>
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
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.common.aliasNameOptional') }}</label>
                    <input v-model="newAliasName" type="text"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        :placeholder="t('settingsSecurity.accounts.aliasNamePlaceholder')">
                </div>
                <div v-if="addError" class="text-red-500 text-sm">{{ addError }}</div>
                <div class="flex justify-end gap-2 pt-2">
                    <button @click="showAddModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">
                        {{ t('common.cancel') }}
                    </button>
                    <button @click="handleAddAlias" :disabled="addingAlias || !newAliasPrefix.trim()"
                        class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50">
                        {{ addingAlias ? t('settingsSecurity.accounts.creating') : t('settingsSecurity.accounts.create') }}
                    </button>
                </div>
            </div>
        </CommonModal>

        <!-- 添加外部账号弹窗 -->
        <CommonModal v-model="showAddAccountModal" :title="t('settingsSecurity.accounts.addExternalTitle')">
            <div class="space-y-4 max-h-96 overflow-y-auto">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.accounts.provider') }}</label>
                    <select v-model="newAccount.provider"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                        <optgroup :label="t('settingsSecurity.accounts.groupInternational')">
                            <option value="gmail">Gmail</option>
                            <option value="outlook">Outlook / Hotmail</option>
                            <option value="icloud">iCloud</option>
                            <option value="yahoo">Yahoo Mail</option>
                            <option value="zoho">Zoho Mail</option>
                        </optgroup>
                        <optgroup :label="t('settingsSecurity.accounts.groupChina')">
                            <option value="qq">{{ t('settingsSecurity.accounts.optQQ') }}</option>
                            <option value="163">{{ t('settingsSecurity.accounts.opt163') }}</option>
                            <option value="126">{{ t('settingsSecurity.accounts.opt126') }}</option>
                            <option value="yeah">{{ t('settingsSecurity.accounts.optYeah') }}</option>
                            <option value="sina">{{ t('settingsSecurity.accounts.optSina') }}</option>
                            <option value="aliyun">{{ t('settingsSecurity.accounts.optAliyun') }}</option>
                        </optgroup>
                        <optgroup :label="t('settingsSecurity.accounts.groupOther')">
                            <option value="custom">{{ t('settingsSecurity.accounts.optCustom') }}</option>
                        </optgroup>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.common.emailAddress') }}</label>
                    <input v-model="newAccount.email" type="email"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        placeholder="your@email.com">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.accounts.passwordLabel') }}</label>
                    <input v-model="newAccount.password" type="password"
                        class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                        :placeholder="t('settingsSecurity.accounts.passwordPlaceholder')">
                    <p class="text-xs text-gray-500 mt-1">{{ t('settingsSecurity.accounts.appPasswordHint') }}</p>
                </div>
                <!-- 自定义服务器配置 -->
                <template v-if="isCustomProvider">
                    <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{{ t('settingsSecurity.accounts.imapHost') }}</label>
                        <div class="flex gap-2">
                            <input v-model="newAccount.imap_host" type="text" placeholder="imap.example.com"
                                class="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm">
                            <input v-model.number="newAccount.imap_port" type="number" placeholder="993"
                                class="w-20 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{{ t('settingsSecurity.accounts.smtpHost') }}</label>
                        <div class="flex gap-2">
                            <input v-model="newAccount.smtp_host" type="text" placeholder="smtp.example.com"
                                class="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm">
                            <input v-model.number="newAccount.smtp_port" type="number" placeholder="587"
                                class="w-20 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm">
                        </div>
                    </div>
                </template>
                <div v-if="accountError" class="text-red-500 text-sm">{{ accountError }}</div>
                <div class="flex justify-end gap-2 pt-2">
                    <button @click="showAddAccountModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">
                        {{ t('common.cancel') }}
                    </button>
                    <button @click="handleAddAccount" :disabled="addingAccount || !newAccount.email || !newAccount.password || (isCustomProvider && (!newAccount.imap_host || !newAccount.smtp_host))"
                        class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50">
                        {{ addingAccount ? t('settingsSecurity.common.adding') : t('settingsSecurity.common.add') }}
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