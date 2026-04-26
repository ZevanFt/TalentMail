<script setup lang="ts">
import { Upload, Trash2, Share2, Link, Copy, Check, Download, X, Lock, Unlock } from 'lucide-vue-next'
useHead({ title: '文件中转站 - TalentMail' })
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { getDriveFiles, uploadDriveFile, deleteDriveFile, createDriveShare, removeDriveShare, downloadDriveFileUrl, token } = useApi()
const config = useConfig()

const files = ref<any[]>([])
const loading = ref(true)
const uploading = ref(false)
const loadError = ref('')

// 分享弹窗
const showShareModal = ref(false)
const shareFile = ref<any>(null)
const shareSettings = ref({ is_public: true, password: '', expires_days: 7 })
const sharing = ref(false)
const copied = ref(false)

const loadFiles = async () => {
  loading.value = true
  loadError.value = ''
  try {
    files.value = await getDriveFiles()
  } catch (e: any) {
    console.error('加载失败', e)
    loadError.value = e.data?.detail || '加载文件失败'
    toast.error(loadError.value)
  } finally {
    loading.value = false
  }
}

const handleUpload = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  
  uploading.value = true
  try {
    for (const file of input.files) {
      const result = await uploadDriveFile(file)
      files.value.unshift(result)
    }
  } catch (e: any) {
    toast.error('上传失败: ' + (e.data?.detail || '未知错误'))
  } finally {
    uploading.value = false
    input.value = ''
  }
}

const handleDelete = async (id: number) => {
  const ok = await confirmDialog({ message: '确定删除此文件？', type: 'danger' })
  if (!ok) return
  try {
    await deleteDriveFile(id)
    files.value = files.value.filter(f => f.id !== id)
  } catch (e: any) {
    console.error('删除失败', e)
    toast.error(e.data?.detail || '删除失败')
  }
}

const openShareModal = (file: any) => {
  shareFile.value = file
  shareSettings.value = { is_public: true, password: '', expires_days: 7 }
  showShareModal.value = true
}

const handleShare = async () => {
  if (!shareFile.value) return
  sharing.value = true
  try {
    const result = await createDriveShare(shareFile.value.id, {
      is_public: shareSettings.value.is_public,
      password: shareSettings.value.password || undefined,
      expires_days: shareSettings.value.expires_days
    })
    // 更新文件列表中的分享信息
    const idx = files.value.findIndex(f => f.id === shareFile.value.id)
    if (idx >= 0) files.value[idx] = result
    shareFile.value = result
  } catch (e: any) {
    toast.error('分享失败: ' + (e.data?.detail || '未知错误'))
  } finally {
    sharing.value = false
  }
}

const handleRemoveShare = async () => {
  if (!shareFile.value) return
  try {
    await removeDriveShare(shareFile.value.id)
    const idx = files.value.findIndex(f => f.id === shareFile.value.id)
    if (idx >= 0) {
      files.value[idx].share_code = null
      files.value[idx].is_public = false
    }
    showShareModal.value = false
  } catch (e: any) {
    console.error('取消分享失败', e)
    toast.error(e.data?.detail || '取消分享失败')
  }
}

const getShareUrl = (code: string) => {
  return `${window.location.origin}/share/${code}`
}

const copyShareUrl = async () => {
  if (!shareFile.value?.share_code) return
  try {
    await copyToClipboard(getShareUrl(shareFile.value.share_code))
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch (e: any) {
    console.error('复制失败', e)
    toast.error('复制失败')
  }
}

const downloadFile = (id: number) => {
  secureDownload(downloadDriveFileUrl(id))
}

// formatSize 来自 utils/format.ts (Nuxt 自动导入)

const formatDateShort = (date: string) => {
  return new Date(date).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// getFileIcon 来自 utils/fileIcon.ts (Nuxt 自动导入)

onMounted(loadFiles)
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-bg-dark">
    <div class="max-w-5xl mx-auto p-6">
      <!-- 标题栏 -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">文件中转站</h1>
          <p class="text-sm text-gray-500 mt-1">上传文件并生成分享链接</p>
        </div>
        <label class="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-hover cursor-pointer flex items-center gap-2">
          <Upload class="w-4 h-4" />
          {{ uploading ? '上传中...' : '上传文件' }}
          <input type="file" multiple class="hidden" @change="handleUpload" :disabled="uploading" />
        </label>
      </div>

      <!-- 文件列表 -->
      <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark">
        <!-- 骨架屏 -->
        <div v-if="loading" class="divide-y divide-gray-100 dark:divide-gray-800">
          <div v-for="i in 5" :key="i" class="flex items-center gap-4 p-4 animate-pulse">
            <div class="w-10 h-10 rounded-lg bg-gray-200 dark:bg-gray-700 shrink-0" />
            <div class="flex-1 space-y-2">
              <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48" />
              <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32" />
            </div>
            <div class="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        </div>
        <div v-else-if="loadError" class="p-8 text-center">
          <p class="text-red-500 mb-3">{{ loadError }}</p>
          <button @click="loadFiles" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">重试</button>
        </div>
        <div v-else-if="files.length === 0" class="p-12 text-center text-gray-500">
          <Upload class="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p class="text-lg font-medium mb-1">暂无文件</p>
          <p class="text-sm text-gray-400">点击上方按钮上传文件，支持最大 50MB</p>
        </div>
        <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
          <div v-for="file in files" :key="file.id" class="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
            <!-- 图标 -->
            <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
              <component :is="getFileIcon(file.content_type)" class="w-5 h-5 text-gray-500" />
            </div>
            
            <!-- 文件信息 -->
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-900 dark:text-white truncate">{{ file.original_filename }}</div>
              <div class="text-xs text-gray-500 flex items-center gap-3">
                <span>{{ formatSize(file.size) }}</span>
                <span>{{ formatDateShort(file.created_at) }}</span>
                <span v-if="file.share_code" class="flex items-center gap-1 text-primary">
                  <Link class="w-3 h-3" /> 已分享
                  <span v-if="file.download_count">({{ file.download_count }}次下载)</span>
                </span>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex items-center gap-1">
              <button @click="downloadFile(file.id)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="下载" aria-label="下载">
                <Download class="w-4 h-4" />
              </button>
              <button @click="openShareModal(file)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="分享" aria-label="分享">
                <Share2 class="w-4 h-4" />
              </button>
              <button @click="handleDelete(file.id)" class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title="删除" aria-label="删除">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分享弹窗 -->
    <CommonModal v-model="showShareModal" title="分享文件" width-class="w-full max-w-md">
      <div v-if="shareFile" class="space-y-4">
        <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div class="font-medium text-gray-900 dark:text-white truncate">{{ shareFile.original_filename }}</div>
          <div class="text-xs text-gray-500">{{ formatSize(shareFile.size) }}</div>
        </div>

        <!-- 已有分享链接 -->
        <div v-if="shareFile.share_code" class="space-y-3">
          <div class="flex items-center gap-2">
            <input :value="getShareUrl(shareFile.share_code)" readonly class="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" />
            <button @click="copyShareUrl" class="px-3 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover flex items-center gap-1">
              <Check v-if="copied" class="w-4 h-4" />
              <Copy v-else class="w-4 h-4" />
            </button>
          </div>
          <div class="flex items-center justify-between text-xs text-gray-500">
            <span class="flex items-center gap-1">
              <Lock v-if="shareFile.share_password" class="w-3 h-3" />
              <Unlock v-else class="w-3 h-3" />
              {{ shareFile.share_password ? '有密码保护' : '无密码' }}
            </span>
            <span>{{ shareFile.download_count }} 次下载</span>
          </div>
          <button @click="handleRemoveShare" class="w-full py-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-sm">
            取消分享
          </button>
        </div>

        <!-- 创建分享 -->
        <div v-else class="space-y-3">
          <div>
            <label for="share-password" class="block text-sm text-gray-600 dark:text-gray-400 mb-1">访问密码（可选）</label>
            <input id="share-password" v-model="shareSettings.password" type="text" placeholder="留空则无需密码" class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm" />
          </div>
          <div>
            <label for="share-expires" class="block text-sm text-gray-600 dark:text-gray-400 mb-1">有效期</label>
            <select id="share-expires" v-model="shareSettings.expires_days" class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm">
              <option :value="1">1 天</option>
              <option :value="7">7 天</option>
              <option :value="30">30 天</option>
              <option :value="null">永久有效</option>
            </select>
          </div>
          <button @click="handleShare" :disabled="sharing" class="w-full py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50">
            {{ sharing ? '创建中...' : '创建分享链接' }}
          </button>
        </div>
      </div>
    </CommonModal>
  </div>
</template>