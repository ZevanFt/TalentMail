<script setup lang="ts">
import { User, Plus, Lock } from 'lucide-vue-next'

const { getMe } = useApi()

const loading = ref(true)
const user = ref<any>(null)

const loadUser = async () => {
    try {
        user.value = await getMe()
    } catch (e: any) {
        console.error('加载用户信息失败', e)
    } finally {
        loading.value = false
    }
}

const getInitial = () => {
    if (user.value?.display_name) return user.value.display_name[0].toUpperCase()
    if (user.value?.email) return user.value.email.split('@')[0][0].toUpperCase()
    return 'U'
}

onMounted(loadUser)
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
                    <h3 class="font-bold text-gray-900 dark:text-white">邮件别名 (Aliases)</h3>
                    <span class="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded flex items-center gap-1">
                        <Lock class="w-3 h-3" /> 即将推出
                    </span>
                </div>
                <div class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                    别名功能正在开发中，敬请期待...
                </div>
            </div>
        </template>
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