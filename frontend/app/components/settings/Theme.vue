<script setup lang="ts">
import { Crown, Upload, X, RotateCcw, Palette, Eye, EyeOff, Check } from 'lucide-vue-next'

const {
    settings: bgSettings,
    isLoading: bgLoading,
    canUseBackground,
    subscriptionChecked,
    uploadImage,
    clearBackground,
    updateSettings: updateBgSettings,
    updateAreas,
    resetToDefault: resetBg,
    previewBackground,
    clearPreview
} = useBackground()

const { isDark, toggleTheme } = useTheme()

// 预览图片状态
const previewImage = ref<string | null>(null)
const isApplying = ref(false)

// 消息提示
const message = ref<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)
const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    message.value = { type, text }
    setTimeout(() => {
        message.value = null
    }, 3000)
}

// 文件上传处理
const fileInput = ref<HTMLInputElement>()
const handleFileSelect = (event: Event) => {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (!file) return

    handleImageUpload(file)
}

const handleDrop = (event: DragEvent) => {
    event.preventDefault()
    const file = event.dataTransfer?.files?.[0]
    if (!file) return

    handleImageUpload(file)
}

const handleDragOver = (event: DragEvent) => {
    event.preventDefault()
}

// 图片上传逻辑 - 所有用户都先预览，再应用
const handleImageUpload = async (file: File) => {
    try {
        // 所有用户都先预览，点击应用后再保存
        const dataUrl = await uploadImage(file, true) // previewOnly = true
        previewImage.value = dataUrl
        if (canUseBackground.value) {
            showMessage('info', '预览效果，点击"应用背景"按钮保存')
        } else {
            showMessage('info', '预览模式：需要订阅会员才能保存')
        }
    } catch (error: any) {
        showMessage('error', error.message || '上传失败')
    }
}

const triggerFileSelect = () => {
    fileInput.value?.click()
}

// 清除背景
const handleClearBackground = () => {
    if (previewImage.value) {
        previewImage.value = null
        clearPreview()
    } else {
        clearBackground()
    }
    // 关键修复：重置 file input 以便可以重新选择同一文件
    if (fileInput.value) {
        fileInput.value.value = ''
    }
}

// 重置为默认
const handleResetBackground = () => {
    previewImage.value = null
    clearPreview()
    resetBg()
}

// 透明度调节
const handleOpacityChange = (value: number) => {
    if (canUseBackground.value) {
        updateBgSettings({ opacity: value })
    } else {
        // 预览模式下也要更新设置，但不保存
        bgSettings.value.opacity = value
        if (previewImage.value) {
            previewBackground(previewImage.value)
        }
    }
}

// 模糊度调节
const handleBlurChange = (value: number) => {
    if (canUseBackground.value) {
        updateBgSettings({ blur: value })
    } else {
        bgSettings.value.blur = value
        if (previewImage.value) {
            previewBackground(previewImage.value)
        }
    }
}

// 叠加层透明度调节
const handleOverlayChange = (value: number) => {
    if (canUseBackground.value) {
        updateBgSettings({ overlayOpacity: value })
    } else {
        bgSettings.value.overlayOpacity = value
        if (previewImage.value) {
            previewBackground(previewImage.value)
        }
    }
}

// 区域切换
const handleAreaToggle = (area: keyof typeof bgSettings.value.areas) => {
    if (canUseBackground.value) {
        updateAreas(area, !bgSettings.value.areas[area])
    } else {
        bgSettings.value.areas[area] = !bgSettings.value.areas[area]
        if (previewImage.value) {
            previewBackground(previewImage.value)
        }
    }
}

const showApplyConfirm = () => {
    if (!canUseBackground.value) {
        showMessage('error', '此功能需要订阅会员')
        return
    }
    
    if (!previewImage.value) return
    
    // 直接应用，不需要确认对话框
    confirmApplyBackground()
}

const confirmApplyBackground = async () => {
    isApplying.value = true
    try {
        if (previewImage.value) {
            // 将预览图片转换为正式背景
            const file = await dataURLtoFile(previewImage.value, 'background.jpg')
            await uploadImage(file)
            previewImage.value = null
            showMessage('success', '背景已应用')
        }
    } catch (error: any) {
        showMessage('error', error.message || '应用失败')
    } finally {
        isApplying.value = false
    }
}

// 工具函数：将 DataURL 转换为 File
const dataURLtoFile = (dataurl: string, filename: string): Promise<File> => {
    return new Promise((resolve, reject) => {
        const arr = dataurl.split(',')
        if (arr.length < 2 || !arr[0] || !arr[1]) {
            reject(new Error('Invalid dataURL format'))
            return
        }
        const mimeMatch = arr[0].match(/:(.*?);/)
        const mime = mimeMatch?.[1] || 'image/jpeg'
        const base64Data = arr[1]
        const bstr = atob(base64Data)
        let n = bstr.length
        const u8arr = new Uint8Array(n)
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n)
        }
        resolve(new File([u8arr], filename, { type: mime }))
    })
}

// 当前显示的背景图片
const currentBackgroundImage = computed(() => {
    return previewImage.value || bgSettings.value.imageUrl || undefined
})

// 是否有背景图片
const hasBackgroundImage = computed(() => {
    return !!(previewImage.value || bgSettings.value.imageUrl)
})

// 在组件挂载时输出调试信息（开发调试用）
onMounted(() => {
    console.log('[Theme] Mounted - canUseBackground:', canUseBackground.value, 'subscriptionChecked:', subscriptionChecked.value)
})
</script>

<template>
    <div class="space-y-8">
        <!-- 消息提示 -->
        <Transition name="slide-down">
            <div v-if="message" class="fixed top-4 right-4 z-50 max-w-sm">
                <div class="rounded-lg shadow-lg border p-4"
                    :class="{
                        'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400': message.type === 'success',
                        'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400': message.type === 'error',
                        'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-400': message.type === 'info'
                    }">
                    <div class="flex items-center gap-2">
                        <Check v-if="message.type === 'success'" class="w-4 h-4" />
                        <X v-else-if="message.type === 'error'" class="w-4 h-4" />
                        <Eye v-else class="w-4 h-4" />
                        <span class="text-sm font-medium">{{ message.text }}</span>
                    </div>
                </div>
            </div>
        </Transition>

        <!-- 主题切换 -->
        <div class="card bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="section-title mb-0">主题模式</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">选择浅色或深色主题</p>
                </div>
                <button @click="toggleTheme"
                    class="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    <Palette class="w-4 h-4" />
                    <span class="text-sm font-medium">{{ isDark ? '深色模式' : '浅色模式' }}</span>
                </button>
            </div>
        </div>

        <!-- 自定义背景 -->
        <div class="card bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <h2 class="section-title mb-0">自定义背景</h2>
                    <span v-if="!canUseBackground && subscriptionChecked"
                        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                        <Crown class="w-3 h-3" />
                        会员功能
                    </span>
                </div>
            </div>

            <!-- 背景图片上传区域 -->
            <div class="space-y-6">
                <!-- 图片预览/上传区域 - 添加 data-bg-preview 属性保护 -->
                <div class="relative" data-bg-preview>
                    <div v-if="hasBackgroundImage"
                        class="relative w-full h-64 rounded-xl overflow-hidden border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800"
                        data-bg-preview>
                        <img :src="currentBackgroundImage" alt="背景预览"
                            class="w-full h-full object-contain bg-gray-100 dark:bg-gray-800"
                            data-bg-preview />
                        
                        <!-- 预览标签 -->
                        <div v-if="previewImage && !canUseBackground"
                            class="absolute top-3 left-3 px-2 py-1 rounded bg-amber-500 text-white text-xs font-medium flex items-center gap-1"
                            data-bg-preview>
                            <Eye class="w-3 h-3" />
                            预览模式
                        </div>
                        
                        <!-- 操作按钮 -->
                        <div class="absolute top-3 right-3 flex gap-2" data-bg-preview>
                            <button @click="triggerFileSelect"
                                class="p-2 rounded-lg bg-white/90 dark:bg-gray-800/90 text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800 shadow-sm transition-colors"
                                title="更换图片"
                                data-bg-preview>
                                <Upload class="w-4 h-4" />
                            </button>
                            <button @click="handleClearBackground"
                                class="p-2 rounded-lg bg-white/90 dark:bg-gray-800/90 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 shadow-sm transition-colors"
                                title="清除背景"
                                data-bg-preview>
                                <X class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    
                    <!-- 上传区域 -->
                    <div v-else
                        @drop="handleDrop"
                        @dragover="handleDragOver"
                        @click="triggerFileSelect"
                        class="w-full h-64 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer flex flex-col items-center justify-center gap-3"
                        data-bg-preview>
                        <Upload class="w-8 h-8 text-gray-400" />
                        <div class="text-center">
                            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">点击上传或拖拽图片到此处</p>
                            <p class="text-xs text-gray-500 mt-1">支持 JPG、PNG 格式，最大 10MB</p>
                        </div>
                    </div>
                    
                    <input ref="fileInput" type="file" accept="image/*" @change="handleFileSelect" class="hidden" />
                </div>

                <!-- 背景设置 -->
                <div v-if="hasBackgroundImage" class="space-y-6">
                    <!-- 透明度 -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            背景透明度: {{ bgSettings.opacity }}%
                        </label>
                        <input type="range" min="10" max="100" :value="bgSettings.opacity"
                            @input="handleOpacityChange(Number(($event.target as HTMLInputElement).value))"
                            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 slider" />
                    </div>

                    <!-- 模糊度 -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            模糊度: {{ bgSettings.blur }}px
                        </label>
                        <input type="range" min="0" max="20" :value="bgSettings.blur"
                            @input="handleBlurChange(Number(($event.target as HTMLInputElement).value))"
                            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 slider" />
                    </div>

                    <!-- 叠加层透明度 -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            叠加层透明度: {{ bgSettings.overlayOpacity }}%
                        </label>
                        <p class="text-xs text-gray-500 mb-2">用于增强文字可读性</p>
                        <input type="range" min="0" max="100" :value="bgSettings.overlayOpacity"
                            @input="handleOverlayChange(Number(($event.target as HTMLInputElement).value))"
                            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 slider" />
                    </div>

                    <!-- 显示区域 -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">显示区域</label>
                        <div class="grid grid-cols-2 gap-3">
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" :checked="bgSettings.areas.header"
                                    @change="handleAreaToggle('header')"
                                    class="rounded border-gray-300 text-primary focus:ring-primary" />
                                <span class="text-sm text-gray-700 dark:text-gray-300">顶部栏</span>
                            </label>
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" :checked="bgSettings.areas.sidebar"
                                    @change="handleAreaToggle('sidebar')"
                                    class="rounded border-gray-300 text-primary focus:ring-primary" />
                                <span class="text-sm text-gray-700 dark:text-gray-300">侧边栏</span>
                            </label>
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" :checked="bgSettings.areas.main"
                                    @change="handleAreaToggle('main')"
                                    class="rounded border-gray-300 text-primary focus:ring-primary" />
                                <span class="text-sm text-gray-700 dark:text-gray-300">主内容区</span>
                            </label>
                            <label class="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" :checked="bgSettings.areas.panels"
                                    @change="handleAreaToggle('panels')"
                                    class="rounded border-gray-300 text-primary focus:ring-primary" />
                                <span class="text-sm text-gray-700 dark:text-gray-300">面板/卡片</span>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <button @click="handleResetBackground"
                        class="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
                        <RotateCcw class="w-4 h-4" />
                        重置为默认
                    </button>
                    
                    <div class="flex items-center gap-3">
                        <!-- 已保存状态（没有预览图时显示） -->
                        <span v-if="canUseBackground && hasBackgroundImage && !previewImage" class="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                            <Check class="w-4 h-4" />
                            背景已保存
                        </span>
                        
                        <!-- 有权限用户的应用按钮（有预览图时显示） -->
                        <button
                            v-if="canUseBackground && previewImage"
                            @click="confirmApplyBackground"
                            :disabled="isApplying"
                            class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                            <Check class="w-4 h-4" />
                            {{ isApplying ? '应用中...' : '应用背景' }}
                        </button>
                        
                        <!-- 非会员预览模式下的升级按钮 -->
                        <button
                            v-if="!canUseBackground && previewImage"
                            @click="showApplyConfirm"
                            :disabled="isApplying"
                            class="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                            <Crown class="w-4 h-4" />
                            {{ isApplying ? '应用中...' : '升级会员以保存' }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- 会员提示 -->
            <div v-if="!canUseBackground && subscriptionChecked && (bgSettings.imageUrl || previewImage)"
                class="mt-4 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                <div class="flex items-start gap-3">
                    <Crown class="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
                    <div>
                        <h4 class="font-medium text-amber-800 dark:text-amber-400 mb-1">会员专享功能</h4>
                        <p class="text-sm text-amber-700 dark:text-amber-500 mb-3">
                            自定义背景是会员专享功能。当前为预览模式，升级会员后可保存和使用自定义背景。
                        </p>
                        <NuxtLink to="/billing"
                            class="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium">
                            <Crown class="w-4 h-4" />
                            升级会员
                        </NuxtLink>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-lg font-bold text-gray-900 dark:text-white;
}

.slider::-webkit-slider-thumb {
    @apply appearance-none w-5 h-5 bg-primary rounded-full cursor-pointer;
}

.slider::-moz-range-thumb {
    @apply w-5 h-5 bg-primary rounded-full cursor-pointer border-0;
}

.slide-down-enter-active,
.slide-down-leave-active {
    transition: all 0.3s ease;
}

.slide-down-enter-from {
    opacity: 0;
    transform: translateY(-20px);
}

.slide-down-leave-to {
    opacity: 0;
    transform: translateY(-20px);
}
</style>