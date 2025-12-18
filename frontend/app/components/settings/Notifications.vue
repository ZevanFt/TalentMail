<script setup lang="ts">
import { BellRing, Volume2, Smartphone, Loader2 } from 'lucide-vue-next'

const { getMe, updateMe } = useApi()

const loading = ref(true)
const saving = ref(false)
const settings = reactive({
    enable_desktop_notifications: true,
    enable_sound_notifications: true,
    enable_pool_notifications: false
})

const loadSettings = async () => {
    try {
        const user = await getMe()
        settings.enable_desktop_notifications = user.enable_desktop_notifications
        settings.enable_sound_notifications = user.enable_sound_notifications
        settings.enable_pool_notifications = user.enable_pool_notifications
    } catch (e) {
        console.error('加载设置失败', e)
    } finally {
        loading.value = false
    }
}

const updateSetting = async (key: 'enable_desktop_notifications' | 'enable_sound_notifications' | 'enable_pool_notifications', value: boolean) => {
    saving.value = true
    try {
        await updateMe({ [key]: value } as any)
    } catch (e: any) {
        console.error('保存设置失败', e)
        // 回滚
        settings[key] = !value
    } finally {
        saving.value = false
    }
}

onMounted(loadSettings)
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">通知偏好</h2>

        <div v-if="loading" class="text-gray-500">加载中...</div>

        <div v-else
            class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark divide-y divide-gray-100 dark:divide-gray-800">

            <!-- 桌面通知 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex gap-4">
                    <div class="p-2 bg-green-100 text-green-600 rounded-lg h-fit">
                        <BellRing class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">桌面通知</div>
                        <div class="text-sm text-gray-500">收到新邮件时在浏览器显示弹窗</div>
                    </div>
                </div>
                <CommonToggle v-model="settings.enable_desktop_notifications"
                    @update:model-value="updateSetting('enable_desktop_notifications', $event)" />
            </div>

            <!-- 提示音 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex gap-4">
                    <div class="p-2 bg-yellow-100 text-yellow-600 rounded-lg h-fit">
                        <Volume2 class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">提示音效</div>
                        <div class="text-sm text-gray-500">播放 "Ding" 提示音</div>
                    </div>
                </div>
                <CommonToggle v-model="settings.enable_sound_notifications"
                    @update:model-value="updateSetting('enable_sound_notifications', $event)" />
            </div>

            <!-- 账号池通知 -->
            <div class="p-6 flex items-center justify-between">
                <div class="flex gap-4">
                    <div class="p-2 bg-purple-100 text-purple-600 rounded-lg h-fit">
                        <Smartphone class="w-5 h-5" />
                    </div>
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white">账号池验证码推送</div>
                        <div class="text-sm text-gray-500">当临时账号收到验证码时，发送系统级通知</div>
                    </div>
                </div>
                <CommonToggle v-model="settings.enable_pool_notifications"
                    @update:model-value="updateSetting('enable_pool_notifications', $event)" />
            </div>

        </div>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}
</style>