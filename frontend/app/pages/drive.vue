<script setup lang="ts">
import { Upload, Trash2, Share2, Link, Copy, Check, Download, X, Lock, Unlock, Eye, FolderPlus, Folder, ChevronRight, Home, Pencil, ArrowRight, Loader2 } from 'lucide-vue-next'
const config = useConfig()
useHead({ title: `文件中转站 - ${config.appName}` })
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { getDriveFiles, uploadDriveFile, deleteDriveFile, createDriveFolder, moveDriveItem, renameDriveItem, createDriveShare, removeDriveShare, downloadDriveFileUrl, previewDriveFileUrl, token } = useApi()

const files = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const limit = 20
const loading = ref(true)
const uploading = ref(false)
const loadError = ref('')
const breadcrumbs = ref<{ id: number; name: string }[]>([])

// 当前文件夹
const currentFolderId = ref<number | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))

// 分享弹窗
const showShareModal = ref(false)
const shareFile = ref<any>(null)
const shareSettings = ref({ is_public: true, password: '', expires_days: 7 })
const sharing = ref(false)
const copied = ref(false)

// 新建文件夹弹窗
const showFolderModal = ref(false)
const newFolderName = ref('')
const creatingFolder = ref(false)

// 重命名弹窗
const showRenameModal = ref(false)
const renameTarget = ref<any>(null)
const renameName = ref('')
const renaming = ref(false)

// 移动弹窗
const showMoveModal = ref(false)
const moveTarget = ref<any>(null)
const moveTargetParentId = ref<number | null>(null)
const moveFolders = ref<any[]>([])
const moveBreadcrumbs = ref<{ id: number; name: string }[]>([])
const moving = ref(false)
const loadingMoveFolders = ref(false)

const loadFiles = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getDriveFiles(page.value, limit, currentFolderId.value)
    files.value = res.items
    total.value = res.total
    breadcrumbs.value = res.breadcrumbs || []
  } catch (e: any) {
    console.error('加载失败', e)
    loadError.value = e.data?.detail || '加载文件失败'
    toast.error(loadError.value)
  } finally {
    loading.value = false
  }
}

const goPage = (p: number) => {
  if (p < 1 || p > totalPages.value || p === page.value) return
  page.value = p
  loadFiles()
}

const navigateToFolder = (folderId: number | null) => {
  currentFolderId.value = folderId
  page.value = 1
  loadFiles()
}

const uploadProgress = ref('')  // 上传进度文本

const handleUpload = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return

  const fileList = Array.from(input.files)
  uploading.value = true
  let successCount = 0
  try {
    for (let i = 0; i < fileList.length; i++) {
      uploadProgress.value = fileList.length > 1 ? `(${i + 1}/${fileList.length})` : ''
      const result = await uploadDriveFile(fileList[i], currentFolderId.value)
      files.value.unshift(result)
      successCount++
    }
    toast.success(`成功上传 ${successCount} 个文件`)
  } catch (e: any) {
    toast.error('上传失败: ' + (e.data?.detail || '未知错误'))
  } finally {
    uploading.value = false
    uploadProgress.value = ''
    input.value = ''
  }
}

const handleDelete = async (id: number) => {
  const item = files.value.find(f => f.id === id)
  const msg = item?.is_folder ? '确定删除此文件夹及其所有内容？' : '确定删除此文件？'
  const ok = await confirmDialog({ message: msg, type: 'danger' })
  if (!ok) return
  try {
    await deleteDriveFile(id)
    files.value = files.value.filter(f => f.id !== id)
    toast.success('删除成功')
  } catch (e: any) {
    console.error('删除失败', e)
    toast.error(e.data?.detail || '删除失败')
  }
}

// --- 新建文件夹 ---
const handleCreateFolder = async () => {
  const name = newFolderName.value.trim()
  if (!name) return
  creatingFolder.value = true
  try {
    const folder = await createDriveFolder(name, currentFolderId.value)
    files.value.unshift(folder)
    showFolderModal.value = false
    newFolderName.value = ''
    toast.success('文件夹已创建')
  } catch (e: any) {
    toast.error(e.data?.detail || '创建文件夹失败')
  } finally {
    creatingFolder.value = false
  }
}

// --- 重命名 ---
const openRenameModal = (item: any) => {
  renameTarget.value = item
  renameName.value = item.original_filename
  showRenameModal.value = true
}
const handleRename = async () => {
  if (!renameTarget.value || !renameName.value.trim()) return
  renaming.value = true
  try {
    const updated = await renameDriveItem(renameTarget.value.id, renameName.value.trim())
    const idx = files.value.findIndex(f => f.id === updated.id)
    if (idx >= 0) files.value[idx] = updated
    showRenameModal.value = false
    toast.success('重命名成功')
  } catch (e: any) {
    toast.error(e.data?.detail || '重命名失败')
  } finally {
    renaming.value = false
  }
}

// --- 移动 ---
const openMoveModal = async (item: any) => {
  moveTarget.value = item
  moveTargetParentId.value = null
  showMoveModal.value = true
  await loadMoveFolders(null)
}
const loadMoveFolders = async (parentId: number | null) => {
  loadingMoveFolders.value = true
  try {
    const res = await getDriveFiles(1, 200, parentId)
    // 只显示文件夹，且排除正在移动的项自身
    moveFolders.value = (res.items || []).filter((f: any) => f.is_folder && f.id !== moveTarget.value?.id)
    moveBreadcrumbs.value = res.breadcrumbs || []
    moveTargetParentId.value = parentId
  } catch (e: any) {
    toast.error('加载文件夹失败')
  } finally {
    loadingMoveFolders.value = false
  }
}
const handleMove = async () => {
  if (!moveTarget.value) return
  // 不能移动到自身所在的相同位置
  if (moveTargetParentId.value === moveTarget.value.parent_id) {
    toast.error('文件已在此位置')
    return
  }
  moving.value = true
  try {
    const updated = await moveDriveItem(moveTarget.value.id, moveTargetParentId.value)
    // 从当前列表中移除
    files.value = files.value.filter(f => f.id !== updated.id)
    showMoveModal.value = false
    toast.success('移动成功')
  } catch (e: any) {
    toast.error(e.data?.detail || '移动失败')
  } finally {
    moving.value = false
  }
}

// --- 分享 ---
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

// 预览
const showPreview = ref(false)
const previewFile = ref<any>(null)

const openPreview = (file: any) => {
  previewFile.value = file
  showPreview.value = true
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
        <div class="flex items-center gap-2">
          <button @click="showFolderModal = true; newFolderName = ''"
            class="flex items-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <FolderPlus class="w-4 h-4" /> 新建文件夹
          </button>
          <label class="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-hover cursor-pointer flex items-center gap-2">
            <Upload class="w-4 h-4" />
            {{ uploading ? `上传中${uploadProgress}...` : '上传文件' }}
            <input type="file" multiple class="hidden" @change="handleUpload" :disabled="uploading" />
          </label>
        </div>
      </div>

      <!-- 面包屑导航 -->
      <div v-if="currentFolderId !== null" class="flex items-center gap-1 mb-4 text-sm flex-wrap">
        <button @click="navigateToFolder(null)" class="flex items-center gap-1 text-primary hover:underline">
          <Home class="w-4 h-4" /> 根目录
        </button>
        <template v-for="(crumb, idx) in breadcrumbs" :key="crumb.id">
          <ChevronRight class="w-4 h-4 text-gray-400 shrink-0" />
          <button
            v-if="idx < breadcrumbs.length - 1"
            @click="navigateToFolder(crumb.id)"
            class="text-primary hover:underline truncate max-w-[160px]"
          >{{ crumb.name }}</button>
          <span v-else class="text-gray-700 dark:text-gray-300 font-medium truncate max-w-[160px]">{{ crumb.name }}</span>
        </template>
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
          <p class="text-lg font-medium mb-1">{{ currentFolderId !== null ? '此文件夹为空' : '暂无文件' }}</p>
          <p class="text-sm text-gray-400">{{ currentFolderId !== null ? '上传文件或创建子文件夹' : '点击上方按钮上传文件，支持最大 50MB' }}</p>
        </div>
        <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
          <div v-for="file in files" :key="file.id" class="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
            <!-- 图标（文件夹可点击进入） -->
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
              :class="file.is_folder ? 'bg-amber-50 dark:bg-amber-900/20 cursor-pointer' : 'bg-gray-100 dark:bg-gray-800'"
              @click="file.is_folder && navigateToFolder(file.id)"
            >
              <Folder v-if="file.is_folder" class="w-5 h-5 text-amber-500" />
              <component v-else :is="getFileIcon(file.content_type)" class="w-5 h-5 text-gray-500" />
            </div>

            <!-- 文件信息 -->
            <div class="flex-1 min-w-0" :class="{ 'cursor-pointer': file.is_folder }" @click="file.is_folder && navigateToFolder(file.id)">
              <div class="font-medium text-gray-900 dark:text-white truncate">{{ file.original_filename }}</div>
              <div class="text-xs text-gray-500 flex items-center gap-3">
                <span v-if="!file.is_folder">{{ formatSize(file.size) }}</span>
                <span v-else class="text-amber-500">文件夹</span>
                <span>{{ formatDateShort(file.created_at) }}</span>
                <span v-if="file.share_code" class="flex items-center gap-1 text-primary">
                  <Link class="w-3 h-3" /> 已分享
                  <span v-if="file.download_count">({{ file.download_count }}次下载)</span>
                </span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center gap-1">
              <button v-if="!file.is_folder && isPreviewable(file.content_type)" @click="openPreview(file)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="预览" aria-label="预览">
                <Eye class="w-4 h-4" />
              </button>
              <button v-if="!file.is_folder" @click="downloadFile(file.id)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="下载" aria-label="下载">
                <Download class="w-4 h-4" />
              </button>
              <button @click="openRenameModal(file)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="重命名" aria-label="重命名">
                <Pencil class="w-4 h-4" />
              </button>
              <button @click="openMoveModal(file)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="移动" aria-label="移动">
                <ArrowRight class="w-4 h-4" />
              </button>
              <button v-if="!file.is_folder" @click="openShareModal(file)" class="p-2 text-gray-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="分享" aria-label="分享">
                <Share2 class="w-4 h-4" />
              </button>
              <button @click="handleDelete(file.id)" class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title="删除" aria-label="删除">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="!loading && totalPages > 1" class="flex items-center justify-between mt-4 px-4 py-3 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark">
        <span class="text-sm text-gray-500">共 {{ total }} 项</span>
        <div class="flex items-center gap-1">
          <button @click="goPage(page - 1)" :disabled="page <= 1"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
            上一页
          </button>
          <span class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400">{{ page }} / {{ totalPages }}</span>
          <button @click="goPage(page + 1)" :disabled="page >= totalPages"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
            下一页
          </button>
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

    <!-- 新建文件夹弹窗 -->
    <CommonModal v-model="showFolderModal" title="新建文件夹" width-class="w-full max-w-sm">
      <div class="space-y-4">
        <input v-model="newFolderName" placeholder="文件夹名称" maxlength="255"
          class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          @keyup.enter="handleCreateFolder" />
      </div>
      <template #footer>
        <button @click="showFolderModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">取消</button>
        <button @click="handleCreateFolder" :disabled="creatingFolder || !newFolderName.trim()"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="creatingFolder" class="w-4 h-4 animate-spin" />
          创建
        </button>
      </template>
    </CommonModal>

    <!-- 重命名弹窗 -->
    <CommonModal v-model="showRenameModal" title="重命名" width-class="w-full max-w-sm">
      <div class="space-y-4">
        <input v-model="renameName" placeholder="新名称" maxlength="255"
          class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          @keyup.enter="handleRename" />
      </div>
      <template #footer>
        <button @click="showRenameModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">取消</button>
        <button @click="handleRename" :disabled="renaming || !renameName.trim()"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="renaming" class="w-4 h-4 animate-spin" />
          确定
        </button>
      </template>
    </CommonModal>

    <!-- 移动弹窗 -->
    <CommonModal v-model="showMoveModal" :title="`移动「${moveTarget?.original_filename || ''}」`" width-class="w-full max-w-md">
      <div class="space-y-3">
        <!-- 移动目标面包屑 -->
        <div class="flex items-center gap-1 text-sm flex-wrap">
          <button @click="loadMoveFolders(null)" class="flex items-center gap-1 text-primary hover:underline">
            <Home class="w-3.5 h-3.5" /> 根目录
          </button>
          <template v-for="(crumb, idx) in moveBreadcrumbs" :key="crumb.id">
            <ChevronRight class="w-3.5 h-3.5 text-gray-400 shrink-0" />
            <button
              v-if="idx < moveBreadcrumbs.length - 1"
              @click="loadMoveFolders(crumb.id)"
              class="text-primary hover:underline truncate max-w-[120px]"
            >{{ crumb.name }}</button>
            <span v-else class="text-gray-700 dark:text-gray-300 font-medium truncate max-w-[120px]">{{ crumb.name }}</span>
          </template>
        </div>

        <!-- 文件夹列表 -->
        <div class="border border-gray-200 dark:border-gray-700 rounded-lg max-h-[300px] overflow-y-auto">
          <div v-if="loadingMoveFolders" class="p-6 text-center text-gray-400">
            <Loader2 class="w-5 h-5 mx-auto animate-spin" />
          </div>
          <div v-else-if="moveFolders.length === 0" class="p-6 text-center text-gray-400 text-sm">
            此目录下没有文件夹
          </div>
          <div v-else class="divide-y divide-gray-100 dark:divide-gray-800">
            <button v-for="folder in moveFolders" :key="folder.id"
              @click="loadMoveFolders(folder.id)"
              class="w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 text-left transition-colors">
              <Folder class="w-5 h-5 text-amber-500 shrink-0" />
              <span class="text-sm text-gray-900 dark:text-white truncate">{{ folder.original_filename }}</span>
              <ChevronRight class="w-4 h-4 text-gray-400 ml-auto shrink-0" />
            </button>
          </div>
        </div>
      </div>
      <template #footer>
        <button @click="showMoveModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">取消</button>
        <button @click="handleMove" :disabled="moving"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="moving" class="w-4 h-4 animate-spin" />
          移动到此处
        </button>
      </template>
    </CommonModal>

    <!-- 文件预览 -->
    <CommonFilePreview v-if="previewFile" v-model="showPreview"
      :file-url="previewDriveFileUrl(previewFile.id)"
      :filename="previewFile.original_filename"
      :content-type="previewFile.content_type"
      :token="token" />
  </div>
</template>
