<script setup lang="ts">
import { PenTool, Calendar, Server, Plus, Trash2, Check, AtSign, Power, Loader2 } from 'lucide-vue-next'

const { getMe, updateMe, getSignatures, createSignature, updateSignature, deleteSignature, getAliases, createAlias, updateAlias, deleteAlias } = useApi()
const { baseDomain } = useConfig()

// 邮件服务器配置
const mailServer = computed(() => `mail.${baseDomain}`)

interface Signature {
    id: number
    name: string
    content_html: string
    is_default: boolean
}

interface EmailAlias {
    id: number
    alias_email: string
    name: string | null
    is_active: boolean
}

const loading = ref(true)
const saving = ref(false)
const signatures = ref<Signature[]>([])
const editingSignature = ref<Signature | null>(null)
const newSignatureName = ref('')
const newSignatureContent = ref('')
const showNewForm = ref(false)

// 别名管理
const aliases = ref<EmailAlias[]>([])
const showAliasForm = ref(false)
const newAliasPrefix = ref('')
const newAliasName = ref('')
const aliasLoading = ref(false)
const aliasError = ref('')

const settings = reactive({
    auto_reply_enabled: false,
    auto_reply_start_date: '',
    auto_reply_end_date: '',
    auto_reply_message: ''
})

const loadSettings = async () => {
    try {
        const [user, sigs, aliasData] = await Promise.all([getMe(), getSignatures(), getAliases()])
        settings.auto_reply_enabled = user.auto_reply_enabled || false
        settings.auto_reply_start_date = user.auto_reply_start_date || ''
        settings.auto_reply_end_date = user.auto_reply_end_date || ''
        settings.auto_reply_message = user.auto_reply_message || ''
        signatures.value = sigs
        aliases.value = aliasData
    } catch (e) {
        console.error('加载设置失败', e)
    } finally {
        loading.value = false
    }
}

const toggleAutoReply = async () => {
    settings.auto_reply_enabled = !settings.auto_reply_enabled
    await saveSettings()
}

const saveSettings = async () => {
    saving.value = true
    try {
        await updateMe({
            auto_reply_enabled: settings.auto_reply_enabled,
            auto_reply_start_date: settings.auto_reply_start_date || null,
            auto_reply_end_date: settings.auto_reply_end_date || null,
            auto_reply_message: settings.auto_reply_message || null
        })
    } catch (e) {
        console.error('保存设置失败', e)
    } finally {
        saving.value = false
    }
}

const addSignature = async () => {
    if (!newSignatureName.value.trim()) return
    try {
        const sig = await createSignature({
            name: newSignatureName.value,
            content_html: newSignatureContent.value,
            is_default: signatures.value.length === 0
        })
        signatures.value.push(sig)
        newSignatureName.value = ''
        newSignatureContent.value = ''
        showNewForm.value = false
    } catch (e) {
        console.error('创建签名失败', e)
    }
}

const startEdit = (sig: Signature) => {
    editingSignature.value = { ...sig }
}

const saveEdit = async () => {
    if (!editingSignature.value) return
    try {
        const updated = await updateSignature(editingSignature.value.id, {
            name: editingSignature.value.name,
            content_html: editingSignature.value.content_html
        })
        const idx = signatures.value.findIndex(s => s.id === updated.id)
        if (idx >= 0) signatures.value[idx] = updated
        editingSignature.value = null
    } catch (e) {
        console.error('更新签名失败', e)
    }
}

const setDefault = async (sig: Signature) => {
    try {
        await updateSignature(sig.id, { is_default: true })
        signatures.value.forEach(s => s.is_default = s.id === sig.id)
    } catch (e) {
        console.error('设置默认签名失败', e)
    }
}

const removeSig = async (sig: Signature) => {
    if (!confirm('确定删除此签名？')) return
    try {
        await deleteSignature(sig.id)
        signatures.value = signatures.value.filter(s => s.id !== sig.id)
    } catch (e) {
        console.error('删除签名失败', e)
    }
}

// 别名管理
const addAlias = async () => {
    if (!newAliasPrefix.value.trim()) return
    aliasLoading.value = true
    aliasError.value = ''
    try {
        const alias = await createAlias(newAliasPrefix.value, newAliasName.value || undefined)
        aliases.value.push(alias)
        newAliasPrefix.value = ''
        newAliasName.value = ''
        showAliasForm.value = false
    } catch (e: any) {
        aliasError.value = e.data?.detail || '创建别名失败'
    } finally {
        aliasLoading.value = false
    }
}

const toggleAliasActive = async (alias: EmailAlias) => {
    try {
        const updated = await updateAlias(alias.id, { is_active: !alias.is_active })
        const idx = aliases.value.findIndex(a => a.id === updated.id)
        if (idx >= 0) aliases.value[idx] = updated
    } catch (e) {
        console.error('切换别名状态失败', e)
    }
}

const removeAlias = async (alias: EmailAlias) => {
    if (!confirm(`确定删除别名 ${alias.alias_email}？`)) return
    try {
        await deleteAlias(alias.id)
        aliases.value = aliases.value.filter(a => a.id !== alias.id)
    } catch (e) {
        console.error('删除别名失败', e)
    }
}

onMounted(loadSettings)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">邮件设置</h2>

        <div v-if="loading" class="text-gray-500">加载中...</div>

        <template v-else>
            <!-- 1. 签名管理 -->
            <section class="card">
                <div class="card-header">
                    <div class="flex items-center gap-3">
                        <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                            <PenTool class="w-5 h-5" />
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white">邮件签名</h3>
                            <p class="text-xs text-gray-500">发送邮件时自动附加的内容</p>
                        </div>
                    </div>
                    <button @click="showNewForm = true" class="btn-secondary text-xs">
                        <Plus class="w-3 h-3 mr-1" /> 新增签名
                    </button>
                </div>

                <!-- 新增签名表单 -->
                <div v-if="showNewForm" class="mt-4 p-4 border border-blue-200 dark:border-blue-800 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                    <input v-model="newSignatureName" class="input-field mb-2" placeholder="签名名称" />
                    <textarea v-model="newSignatureContent" class="input-field h-20" placeholder="签名内容（支持HTML）"></textarea>
                    <div class="flex gap-2 mt-2">
                        <button @click="addSignature" class="btn-primary text-xs">保存</button>
                        <button @click="showNewForm = false" class="btn-secondary text-xs">取消</button>
                    </div>
                </div>

                <!-- 签名列表 -->
                <div class="mt-4 space-y-3">
                    <div v-for="sig in signatures" :key="sig.id" class="p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                        <template v-if="editingSignature?.id === sig.id">
                            <input v-model="editingSignature.name" class="input-field mb-2" />
                            <textarea v-model="editingSignature.content_html" class="input-field h-20"></textarea>
                            <div class="flex gap-2 mt-2">
                                <button @click="saveEdit" class="btn-primary text-xs">保存</button>
                                <button @click="editingSignature = null" class="btn-secondary text-xs">取消</button>
                            </div>
                        </template>
                        <template v-else>
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <span class="font-medium dark:text-white">{{ sig.name }}</span>
                                    <span v-if="sig.is_default" class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">默认</span>
                                </div>
                                <div class="flex gap-2">
                                    <button v-if="!sig.is_default" @click="setDefault(sig)" class="text-gray-400 hover:text-green-500" title="设为默认">
                                        <Check class="w-4 h-4" />
                                    </button>
                                    <button @click="startEdit(sig)" class="text-gray-400 hover:text-blue-500" title="编辑">
                                        <PenTool class="w-4 h-4" />
                                    </button>
                                    <button @click="removeSig(sig)" class="text-gray-400 hover:text-red-500" title="删除">
                                        <Trash2 class="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                            <div class="mt-2 text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap" v-html="sig.content_html"></div>
                        </template>
                    </div>
                    <div v-if="signatures.length === 0" class="text-gray-500 text-sm">暂无签名，点击上方按钮新增</div>
                </div>
            </section>

            <!-- 2. 邮件别名 -->
            <section class="card">
                <div class="card-header">
                    <div class="flex items-center gap-3">
                        <div class="icon-box bg-green-100 text-green-600 dark:bg-green-900/30">
                            <AtSign class="w-5 h-5" />
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white">邮件别名</h3>
                            <p class="text-xs text-gray-500">创建别名地址，所有发送到别名的邮件都会转发到你的主邮箱</p>
                        </div>
                    </div>
                    <button @click="showAliasForm = true" class="btn-secondary text-xs">
                        <Plus class="w-3 h-3 mr-1" /> 新增别名
                    </button>
                </div>

                <!-- 新增别名表单 -->
                <div v-if="showAliasForm" class="mt-4 p-4 border border-green-200 dark:border-green-800 rounded-lg bg-green-50 dark:bg-green-900/20">
                    <div class="mb-3">
                        <label class="block text-xs text-gray-500 mb-1">别名地址</label>
                        <div class="flex items-center gap-2">
                            <input v-model="newAliasPrefix" class="input-field flex-1" placeholder="support" />
                            <span class="text-gray-500 dark:text-gray-400">@{{ baseDomain }}</span>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="block text-xs text-gray-500 mb-1">备注名称（可选）</label>
                        <input v-model="newAliasName" class="input-field" placeholder="客服邮箱" />
                    </div>
                    <div v-if="aliasError" class="text-red-500 text-xs mb-2">{{ aliasError }}</div>
                    <div class="flex gap-2">
                        <button @click="addAlias" :disabled="aliasLoading || !newAliasPrefix.trim()" class="btn-primary text-xs disabled:opacity-50">
                            <Loader2 v-if="aliasLoading" class="w-3 h-3 mr-1 animate-spin" />
                            保存
                        </button>
                        <button @click="showAliasForm = false; aliasError = ''" class="btn-secondary text-xs">取消</button>
                    </div>
                </div>

                <!-- 别名列表 -->
                <div class="mt-4 space-y-2">
                    <div v-for="alias in aliases" :key="alias.id"
                        class="flex items-center justify-between p-3 border rounded-lg transition-colors"
                        :class="alias.is_active
                            ? 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
                            : 'border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 opacity-60'">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                <AtSign class="w-4 h-4 text-green-600 dark:text-green-400" />
                            </div>
                            <div>
                                <div class="font-medium text-gray-900 dark:text-white text-sm">{{ alias.alias_email }}</div>
                                <div class="text-xs text-gray-500">{{ alias.name || '未命名' }}</div>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span v-if="alias.is_active" class="text-xs text-green-600 bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded">启用</span>
                            <span v-else class="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">禁用</span>
                            <button @click="toggleAliasActive(alias)"
                                class="p-1.5 rounded-lg transition-colors"
                                :class="alias.is_active ? 'text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20' : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'"
                                :title="alias.is_active ? '点击禁用' : '点击启用'">
                                <Power class="w-4 h-4" />
                            </button>
                            <button @click="removeAlias(alias)" class="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title="删除">
                                <Trash2 class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    <div v-if="aliases.length === 0" class="text-gray-500 text-sm py-4 text-center">
                        暂无别名，点击上方按钮新增
                    </div>
                </div>
            </section>

            <!-- 3. 自动回复 -->
            <section class="card">
                <div class="card-header">
                    <div class="flex items-center gap-3">
                        <div class="icon-box bg-purple-100 text-purple-600 dark:bg-purple-900/30">
                            <Calendar class="w-5 h-5" />
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white">自动回复 / 休假模式</h3>
                            <p class="text-xs text-gray-500">在特定时间段自动回复收到的邮件</p>
                        </div>
                    </div>
                    <CommonToggle v-model="settings.auto_reply_enabled" @update:model-value="saveSettings" />
                </div>

                <div v-if="settings.auto_reply_enabled" class="mt-4 space-y-3 pt-4 border-t border-gray-100 dark:border-gray-800">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-1">
                            <label class="text-xs text-gray-500">开始时间</label>
                            <input type="date" v-model="settings.auto_reply_start_date" @change="saveSettings" class="input-field">
                        </div>
                        <div class="space-y-1">
                            <label class="text-xs text-gray-500">结束时间</label>
                            <input type="date" v-model="settings.auto_reply_end_date" @change="saveSettings" class="input-field">
                        </div>
                    </div>
                    <textarea v-model="settings.auto_reply_message" @blur="saveSettings" class="input-field h-20" placeholder="自动回复内容：您好，我现在不在办公室..."></textarea>
                </div>
            </section>

            <!-- 3. 服务器设置 -->
            <section class="card">
                <div class="card-header">
                    <div class="flex items-center gap-3">
                        <div class="icon-box bg-orange-100 text-orange-600 dark:bg-orange-900/30">
                            <Server class="w-5 h-5" />
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white">POP / IMAP / SMTP</h3>
                            <p class="text-xs text-gray-500">配置第三方客户端连接</p>
                        </div>
                    </div>
                </div>
                <div class="mt-4 space-y-4">
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                        <div>
                            <div class="text-sm font-medium dark:text-white">IMAP / SMTP 服务</div>
                            <div class="text-xs text-gray-500 mt-0.5">系统默认开启，支持所有标准邮件客户端</div>
                        </div>
                        <div class="flex items-center gap-2 text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400 px-3 py-1 rounded-full text-xs font-medium">
                            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            运行中
                        </div>
                    </div>
                    <div class="text-xs text-gray-500 font-mono bg-gray-100 dark:bg-gray-900 p-3 rounded select-all">
                        IMAP Server: {{ mailServer }} (Port: 993)<br>
                        SMTP Server: {{ mailServer }} (Port: 465)
                    </div>
                </div>
            </section>
        </template>
    </div>
</template>

<style scoped>
/* 通用样式，建议提取到全局 CSS，这里为了方便直接写 */
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6;
}

.card-header {
    @apply flex items-center justify-between;
}

.icon-box {
    @apply p-2 rounded-lg;
}

.input-field {
    @apply w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm dark:text-white transition-all;
}

.btn-secondary {
    @apply px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center text-gray-700 dark:text-gray-300;
}

.btn-primary {
    @apply px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors flex items-center;
}
</style>