<script setup lang="ts">
import { Camera } from 'lucide-vue-next'

const { getMe, updateMe } = useApi()

const user = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const message = ref('')

const form = reactive({
    displayName: '',
    signature: ''
})

const loadUser = async () => {
    try {
        user.value = await getMe()
        form.displayName = user.value.display_name || ''
    } catch (e) {
        console.error('加载用户信息失败', e)
    } finally {
        loading.value = false
    }
}

const handleSave = async () => {
    saving.value = true
    message.value = ''
    try {
        await updateMe({ display_name: form.displayName })
        message.value = '保存成功'
        setTimeout(() => message.value = '', 3000)
    } catch (e: any) {
        message.value = e.data?.detail || '保存失败'
    } finally {
        saving.value = false
    }
}

const getInitial = () => {
    if (user.value?.display_name) return user.value.display_name[0].toUpperCase()
    if (user.value?.email) return user.value.email[0].toUpperCase()
    return 'U'
}

onMounted(loadUser)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">账号信息</h2>

        <div v-if="loading" class="text-gray-500">加载中...</div>

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
                    <p class="text-sm text-gray-500 mb-3">支持 JPG, PNG 格式，最大 5MB</p>
                    <button class="btn-secondary">更换头像</button>
                </div>
            </div>

            <!-- 表单区域 -->
            <div class="space-y-6 max-w-lg">
                <div class="space-y-2">
                    <label class="form-label">显示名称</label>
                    <input v-model="form.displayName" type="text" class="input-field" placeholder="输入显示名称">
                </div>

                <div class="space-y-2">
                    <label class="form-label">邮箱地址</label>
                    <div class="relative">
                        <input type="text" :value="user.email" disabled
                            class="input-field bg-gray-50 dark:bg-gray-800/50 text-gray-500 cursor-not-allowed pr-12">
                        <span
                            class="absolute right-3 top-2.5 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">已验证</span>
                    </div>
                    <p class="text-xs text-gray-400">邮箱地址无法直接修改，请联系管理员。</p>
                </div>

                <div class="space-y-2">
                    <label class="form-label">个人签名</label>
                    <textarea v-model="form.signature"
                        class="input-field h-32 resize-none custom-scrollbar leading-relaxed"
                        placeholder="这个人很懒，什么都没写~"></textarea>
                    <p class="text-xs text-gray-400 text-right">{{ form.signature.length }} / 200</p>
                </div>
            </div>

            <!-- 消息提示 -->
            <div v-if="message" :class="['text-sm', message === '保存成功' ? 'text-green-600' : 'text-red-600']">
                {{ message }}
            </div>

            <!-- 底部保存 -->
            <div class="pt-4 border-t border-gray-100 dark:border-gray-800">
                <button @click="handleSave" :disabled="saving" class="btn-primary">
                    {{ saving ? '保存中...' : '保存更改' }}
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