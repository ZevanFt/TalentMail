<template>
  <div class="space-y-6">
    <!-- 标题和操作按钮 -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">更新日志</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">查看系统版本更新历史和功能变更</p>
      </div>
      <div class="flex items-center gap-3">
        <a
          href="https://github.com/ZevanFt/TalentMail"
          target="_blank"
          rel="noopener noreferrer"
          class="px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-2"
        >
          <Github class="w-4 h-4" />
          GitHub
        </a>
        <button
          v-if="isAdmin"
          @click="showEditor = true; editingItem = null"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus class="w-4 h-4" />
          发布新版本
        </button>
      </div>
    </div>

    <!-- 筛选器和操作按钮 -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-3">
        <select
          v-model="filterType"
          class="px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm"
        >
          <option value="">全部类型</option>
          <option value="release">正式版</option>
          <option value="hotfix">热修复</option>
          <option value="beta">测试版</option>
          <option value="alpha">预览版</option>
        </select>
        <select
          v-model="filterCategory"
          class="px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm"
        >
          <option value="">全部分类</option>
          <option value="feature">新功能</option>
          <option value="bugfix">Bug修复</option>
          <option value="improvement">优化改进</option>
          <option value="security">安全更新</option>
        </select>
        
        <!-- 排序按钮 -->
        <button
          @click="toggleSortOrder"
          class="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm flex items-center gap-2 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          :title="sortOrder === 'desc' ? '当前：最新优先，点击切换为最早优先' : '当前：最早优先，点击切换为最新优先'"
        >
          <ArrowDownUp class="w-4 h-4" />
          <span>{{ sortOrder === 'desc' ? '最新优先' : '最早优先' }}</span>
        </button>
        
        <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <input
            type="checkbox"
            v-model="showMajorOnly"
            class="rounded border-gray-300"
          />
          仅显示重大更新
        </label>
      </div>
      
      <!-- 展开/收起全部按钮 -->
      <div v-if="changelogs.length > 0" class="flex items-center gap-2">
        <button
          @click="expandAll"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title="展开全部"
        >
          展开全部
        </button>
        <span class="text-gray-300 dark:text-gray-600">|</span>
        <button
          @click="collapseAll"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title="收起全部"
        >
          收起全部
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="changelogs.length === 0" class="text-center py-12">
      <ClipboardList class="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
      <p class="text-gray-500 dark:text-gray-400">暂无更新日志</p>
    </div>

    <!-- 更新日志列表 - 手风琴效果 -->
    <div v-else class="space-y-3">
      <div
        v-for="log in changelogs"
        :key="log.id"
        class="card bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden transition-all duration-200"
      >
        <!-- 手风琴头部 - 可点击展开/收起 -->
        <div
          @click="toggleExpand(log.id)"
          class="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        >
          <div class="flex items-center gap-4 flex-1 min-w-0">
            <!-- 展开/收起图标 -->
            <ChevronRight
              class="w-4 h-4 text-gray-400 transition-transform duration-200 flex-shrink-0"
              :class="{ 'rotate-90': expandedIds.has(log.id) }"
            />
            
            <!-- 版本号 -->
            <span class="text-xl font-bold text-blue-600 dark:text-blue-400 flex-shrink-0">v{{ log.version }}</span>
            
            <!-- 类型标签 -->
            <span
              :class="getTypeBadgeClass(log.type)"
              class="px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0"
            >
              {{ getTypeLabel(log.type) }}
            </span>
            
            <!-- 重大更新标签 -->
            <span
              v-if="log.is_major"
              class="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 flex-shrink-0"
            >
              重大更新
            </span>
            
            <!-- 未发布标签 -->
            <span
              v-if="!log.is_published"
              class="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 flex-shrink-0"
            >
              未发布
            </span>
            
            <!-- 标题 - 收起时显示 -->
            <span
              v-if="!expandedIds.has(log.id)"
              class="text-gray-600 dark:text-gray-400 truncate"
            >
              {{ log.title }}
            </span>
          </div>
          
          <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 flex-shrink-0">
            <span v-if="log.author">{{ log.author }}</span>
            <span>{{ formatDate(log.published_at || log.created_at) }}</span>
            
            <!-- 管理员操作按钮 -->
            <div v-if="isAdmin" class="flex items-center gap-1" @click.stop>
              <button
                @click="editChangelog(log)"
                class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                title="编辑"
              >
                <Pencil class="w-4 h-4" />
              </button>
              <button
                v-if="!log.is_published"
                @click="publishLog(log)"
                class="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                title="发布"
              >
                <Rocket class="w-4 h-4" />
              </button>
              <button
                v-else
                @click="unpublishLog(log)"
                class="p-1.5 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg transition-colors"
                title="取消发布"
              >
                <Package class="w-4 h-4" />
              </button>
              <button
                @click="confirmDelete(log)"
                class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                title="删除"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- 手风琴内容 - 使用 CSS Grid 实现平滑展开/收起 -->
        <div
          class="grid transition-[grid-template-rows] duration-300 ease-out"
          :class="expandedIds.has(log.id) ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
        >
          <div class="overflow-hidden">
            <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <!-- 版本标题 -->
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">{{ log.title }}</h4>
              
              <!-- 标签 -->
              <div v-if="log.tags && log.tags.length > 0" class="flex flex-wrap gap-2 mb-4">
                <span
                  v-for="tag in log.tags"
                  :key="tag"
                  class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-400"
                >
                  #{{ tag }}
                </span>
              </div>

              <!-- 内容 (Markdown渲染) -->
              <div
                class="prose prose-sm dark:prose-invert max-w-none"
                v-html="renderMarkdown(log.content)"
              ></div>

              <!-- 破坏性变更 -->
              <div v-if="log.breaking_changes" class="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                <h5 class="font-semibold text-red-800 dark:text-red-200 mb-2 flex items-center gap-2">
                  <AlertTriangle class="w-4 h-4" />
                  破坏性变更
                </h5>
                <div
                  class="prose prose-sm dark:prose-invert max-w-none text-red-700 dark:text-red-300"
                  v-html="renderMarkdown(log.breaking_changes)"
                ></div>
              </div>

              <!-- 迁移说明 -->
              <div v-if="log.migration_notes" class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h5 class="font-semibold text-blue-800 dark:text-blue-200 mb-2 flex items-center gap-2">
                  <FileText class="w-4 h-4" />
                  迁移说明
                </h5>
                <div
                  class="prose prose-sm dark:prose-invert max-w-none text-blue-700 dark:text-blue-300"
                  v-html="renderMarkdown(log.migration_notes)"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore" class="flex justify-center">
        <button
          @click="loadMore"
          :disabled="loadingMore"
          class="px-6 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
        >
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div
      v-if="showEditor"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showEditor = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 class="text-lg font-semibold">{{ editingItem ? '编辑更新日志' : '发布新版本' }}</h3>
          <button @click="showEditor = false" class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
            <X class="w-5 h-5" />
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">版本号 *</label>
              <input
                v-model="form.version"
                type="text"
                placeholder="如 1.0.0"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">类型</label>
              <select
                v-model="form.type"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              >
                <option value="release">正式版</option>
                <option value="hotfix">热修复</option>
                <option value="beta">测试版</option>
                <option value="alpha">预览版</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分类</label>
              <select
                v-model="form.category"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              >
                <option value="">不分类</option>
                <option value="feature">新功能</option>
                <option value="bugfix">Bug修复</option>
                <option value="improvement">优化改进</option>
                <option value="security">安全更新</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">作者</label>
              <input
                v-model="form.author"
                type="text"
                placeholder="留空使用当前用户"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">标题 *</label>
            <input
              v-model="form.title"
              type="text"
              placeholder="更新标题"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">标签</label>
            <input
              v-model="tagsInput"
              type="text"
              placeholder="多个标签用逗号分隔，如：工作流,模板,API"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">更新内容 * (支持Markdown)</label>
            <textarea
              v-model="form.content"
              rows="8"
              placeholder="### 新功能&#10;- 功能1&#10;- 功能2&#10;&#10;### Bug修复&#10;- 修复了xxx问题"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">破坏性变更 (可选)</label>
            <textarea
              v-model="form.breaking_changes"
              rows="3"
              placeholder="如果有破坏性变更，请在这里说明"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">迁移说明 (可选)</label>
            <textarea
              v-model="form.migration_notes"
              rows="3"
              placeholder="如果需要用户手动操作，请在这里说明迁移步骤"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm"
            ></textarea>
          </div>

          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="form.is_major" class="rounded border-gray-300" />
              <span class="text-sm text-gray-700 dark:text-gray-300">标记为重大更新</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="form.is_published" class="rounded border-gray-300" />
              <span class="text-sm text-gray-700 dark:text-gray-300">立即发布</span>
            </label>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            @click="showEditor = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="saveChangelog"
            :disabled="saving || !form.version || !form.title || !form.content"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? '保存中...' : (editingItem ? '保存修改' : '发布') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showDeleteConfirm = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">确认删除</h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          确定要删除版本 <strong>{{ deletingItem?.version }}</strong> 的更新日志吗？此操作不可恢复。
        </p>
        <div class="flex justify-end gap-3">
          <button
            @click="showDeleteConfirm = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            取消
          </button>
          <button
            @click="deleteLog"
            :disabled="deleting"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Plus, ClipboardList, ChevronRight, Pencil, Rocket, Package, Trash2, AlertTriangle, FileText, X, ArrowDownUp, Github } from 'lucide-vue-next'

const { getChangelogs, createChangelog, updateChangelog, deleteChangelog: apiDeleteChangelog, publishChangelog, unpublishChangelog, getMe } = useApi()

interface Changelog {
  id: number
  version: string
  title: string
  content: string
  type: string
  category: string | null
  is_major: boolean
  is_published: boolean
  published_at: string | null
  author: string | null
  tags: string[] | null
  breaking_changes: string | null
  migration_notes: string | null
  created_at: string
  updated_at: string
}

const loading = ref(true)
const loadingMore = ref(false)
const saving = ref(false)
const deleting = ref(false)
const changelogs = ref<Changelog[]>([])
const page = ref(1)
const hasMore = ref(false)
const isAdmin = ref(false)

const filterType = ref('')
const filterCategory = ref('')
const showMajorOnly = ref(false)
const sortOrder = ref<'desc' | 'asc'>('desc')

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
}

const showEditor = ref(false)
const editingItem = ref<Changelog | null>(null)
const tagsInput = ref('')

// 手风琴展开状态
const expandedIds = ref<Set<number>>(new Set())

const toggleExpand = (id: number) => {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
  // 触发响应式更新
  expandedIds.value = new Set(expandedIds.value)
}

// 展开全部/收起全部
const expandAll = () => {
  expandedIds.value = new Set(changelogs.value.map(log => log.id))
}

const collapseAll = () => {
  expandedIds.value = new Set()
}

const showDeleteConfirm = ref(false)
const deletingItem = ref<Changelog | null>(null)

const form = ref({
  version: '',
  title: '',
  content: '',
  type: 'release',
  category: '',
  is_major: false,
  is_published: true,
  author: '',
  breaking_changes: '',
  migration_notes: ''
})

const loadData = async (reset = true) => {
  if (reset) {
    loading.value = true
    page.value = 1
  } else {
    loadingMore.value = true
  }

  try {
    const res = await getChangelogs({
      page: page.value,
      page_size: 10,
      type: filterType.value || undefined,
      category: filterCategory.value || undefined,
      is_major: showMajorOnly.value ? true : undefined,
      sort_order: sortOrder.value
    })
    
    if (reset) {
      changelogs.value = res.items
    } else {
      changelogs.value.push(...res.items)
    }
    hasMore.value = res.has_more
  } catch (e) {
    console.error('加载更新日志失败:', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  page.value++
  loadData(false)
}

const checkAdmin = async () => {
  try {
    const user = await getMe()
    isAdmin.value = user.role === 'admin'
  } catch (e) {
    isAdmin.value = false
  }
}

const editChangelog = (log: Changelog) => {
  editingItem.value = log
  form.value = {
    version: log.version,
    title: log.title,
    content: log.content,
    type: log.type,
    category: log.category || '',
    is_major: log.is_major,
    is_published: log.is_published,
    author: log.author || '',
    breaking_changes: log.breaking_changes || '',
    migration_notes: log.migration_notes || ''
  }
  tagsInput.value = log.tags?.join(', ') || ''
  showEditor.value = true
}

const saveChangelog = async () => {
  saving.value = true
  try {
    const tags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t)
    const data = {
      ...form.value,
      tags: tags.length > 0 ? tags : undefined,
      category: form.value.category || undefined,
      author: form.value.author || undefined,
      breaking_changes: form.value.breaking_changes || undefined,
      migration_notes: form.value.migration_notes || undefined
    }

    if (editingItem.value) {
      await updateChangelog(editingItem.value.id, data)
    } else {
      await createChangelog(data)
    }

    showEditor.value = false
    loadData()
    resetForm()
  } catch (e) {
    console.error('保存失败:', e)
    alert('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  form.value = {
    version: '',
    title: '',
    content: '',
    type: 'release',
    category: '',
    is_major: false,
    is_published: true,
    author: '',
    breaking_changes: '',
    migration_notes: ''
  }
  tagsInput.value = ''
  editingItem.value = null
}

const confirmDelete = (log: Changelog) => {
  deletingItem.value = log
  showDeleteConfirm.value = true
}

const deleteLog = async () => {
  if (!deletingItem.value) return
  deleting.value = true
  try {
    await apiDeleteChangelog(deletingItem.value.id)
    showDeleteConfirm.value = false
    deletingItem.value = null
    loadData()
  } catch (e) {
    console.error('删除失败:', e)
    alert('删除失败，请重试')
  } finally {
    deleting.value = false
  }
}

const publishLog = async (log: Changelog) => {
  try {
    await publishChangelog(log.id)
    loadData()
  } catch (e) {
    console.error('发布失败:', e)
    alert('发布失败，请重试')
  }
}

const unpublishLog = async (log: Changelog) => {
  try {
    await unpublishChangelog(log.id)
    loadData()
  } catch (e) {
    console.error('取消发布失败:', e)
    alert('取消发布失败，请重试')
  }
}

const getTypeBadgeClass = (type: string) => {
  const classes: Record<string, string> = {
    release: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    hotfix: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    beta: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    alpha: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  }
  return classes[type] || classes.release
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    release: '正式版',
    hotfix: '热修复',
    beta: '测试版',
    alpha: '预览版'
  }
  return labels[type] || type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 处理行内格式
const formatInline = (text: string): string => {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900 dark:text-white">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-sm font-mono">$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank">$1</a>')
}

const renderMarkdown = (content: string): string => {
  if (!content) return ''
  
  // 分段处理
  const lines = content.split('\n')
  const result: string[] = []
  let inList = false
  let listType = 'ul'
  
  for (const line of lines) {
    // 标题处理
    if (line.startsWith('### ')) {
      if (inList) { result.push(listType === 'ul' ? '</ul>' : '</ol>'); inList = false }
      result.push(`<h3 class="text-base font-semibold text-gray-800 dark:text-gray-200 mt-5 mb-3 flex items-center gap-2">${formatInline(line.slice(4))}</h3>`)
      continue
    }
    if (line.startsWith('## ')) {
      if (inList) { result.push(listType === 'ul' ? '</ul>' : '</ol>'); inList = false }
      result.push(`<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mt-5 mb-3">${formatInline(line.slice(3))}</h2>`)
      continue
    }
    if (line.startsWith('# ')) {
      if (inList) { result.push(listType === 'ul' ? '</ul>' : '</ol>'); inList = false }
      result.push(`<h1 class="text-xl font-bold text-gray-800 dark:text-gray-200 mt-5 mb-3">${formatInline(line.slice(2))}</h1>`)
      continue
    }
    
    // 无序列表处理
    if (line.match(/^[-*] /)) {
      if (!inList) {
        result.push('<ul class="space-y-2 my-3">')
        inList = true
        listType = 'ul'
      }
      const listContent = formatInline(line.replace(/^[-*] /, ''))
      result.push(`<li class="flex items-start gap-2 text-gray-700 dark:text-gray-300"><span class="text-blue-500 mt-1.5 flex-shrink-0">•</span><span>${listContent}</span></li>`)
      continue
    }
    
    // 有序列表处理
    const orderedMatch = line.match(/^(\d+)\. (.+)/)
    if (orderedMatch && orderedMatch[2]) {
      if (!inList) {
        result.push('<ol class="space-y-2 my-3 list-none">')
        inList = true
        listType = 'ol'
      }
      const listContent = formatInline(orderedMatch[2])
      result.push(`<li class="flex items-start gap-2 text-gray-700 dark:text-gray-300"><span class="text-blue-500 font-medium flex-shrink-0">${orderedMatch[1]}.</span><span>${listContent}</span></li>`)
      continue
    }
    
    // 空行
    if (line.trim() === '') {
      if (inList) { result.push(listType === 'ul' ? '</ul>' : '</ol>'); inList = false }
      result.push('<div class="h-2"></div>')
      continue
    }
    
    // 普通段落
    if (inList) { result.push(listType === 'ul' ? '</ul>' : '</ol>'); inList = false }
    result.push(`<p class="text-gray-700 dark:text-gray-300 my-2">${formatInline(line)}</p>`)
  }
  
  if (inList) result.push(listType === 'ul' ? '</ul>' : '</ol>')
  
  return result.join('')
}

watch([filterType, filterCategory, showMajorOnly, sortOrder], () => {
  loadData()
})

onMounted(() => {
  checkAdmin()
  loadData()
})
</script>