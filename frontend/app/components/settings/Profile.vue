<script setup lang="ts">
import { Camera, ExternalLink, Link2, Loader2, ShieldCheck, ShieldOff } from 'lucide-vue-next'

const { getMe, updateMe, getMySsoStatus, getSSOLoginUrl } = useApi()
const toast = useToast()
const { t } = useI18n()
const route = useRoute()

const user = ref<AppUser | null>(null)
const loading = ref(true)
const saving = ref(false)
const message = ref('')
const bindingSso = ref(false)

// 认证中心绑定状态（TOTP 密钥在认证中心，这里仅展示状态）
const ssoStatus = ref<{ sso_bound: boolean; auth_center_url: string | null; auth_center_username: string | null; mfa_enabled: boolean; auth_center_session_active: boolean } | null>(null)

const loadSsoStatus = async () => {
    try {
        ssoStatus.value = await getMySsoStatus()
    } catch {
        ssoStatus.value = null
    }
}

const handleBindSso = async () => {
    bindingSso.value = true
    try {
        sessionStorage.setItem('sso_bind_return', route.fullPath || '/settings')
        const { redirect_url } = await getSSOLoginUrl('bind')
        window.location.href = redirect_url
    } catch (e: any) {
        bindingSso.value = false
        toast.error(e?.data?.detail || t('settings.profile.bindSsoFailed'))
    }
}

const mfaManageUrl = computed(() => {
    if (!ssoStatus.value?.sso_bound || !ssoStatus.value.auth_center_url) return ''
    return `${ssoStatus.value.auth_center_url}/profile`
})

const form = reactive({
    displayName: '',
    signature: ''
})

const loadUser = async () => {
    try {
        user.value = await getMe()
        form.displayName = user.value.display_name || ''
    } catch (e: any) {
        console.error('加载用户信息失败', e)
        toast.error(e.data?.detail || t('settings.common.loadUserFailed'))
    } finally {
        loading.value = false
    }
}

const handleSave = async () => {
    saving.value = true
    message.value = ''
    try {
        await updateMe({ display_name: form.displayName })
        message.value = t('settings.profile.saved')
        setTimeout(() => message.value = '', 3000)
    } catch (e: any) {
        message.value = e.data?.detail || t('settings.profile.saveFailed')
    } finally {
        saving.value = false
    }
}

const getInitial = () => {
    if (user.value?.display_name) return user.value.display_name[0].toUpperCase()
    if (user.value?.email) return user.value.email[0].toUpperCase()
    return 'U'
}

onMounted(() => {
    loadUser()
    loadSsoStatus()
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">{{ t('settings.tabs.profile') }}</h2>

        <div v-if="loading" class="text-gray-500">{{ t('settings.common.loading') }}</div>

        <template v-else-if="user">
            <!-- 头像区域 -->
            <div class="flex items-center gap-6">
                <div class="relative group cursor-pointer">
                    <div
                        class="w-24 h-24 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-4xl text-white font-bold shadow-xl shadow-primary/20">
                        {{ getInitial() }}
                    </div>
                    <div
                        class="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Camera class="w-8 h-8 text-white" />
                    </div>
                </div>
                <div>
                    <h3 class="font-bold text-lg text-gray-900 dark:text-white">{{ user.display_name || user.email }}</h3>
                    <p class="text-sm text-gray-500 mb-3">{{ t('settings.profile.avatarHint') }}</p>
                    <button class="btn-secondary">{{ t('settings.profile.changeAvatar') }}</button>
                </div>
            </div>

            <!-- 表单区域 -->
            <div class="space-y-6 max-w-lg">
                <div class="space-y-2">
                    <label class="form-label">{{ t('settings.profile.displayName') }}</label>
                    <input v-model="form.displayName" type="text" class="input-field" :placeholder="t('settings.profile.displayNamePlaceholder')">
                </div>

                <div class="space-y-2">
                    <label class="form-label">{{ t('settings.profile.email') }}</label>
                    <div class="relative">
                        <input type="text" :value="user.email" disabled
                            class="input-field bg-gray-50 dark:bg-gray-800/50 text-gray-500 cursor-not-allowed pr-12">
                        <span
                            class="absolute right-3 top-2.5 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">{{ t('settings.profile.verified') }}</span>
                    </div>
                    <p class="text-xs text-gray-400">{{ t('settings.profile.emailReadonly') }}</p>
                </div>

                <!-- 认证中心绑定状态 -->
                <div class="space-y-2">
                    <label class="form-label">{{ t('settings.profile.ssoBinding') }}</label>
                    <div
                        class="flex items-center justify-between gap-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/40 px-4 py-3">
                        <div class="flex items-start gap-3">
                            <Link2 class="w-5 h-5 mt-0.5"
                                :class="ssoStatus?.sso_bound ? 'text-green-600' : 'text-gray-400'" />
                            <div>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">
                                    {{ ssoStatus?.sso_bound ? t('settings.profile.ssoBound') : t('settings.profile.ssoUnbound') }}
                                </p>
                                <p v-if="ssoStatus?.sso_bound && ssoStatus.auth_center_username" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    {{ t('settings.profile.authCenterAccount') }}<span class="font-mono text-gray-700 dark:text-gray-300">{{ ssoStatus.auth_center_username }}</span>
                                </p>
                                <p v-if="ssoStatus?.sso_bound" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    {{ t('settings.profile.totpLabel') }}
                                    <span :class="ssoStatus.mfa_enabled ? 'text-green-600 font-medium' : 'text-amber-600'"
                                        class="inline-flex items-center gap-1 align-middle">
                                        <ShieldCheck v-if="ssoStatus.mfa_enabled" class="w-3.5 h-3.5" />
                                        <ShieldOff v-else class="w-3.5 h-3.5" />
                                        {{ ssoStatus.mfa_enabled ? t('settings.profile.mfaOn') : t('settings.profile.mfaOff') }}
                                    </span>
                                </p>
                                <p v-else class="text-xs text-gray-400 mt-0.5">
                                    {{ t('settings.profile.ssoHint') }}
                                </p>
                            </div>
                        </div>
                        <div class="flex items-center gap-2 shrink-0">
                            <button v-if="!ssoStatus?.sso_bound" type="button" class="btn-primary text-sm inline-flex items-center gap-1.5"
                                :disabled="bindingSso" @click="handleBindSso">
                                <Loader2 v-if="bindingSso" class="w-4 h-4 animate-spin" />
                                <Link2 v-else class="w-4 h-4" />
                                {{ bindingSso ? t('settings.profile.bindingSso') : t('settings.profile.bindSso') }}
                            </button>
                            <a v-if="ssoStatus?.sso_bound && mfaManageUrl" :href="mfaManageUrl" target="_blank"
                                class="btn-secondary shrink-0 inline-flex items-center gap-1.5 text-sm">
                                <ExternalLink class="w-4 h-4" /> {{ t('settings.profile.manageInAuthCenter') }}
                            </a>
                        </div>
                    </div>
                    <p class="text-xs text-gray-400">
                        {{ t('settings.profile.totpNote') }}
                    </p>
                </div>

                <div class="space-y-2">
                    <label class="form-label">{{ t('settings.profile.signature') }}</label>
                    <textarea v-model="form.signature"
                        class="input-field h-32 resize-none custom-scrollbar leading-relaxed"
                        :placeholder="t('settings.profile.signaturePlaceholder')"></textarea>
                    <p class="text-xs text-gray-400 text-right">{{ form.signature.length }} / 200</p>
                </div>
            </div>

            <!-- 消息提示 -->
            <div v-if="message" :class="['text-sm', message === t('settings.profile.saved') ? 'text-green-600' : 'text-red-600']">
                {{ message }}
            </div>

            <!-- 底部保存 -->
            <div class="pt-4 border-t border-gray-100 dark:border-gray-800">
                <button @click="handleSave" :disabled="saving" class="btn-primary">
                    {{ saving ? t('settings.common.saving') : t('settings.profile.saveChanges') }}
                </button>
            </div>
        </template>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.form-label {
    @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}

.input-field {
    @apply w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all text-gray-900 dark:text-white text-sm;
}

.btn-primary {
    @apply px-8 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-hover transition-all shadow-lg shadow-primary/20 font-medium active:scale-95 disabled:opacity-50;
}

.btn-secondary {
    @apply px-4 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 text-xs rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors;
}
</style>