<script setup lang="ts">
import { ShieldAlert, ImageOff, Lock, Plus } from 'lucide-vue-next'

const { getMe, updateMe } = useApi()

const user = ref<any>(null)
const loading = ref(true)
const saving = ref(false)

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

onMounted(() => {
    loadUser()
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
                <button class="text-primary text-sm font-medium flex items-center gap-1">
                    <Plus class="w-4 h-4" /> 添加
                </button>
            </div>
            <div class="text-sm text-gray-500 italic p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                暂无屏蔽的邮箱地址
            </div>
        </div>

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