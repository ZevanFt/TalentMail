<script setup lang="ts">
import { Paperclip, Download, Trash2, FileText, Image, File, Upload, Link, Check, Loader2 } from 'lucide-vue-next'
const config = useConfig()
const { t } = useI18n()
useHead({ title: computed(() => `${t('attachments.title')} - ${config.appName}`) })
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { getAttachments, uploadAttachment, downloadAttachmentUrl, deleteAttachment } = useApi()

interface Attachment { id: number; filename: string; content_type: string; size: number; email_id?: number; email_subject?: string }
const attachments = ref<Attachment[]>([])
const total = ref(0)
const page = ref(1)
const limit = 50
const loading = ref(true)
const uploading = ref(false)
const loadError = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))

const loadAttachments = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getAttachments(page.value, limit)
    attachments.value = res.items
    total.value = res.total
  } catch (e: any) {
    console.error('加载附件失败', e)
    loadError.value = e.data?.detail || t('attachments.loadFailed')
    toast.error(loadError.value)
  } finally { loading.value = false }
}

const goPage = (p: number) => {
  if (p < 1 || p > totalPages.value || p === page.value) return
  page.value = p
  loadAttachments()
}

const handleUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  const file = files[0]
  if (!file) return

  uploading.value = true
  try {
    await uploadAttachment(file)
    toast.success(t('attachments.uploadSuccess'))
    await loadAttachments()
  } catch (e: any) {
    console.error('上传失败', e)
    toast.error(e.data?.detail || t('attachments.uploadFailed'))
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
    await copyToClipboard(url)
    copiedId.value = id
    setTimeout(() => copiedId.value = null, 2000)
  } catch (e: any) {
    console.error('复制失败', e)
    toast.error(t('attachments.copyFailed'))
  }
}

// 分类
const transferFiles = computed(() => attachments.value.filter(a => !a.email_id))
const emailAttachments = computed(() => attachments.value.filter(a => a.email_id))

// formatSize 来自 utils/format.ts (Nuxt 自动导入)

const getIcon = (type: string) => {
  if (type.startsWith('image/')) return Image
  if (type.includes('pdf') || type.includes('document')) return FileText
  return File
}

const download = (id: number) => {
  secureDownload(downloadAttachmentUrl(id))
}

const remove = async (id: number) => {
  const ok = await confirmDialog({ message: t('attachments.confirmDelete'), type: 'danger' })
  if (!ok) return
  try {
    await deleteAttachment(id)
    await loadAttachments()
  } catch (e: any) {
    console.error('删除附件失败', e)
    toast.error(e.data?.detail || t('attachments.deleteFailed'))
  }
}

onMounted(loadAttachments)
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50 dark:bg-bg-dark">
    <header class="flex items-center justify-between px-6 py-4 border-b dark:border-border-dark bg-white dark:bg-bg-panelDark">
      <h1 class="text-xl font-bold">{{ t('attachments.headerTitle') }}</h1>
      <div class="flex items-center gap-2">
        <input type="file" ref="fileInput" class="hidden" @change="handleUpload">
        <button @click="triggerUpload" :disabled="uploading" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50">
          <Upload v-if="!uploading" class="w-4 h-4" />
          <Loader2 v-else class="w-4 h-4 animate-spin" />
          {{ uploading ? t('attachments.uploading') : t('attachments.uploadFile') }}
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-auto p-6">
      <!-- 骨架屏 -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 6" :key="i" class="flex items-center gap-4 p-4 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark animate-pulse">
          <div class="w-10 h-10 rounded-lg bg-gray-200 dark:bg-gray-700 shrink-0" />
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-40" />
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24" />
          </div>
          <div class="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
      <div v-else-if="loadError" class="text-center py-12">
        <p class="text-red-500 mb-3">{{ loadError }}</p>
        <button @click="loadAttachments" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">{{ t('attachments.retry') }}</button>
      </div>
      <div v-else-if="attachments.length === 0" class="text-center py-12 text-gray-500">
        <Paperclip class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p class="text-lg font-medium mb-1">{{ t('attachments.empty') }}</p>
        <p class="text-sm text-gray-400">{{ t('attachments.emptyHint') }}</p>
      </div>
      <div v-else class="space-y-8">
        <!-- 中转站文件 -->
        <div v-if="transferFiles.length > 0">
          <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
            <Upload class="w-5 h-5 text-primary" />
            {{ t('attachments.transferTitle') }}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="a in transferFiles" :key="a.id" class="bg-white dark:bg-bg-panelDark rounded-lg p-4 shadow-sm border dark:border-border-dark flex flex-col">
              <div class="flex items-start gap-3 mb-3">
                <component :is="getIcon(a.content_type)" class="w-10 h-10 text-gray-400 shrink-0" />
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate" :title="a.filename">{{ a.filename }}</div>
                  <div class="text-sm text-gray-500">{{ formatSize(a.size) }}</div>
                </div>
              </div>
              <div class="mt-auto flex items-center justify-end gap-2 pt-3 border-t dark:border-border-dark">
                <button @click="copyLink(a.id)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400" :title="copiedId === a.id ? t('attachments.copied') : t('attachments.copyLink')">
                  <Check v-if="copiedId === a.id" class="w-4 h-4 text-green-500" />
                  <Link v-else class="w-4 h-4" />
                </button>
                <button @click="download(a.id)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400" :title="t('attachments.download')">
                  <Download class="w-4 h-4" />
                </button>
                <button @click="remove(a.id)" class="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded text-red-500" :title="t('common.delete')">
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
            {{ t('attachments.emailTitle') }}
          </h2>
          <div class="space-y-2">
            <div v-for="a in emailAttachments" :key="a.id" class="flex items-center gap-4 bg-white dark:bg-bg-panelDark rounded-lg p-4 shadow-sm border dark:border-border-dark">
              <component :is="getIcon(a.content_type)" class="w-8 h-8 text-gray-400 shrink-0" />
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">{{ a.filename }}</div>
                <div class="text-sm text-gray-500">{{ formatSize(a.size) }}</div>
              </div>
              <div class="flex gap-2 shrink-0">
                <button @click="download(a.id)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" :title="t('attachments.download')">
                  <Download class="w-4 h-4" />
                </button>
                <!-- 邮件附件通常不允许直接删除，除非删除邮件 -->
              </div>
            </div>
          </div>
        </div>
        <!-- 分页 -->
        <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 bg-white dark:bg-bg-panelDark rounded-xl border dark:border-border-dark">
          <span class="text-sm text-gray-500">{{ t('attachments.totalItems', { n: total }) }}</span>
          <div class="flex items-center gap-1">
            <button @click="goPage(page - 1)" :disabled="page <= 1"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              {{ t('attachments.prevPage') }}
            </button>
            <span class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400">{{ page }} / {{ totalPages }}</span>
            <button @click="goPage(page + 1)" :disabled="page >= totalPages"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              {{ t('attachments.nextPage') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>