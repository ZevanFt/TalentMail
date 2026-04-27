<script setup lang="ts">
import { Loader2, AlertCircle } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  fileUrl: string
  filename: string
  contentType: string | null
  token?: string
}>()

const emit = defineEmits(['update:modelValue'])

const previewType = computed(() => getPreviewType(props.contentType))
const loading = ref(true)
const error = ref('')
const objectUrl = ref('')
const textContent = ref('')

const loadPreview = async () => {
  loading.value = true
  error.value = ''
  // 清理旧的 Object URL
  if (objectUrl.value && props.token) {
    URL.revokeObjectURL(objectUrl.value)
  }
  objectUrl.value = ''
  textContent.value = ''

  try {
    const headers: Record<string, string> = {}
    if (props.token) headers['Authorization'] = `Bearer ${props.token}`

    if (previewType.value === 'image' || previewType.value === 'pdf') {
      if (props.token) {
        // 需要认证: fetch blob → Object URL（img/iframe src 无法带 header）
        const res = await fetch(props.fileUrl, { headers })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const blob = await res.blob()
        objectUrl.value = URL.createObjectURL(blob)
      } else {
        objectUrl.value = props.fileUrl
      }
    } else if (previewType.value === 'text') {
      const res = await fetch(props.fileUrl, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const text = await res.text()
      // 限制显示长度，防止巨型文本卡死浏览器
      textContent.value = text.length > 500_000 ? text.slice(0, 500_000) + '\n\n… 内容过长，已截断' : text
    }
  } catch (e: any) {
    console.error('预览加载失败', e)
    error.value = e.message?.includes('415') ? '此文件类型不支持预览' : '预览加载失败'
  } finally {
    loading.value = false
  }
}

// 打开时加载
watch(() => props.modelValue, (open) => {
  if (open) loadPreview()
})

// 清理 Object URL
onUnmounted(() => {
  if (objectUrl.value && props.token) {
    URL.revokeObjectURL(objectUrl.value)
  }
})
</script>

<template>
  <CommonModal
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :title="filename"
    width-class="w-full max-w-4xl"
  >
    <div class="min-h-[200px] flex items-center justify-center">
      <!-- Loading -->
      <div v-if="loading" class="text-center py-12">
        <Loader2 class="w-8 h-8 mx-auto animate-spin text-primary" />
        <p class="mt-2 text-sm text-gray-500">加载预览中...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-12">
        <AlertCircle class="w-10 h-10 mx-auto text-red-400 mb-2" />
        <p class="text-red-500">{{ error }}</p>
      </div>

      <!-- Image -->
      <div v-else-if="previewType === 'image'" class="w-full flex items-center justify-center">
        <img
          :src="objectUrl"
          :alt="filename"
          class="max-w-full max-h-[70vh] object-contain rounded"
        />
      </div>

      <!-- PDF -->
      <div v-else-if="previewType === 'pdf'" class="w-full">
        <iframe :src="objectUrl" class="w-full h-[70vh] border-0 rounded" />
      </div>

      <!-- Text / Code -->
      <div v-else-if="previewType === 'text'" class="w-full">
        <pre class="w-full max-h-[70vh] overflow-auto p-4 bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 text-sm rounded-lg border border-gray-200 dark:border-gray-700 whitespace-pre-wrap break-words font-mono">{{ textContent }}</pre>
      </div>

      <!-- Unsupported -->
      <div v-else class="text-center py-12 text-gray-500">
        <AlertCircle class="w-10 h-10 mx-auto mb-2 opacity-50" />
        <p>此文件类型不支持预览</p>
      </div>
    </div>
  </CommonModal>
</template>
