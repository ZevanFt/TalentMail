<script setup lang="ts">
import { KeyRound, Smartphone, ShieldCheck, History, Laptop, Globe, X } from 'lucide-vue-next'

const { changePassword } = useApi()

const showPasswordModal = ref(false)
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const passwordForm = reactive({
    current: '',
    new: '',
    confirm: ''
})

const openPasswordModal = () => {
    passwordForm.current = ''
    passwordForm.new = ''
    passwordForm.confirm = ''
    message.value = ''
    showPasswordModal.value = true
}

const handleChangePassword = async () => {
    message.value = ''
    
    if (passwordForm.new !== passwordForm.confirm) {
        message.value = '两次输入的新密码不一致'
        messageType.value = 'error'
        return
    }
    
    if (passwordForm.new.length < 6) {
        message.value = '新密码至少需要6个字符'
        messageType.value = 'error'
        return
    }
    
    saving.value = true
    try {
        await changePassword(passwordForm.current, passwordForm.new)
        message.value = '密码修改成功'
        messageType.value = 'success'
        setTimeout(() => {
            showPasswordModal.value = false
        }, 1500)
    } catch (e: any) {
        message.value = e.data?.detail || '密码修改失败'
        messageType.value = 'error'
    } finally {
        saving.value = false
    }
}
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">登录与安全</h2>

        <!-- 1. 核心认证设置 -->
        <div class="card divide-y divide-gray-100 dark:divide-gray-800">

            <!-- 修改密码 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-purple-100 text-purple-600 dark:bg-purple-900/30">
                        <KeyRound class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">登录密码</div>
                        <div class="text-sm text-gray-500 mt-0.5">建议定期更换密码以保护账号安全</div>
                    </div>
                </div>
                <button @click="openPasswordModal" class="btn-secondary">修改密码</button>
            </div>

            <!-- 两步验证 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-green-100 text-green-600 dark:bg-green-900/30">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">两步验证 (2FA)</div>
                        <div class="text-sm text-gray-500 mt-0.5">使用 Authenticator App 进行二次确认</div>
                    </div>
                </div>
                <button class="btn-primary">立即启用</button>
            </div>

            <!-- 备用邮箱 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="icon-box bg-blue-100 text-blue-600 dark:bg-blue-900/30">
                        <ShieldCheck class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">安全辅助邮箱</div>
                        <div class="text-sm text-gray-500 mt-0.5">用于找回密码或接收安全通知</div>
                    </div>
                </div>
                <div class="text-sm text-gray-400 mr-4">未设置</div>
            </div>
        </div>

        <!-- 2. 最近活动设备 -->
        <div class="space-y-4">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <History class="w-5 h-5 text-gray-500" />
                最近登录设备
            </h3>

            <div class="card p-0 overflow-hidden">
                <!-- 当前设备 -->
                <div
                    class="p-4 flex items-center justify-between bg-green-50/50 dark:bg-green-900/10 border-b border-gray-100 dark:border-gray-800">
                    <div class="flex items-center gap-4">
                        <Laptop class="w-8 h-8 text-green-600 dark:text-green-400" />
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                当前浏览器
                                <span
                                    class="px-2 py-0.5 bg-green-100 text-green-700 text-[10px] rounded-full">当前设备</span>
                            </div>
                            <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                                <Globe class="w-3 h-3" /> 刚刚
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 修改密码弹窗 -->
        <Teleport to="body">
            <div v-if="showPasswordModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <div class="bg-white dark:bg-bg-panelDark rounded-2xl shadow-2xl w-full max-w-md">
                    <div class="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-800">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">修改密码</h3>
                        <button @click="showPasswordModal = false" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                            <X class="w-5 h-5 text-gray-500" />
                        </button>
                    </div>
                    
                    <div class="p-6 space-y-4">
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">当前密码</label>
                            <input v-model="passwordForm.current" type="password" class="input-field" placeholder="输入当前密码">
                        </div>
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">新密码</label>
                            <input v-model="passwordForm.new" type="password" class="input-field" placeholder="输入新密码（至少6位）">
                        </div>
                        <div class="space-y-2">
                            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">确认新密码</label>
                            <input v-model="passwordForm.confirm" type="password" class="input-field" placeholder="再次输入新密码">
                        </div>
                        
                        <div v-if="message" :class="['text-sm', messageType === 'success' ? 'text-green-600' : 'text-red-600']">
                            {{ message }}
                        </div>
                    </div>
                    
                    <div class="flex justify-end gap-3 p-6 border-t border-gray-100 dark:border-gray-800">
                        <button @click="showPasswordModal = false" class="btn-secondary">取消</button>
                        <button @click="handleChangePassword" :disabled="saving" class="btn-primary">
                            {{ saving ? '保存中...' : '确认修改' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden;
}

.icon-box {
    @apply p-2.5 rounded-lg flex items-center justify-center;
}

.input-field {
    @apply w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all text-gray-900 dark:text-white text-sm;
}

.btn-primary {
    @apply px-4 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20 disabled:opacity-50;
}

.btn-secondary {
    @apply px-4 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors;
}
</style>