<script setup lang="ts">
import { Download, Lock, FileText, Image, Film, Music, Archive, File } from 'lucide-vue-next'

const route = useRoute()
const code = route.params.code as string
const { getShareInfo, downloadSharedFileUrl } = useApi()

const file = ref<any>(null)
const loading = ref(true)
const error = ref('')
const password = ref('')
const needPassword = ref(false)
const downloading = ref(false)

const loadShare = async () => {
  loading.value = true
  error.value = ''
  try {
    file.value = await getShareInfo(code, password.value || undefined)
    needPassword.value = false
  } catch (e: any) {
    if (e.data?.detail === '需要密码') {
      needPassword.value = true
    } else if (e.data?.detail === '密码错误') {
      error.value = '密码错误'
    } else {
      error.value = e.data?.detail || '分享链接无效或已过期'
    }
  } finally {
    loading.value = false
  }
}

const download = () => {
  downloading.value = true
  const url = downloadSharedFileUrl(code, password.value || undefined)
  window.open(url, '_blank')
  setTimeout(() => downloading.value = false, 1000)
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getFileIcon = (contentType: string | null) => {
  if (!contentType) return File
  if (contentType.startsWith('image/')) return Image
  if (contentType.startsWith('video/')) return Film
  if (contentType.startsWith('audio/')) return Music
  if (contentType.includes('zip') || contentType.includes('rar')) return Archive
  if (contentType.includes('pdf') || contentType.includes('text')) return FileText
  return File
}

onMounted(loadShare)
</script>

<template>
  <div class="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-md">
      <!-- 加载中 -->
      <div v-if="loading" class="text-center py-8 text-gray-500">加载中...</div>
      
      <!-- 需要密码 -->
      <div v-else-if="needPassword" class="text-center">
        <Lock class="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <h2 class="text-lg font-bold mb-2">此文件需要密码</h2>
        <input v-model="password" type="password" placeholder="请输入访问密码" class="w-full px-4 py-2 border rounded-lg mb-3 dark:bg-gray-700 dark:border-gray-600" @keyup.enter="loadShare" />
        <div v-if="error" class="text-red-500 text-sm mb-3">{{ error }}</div>
        <button @click="loadShare" class="w-full py-2 bg-primary text-white rounded-lg hover:bg-primary-hover">验证</button>
      </div>
      
      <!-- 错误 -->
      <div v-else-if="error" class="text-center py-8">
        <div class="text-red-500 mb-2">{{ error }}</div>
      </div>
      
      <!-- 文件信息 -->
      <div v-else-if="file" class="text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
          <component :is="getFileIcon(file.content_type)" class="w-8 h-8 text-gray-500" />
        </div>
        <h2 class="text-lg font-bold mb-1 break-all">{{ file.original_filename }}</h2>
        <p class="text-sm text-gray-500 mb-6">{{ formatSize(file.size) }}</p>
        <button @click="download" :disabled="downloading" class="w-full py-3 bg-primary text-white rounded-lg hover:bg-primary-hover flex items-center justify-center gap-2 disabled:opacity-50">
          <Download class="w-5 h-5" />
          {{ downloading ? '下载中...' : '下载文件' }}
        </button>
        <p class="text-xs text-gray-400 mt-4">已下载 {{ file.download_count }} 次</p>
      </div>
    </div>
  </div>
</template>