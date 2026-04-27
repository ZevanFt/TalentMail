<script setup lang="ts">
import { Upload, Loader2, CheckCircle, AlertCircle, FileText, Inbox } from 'lucide-vue-next'

const { importEmails, getFolders } = useApi()
const toast = useToast()

const file = ref<File | null>(null)
const folderId = ref<number | undefined>(undefined)
const importing = ref(false)
const result = ref<{
  total_found: number
  imported: number
  skipped_duplicate: number
  skipped_error: number
  errors: string[]
} | null>(null)

const folders = ref<{ id: number; name: string; role: string }[]>([])
const loadingFolders = ref(true)

const loadFolders = async () => {
  loadingFolders.value = true
  try {
    const res = await getFolders()
    folders.value = res || []
  } catch (e: any) {
    console.error('加载文件夹失败', e)
  } finally {
    loadingFolders.value = false
  }
}

const handleFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    file.value = input.files[0]
    result.value = null
  }
}

const handleImport = async () => {
  if (!file.value) return
  importing.value = true
  result.value = null
  try {
    result.value = await importEmails(file.value, folderId.value)
    if (result.value.imported > 0) {
      toast.success(`成功导入 ${result.value.imported} 封邮件`)
    } else if (result.value.skipped_duplicate > 0) {
      toast.info('所有邮件已存在，无需重复导入')
    }
  } catch (e: any) {
    console.error('导入失败', e)
    toast.error(e.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

const reset = () => {
  file.value = null
  result.value = null
  const input = document.getElementById('import-file') as HTMLInputElement
  if (input) input.value = ''
}

onMounted(loadFolders)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-bold text-gray-900 dark:text-white">邮件导入</h2>
      <p class="text-sm text-gray-500 mt-1">上传 .eml 或 .mbox 文件，将邮件导入到指定文件夹（单次最多 500 封，50MB）</p>
    </div>

    <!-- 上传区域 -->
    <div class="bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark space-y-4">
      <!-- 文件选择 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">选择文件</label>
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm">
            <FileText class="w-4 h-4 text-gray-500" />
            {{ file ? file.name : '选择 .eml 或 .mbox 文件' }}
            <input id="import-file" type="file" accept=".eml,.mbox" class="hidden" @change="handleFileChange" />
          </label>
          <span v-if="file" class="text-xs text-gray-400">{{ formatSize(file.size) }}</span>
        </div>
      </div>

      <!-- 目标文件夹 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">导入到</label>
        <div class="flex items-center gap-2">
          <Inbox class="w-4 h-4 text-gray-400" />
          <select v-model="folderId"
            class="flex-1 px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
            <option :value="undefined">收件箱（默认）</option>
            <option v-for="f in folders" :key="f.id" :value="f.id">{{ f.name }}</option>
          </select>
        </div>
      </div>

      <!-- 导入按钮 -->
      <button @click="handleImport" :disabled="!file || importing"
        class="flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium disabled:opacity-50">
        <Loader2 v-if="importing" class="w-4 h-4 animate-spin" />
        <Upload v-else class="w-4 h-4" />
        {{ importing ? '导入中...' : '开始导入' }}
      </button>
    </div>

    <!-- 结果面板 -->
    <div v-if="result" class="bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark space-y-4">
      <div class="flex items-center gap-2">
        <CheckCircle v-if="result.imported > 0" class="w-5 h-5 text-green-500" />
        <AlertCircle v-else class="w-5 h-5 text-amber-500" />
        <h3 class="text-sm font-bold text-gray-900 dark:text-white">导入结果</h3>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ result.total_found }}</div>
          <div class="text-xs text-gray-500">发现邮件</div>
        </div>
        <div class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
          <div class="text-2xl font-bold text-green-600">{{ result.imported }}</div>
          <div class="text-xs text-green-600">成功导入</div>
        </div>
        <div class="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg text-center">
          <div class="text-2xl font-bold text-amber-600">{{ result.skipped_duplicate }}</div>
          <div class="text-xs text-amber-600">跳过重复</div>
        </div>
        <div class="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-center">
          <div class="text-2xl font-bold text-red-600">{{ result.skipped_error }}</div>
          <div class="text-xs text-red-600">解析失败</div>
        </div>
      </div>

      <!-- 错误列表 -->
      <div v-if="result.errors.length > 0" class="space-y-2">
        <div class="text-sm font-medium text-red-500">错误详情：</div>
        <div class="max-h-[200px] overflow-y-auto space-y-1">
          <div v-for="(err, idx) in result.errors" :key="idx"
            class="text-xs text-red-600 bg-red-50 dark:bg-red-900/20 px-3 py-1.5 rounded">
            {{ err }}
          </div>
        </div>
      </div>

      <button @click="reset" class="text-sm text-primary hover:underline">继续导入</button>
    </div>
  </div>
</template>
