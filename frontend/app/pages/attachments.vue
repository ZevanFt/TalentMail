<script setup lang="ts">
import { Paperclip, Download, Trash2, FileText, Image, File, Upload, Link, Check } from 'lucide-vue-next'

const { downloadAttachmentUrl, deleteAttachment, token } = useApi()

interface Attachment { id: number; filename: string; content_type: string; size: number; email_id?: number; email_subject?: string }
const attachments = ref<Attachment[]>([])
const loading = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const loadAttachments = async () => {
  loading.value = true
  try {
    const res = await $fetch<Attachment[]>('/api/attachments/list', {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    attachments.value = res
  } catch {} finally { loading.value = false }
}

const handleUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  const file = files[0]
  if (!file) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    await $fetch('/api/attachments/upload', {
      method: 'POST',
      body: formData,
      headers: { Authorization: `Bearer ${token.value}` }
    })
    await loadAttachments()
  } catch (e) {
    console.error('上传失败', e)
    alert('上传失败')
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const triggerUpload = () => {
  fileInput.value?.click()
}

// 复制链接状态
const copiedId = ref<number | null>(null)
const copyLink = async (id: number) => {
  const url = `${window.location.origin}${downloadAttachmentUrl(id)}`
  try {
    await navigator.clipboard.writeText(url)
    copiedId.value = id
    setTimeout(() => copiedId.value = null, 2000)
  } catch (e) {
    console.error('复制失败', e)
  }
}

// 分类
const transferFiles = computed(() => attachments.value.filter(a => !a.email_id))
const emailAttachments = computed(() => attachments.value.filter(a => a.email_id))

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getIcon = (type: string) => {
  if (type.startsWith('image/')) return Image
  if (type.includes('pdf') || type.includes('document')) return FileText
  return File
}

const download = (id: number) => {
  window.open(downloadAttachmentUrl(id) + `?token=${token.value}`, '_blank')
}

const remove = async (id: number) => {
  if (!confirm('确定删除此附件？')) return
  try { await deleteAttachment(id); await loadAttachments() } catch {}
}

onMounted(loadAttachments)
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
    <header class="flex items-center justify-between px-6 py-4 border-b dark:border-gray-800 bg-white dark:bg-gray-900">
      <h1 class="text-xl font-bold">附件中心</h1>
      <div class="flex items-center gap-2">
        <input type="file" ref="fileInput" class="hidden" @change="handleUpload">
        <button @click="triggerUpload" :disabled="uploading" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50">
          <Upload v-if="!uploading" class="w-4 h-4" />
          <Loader2 v-else class="w-4 h-4 animate-spin" />
          {{ uploading ? '上传中...' : '上传文件' }}
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
      <div v-else-if="attachments.length === 0" class="text-center py-12 text-gray-500">
        <Paperclip class="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>暂无附件</p>
      </div>
      <div v-else class="space-y-8">
        <!-- 中转站文件 -->
        <div v-if="transferFiles.length > 0">
          <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
            <Upload class="w-5 h-5 text-primary" />
            文件中转站
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="a in transferFiles" :key="a.id" class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border dark:border-gray-700 flex flex-col">
              <div class="flex items-start gap-3 mb-3">
                <component :is="getIcon(a.content_type)" class="w-10 h-10 text-gray-400 shrink-0" />
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate" :title="a.filename">{{ a.filename }}</div>
                  <div class="text-sm text-gray-500">{{ formatSize(a.size) }}</div>
                </div>
              </div>
              <div class="mt-auto flex items-center justify-end gap-2 pt-3 border-t dark:border-gray-700">
                <button @click="copyLink(a.id)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400" :title="copiedId === a.id ? '已复制' : '复制链接'">
                  <Check v-if="copiedId === a.id" class="w-4 h-4 text-green-500" />
                  <Link v-else class="w-4 h-4" />
                </button>
                <button @click="download(a.id)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400" title="下载">
                  <Download class="w-4 h-4" />
                </button>
                <button @click="remove(a.id)" class="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded text-red-500" title="删除">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 邮件附件 -->
        <div v-if="emailAttachments.length > 0">
          <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
            <Paperclip class="w-5 h-5 text-gray-500" />
            邮件附件
          </h2>
          <div class="space-y-2">
            <div v-for="a in emailAttachments" :key="a.id" class="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border dark:border-gray-700">
              <component :is="getIcon(a.content_type)" class="w-8 h-8 text-gray-400 shrink-0" />
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">{{ a.filename }}</div>
                <div class="text-sm text-gray-500">{{ formatSize(a.size) }}</div>
              </div>
              <div class="flex gap-2 shrink-0">
                <button @click="download(a.id)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="下载">
                  <Download class="w-4 h-4" />
                </button>
                <!-- 邮件附件通常不允许直接删除，除非删除邮件 -->
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>