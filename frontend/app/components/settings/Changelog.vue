<template>
  <div class="space-y-6">
    <!-- 标题和操作按钮 -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('settingsSecurity.changelog.title') }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('settingsSecurity.changelog.desc') }}</p>
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
          {{ t('settingsSecurity.changelog.publishNew') }}
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
          <option value="">{{ t('settingsSecurity.changelog.allTypes') }}</option>
          <option value="release">{{ t('settingsSecurity.changelog.typeRelease') }}</option>
          <option value="hotfix">{{ t('settingsSecurity.changelog.typeHotfix') }}</option>
          <option value="beta">{{ t('settingsSecurity.changelog.typeBeta') }}</option>
          <option value="alpha">{{ t('settingsSecurity.changelog.typeAlpha') }}</option>
        </select>
        <select
          v-model="filterCategory"
          class="px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm"
        >
          <option value="">{{ t('settingsSecurity.changelog.allCategories') }}</option>
          <option value="feature">{{ t('settingsSecurity.changelog.catFeature') }}</option>
          <option value="bugfix">{{ t('settingsSecurity.changelog.catBugfix') }}</option>
          <option value="improvement">{{ t('settingsSecurity.changelog.catImprovement') }}</option>
          <option value="security">{{ t('settingsSecurity.changelog.catSecurity') }}</option>
        </select>
        
        <!-- 排序按钮 -->
        <button
          @click="toggleSortOrder"
          class="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm flex items-center gap-2 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          :title="sortOrder === 'desc' ? t('settingsSecurity.changelog.sortNewestHint') : t('settingsSecurity.changelog.sortOldestHint')"
        >
          <ArrowDownUp class="w-4 h-4" />
          <span>{{ sortOrder === 'desc' ? t('settingsSecurity.changelog.newestFirst') : t('settingsSecurity.changelog.oldestFirst') }}</span>
        </button>
        
        <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <input
            type="checkbox"
            v-model="showMajorOnly"
            class="rounded border-gray-300"
          />
          {{ t('settingsSecurity.changelog.majorOnly') }}
        </label>
      </div>
      
      <!-- 展开/收起全部按钮 -->
      <div v-if="changelogs.length > 0" class="flex items-center gap-2">
        <button
          @click="expandAll"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          :title="t('settingsSecurity.changelog.expandAll')"
        >
          {{ t('settingsSecurity.changelog.expandAll') }}
        </button>
        <span class="text-gray-300 dark:text-gray-600">|</span>
        <button
          @click="collapseAll"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          :title="t('settingsSecurity.changelog.collapseAll')"
        >
          {{ t('settingsSecurity.changelog.collapseAll') }}
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
      <p class="text-gray-500 dark:text-gray-400">{{ t('settingsSecurity.changelog.empty') }}</p>
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
              class="px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 whitespace-nowrap"
            >
              {{ getTypeLabel(log.type) }}
            </span>
            
            <!-- 重大更新标签 -->
            <span
              v-if="log.is_major"
              class="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 flex-shrink-0 whitespace-nowrap"
            >
              {{ t('settingsSecurity.changelog.majorBadge') }}
            </span>
            
            <!-- 未发布标签 -->
            <span
              v-if="!log.is_published"
              class="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 flex-shrink-0 whitespace-nowrap"
            >
              {{ t('settingsSecurity.changelog.unpublished') }}
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
                :title="t('settingsSecurity.common.edit')"
              >
                <Pencil class="w-4 h-4" />
              </button>
              <button
                v-if="!log.is_published"
                @click="publishLog(log)"
                class="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                :title="t('settingsSecurity.changelog.publish')"
              >
                <Rocket class="w-4 h-4" />
              </button>
              <button
                v-else
                @click="unpublishLog(log)"
                class="p-1.5 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg transition-colors"
                :title="t('settingsSecurity.changelog.unpublish')"
              >
                <Package class="w-4 h-4" />
              </button>
              <button
                @click="confirmDelete(log)"
                class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                :title="t('common.delete')"
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
                  class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap"
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
                  {{ t('settingsSecurity.changelog.breakingChanges') }}
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
                  {{ t('settingsSecurity.changelog.migrationNotes') }}
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
          {{ loadingMore ? t('common.loading') : t('settingsSecurity.changelog.loadMore') }}
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
          <h3 class="text-lg font-semibold">{{ editingItem ? t('settingsSecurity.changelog.editTitle') : t('settingsSecurity.changelog.publishNew') }}</h3>
          <button @click="showEditor = false" class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
            <X class="w-5 h-5" />
          </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.versionLabel') }}</label>
              <input
                v-model="form.version"
                type="text"
                :placeholder="t('settingsSecurity.changelog.versionPlaceholder')"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.typeLabel') }}</label>
              <select
                v-model="form.type"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              >
                <option value="release">{{ t('settingsSecurity.changelog.typeRelease') }}</option>
                <option value="hotfix">{{ t('settingsSecurity.changelog.typeHotfix') }}</option>
                <option value="beta">{{ t('settingsSecurity.changelog.typeBeta') }}</option>
                <option value="alpha">{{ t('settingsSecurity.changelog.typeAlpha') }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.categoryLabel') }}</label>
              <select
                v-model="form.category"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              >
                <option value="">{{ t('settingsSecurity.changelog.noCategory') }}</option>
                <option value="feature">{{ t('settingsSecurity.changelog.catFeature') }}</option>
                <option value="bugfix">{{ t('settingsSecurity.changelog.catBugfix') }}</option>
                <option value="improvement">{{ t('settingsSecurity.changelog.catImprovement') }}</option>
                <option value="security">{{ t('settingsSecurity.changelog.catSecurity') }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.authorLabel') }}</label>
              <input
                v-model="form.author"
                type="text"
                :placeholder="t('settingsSecurity.changelog.authorPlaceholder')"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.titleLabel') }}</label>
            <input
              v-model="form.title"
              type="text"
              :placeholder="t('settingsSecurity.changelog.titlePlaceholder')"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.tagsLabel') }}</label>
            <input
              v-model="tagsInput"
              type="text"
              :placeholder="t('settingsSecurity.changelog.tagsPlaceholder')"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.contentLabel') }}</label>
            <textarea
              v-model="form.content"
              rows="8"
              :placeholder="t('settingsSecurity.changelog.contentPlaceholder')"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.breakingChangesOptional') }}</label>
            <textarea
              v-model="form.breaking_changes"
              rows="3"
              :placeholder="t('settingsSecurity.changelog.breakingPlaceholder')"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.changelog.migrationNotesOptional') }}</label>
            <textarea
              v-model="form.migration_notes"
              rows="3"
              :placeholder="t('settingsSecurity.changelog.migrationPlaceholder')"
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 font-mono text-sm"
            ></textarea>
          </div>

          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="form.is_major" class="rounded border-gray-300" />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.changelog.markMajor') }}</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" v-model="form.is_published" class="rounded border-gray-300" />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ t('settingsSecurity.changelog.publishNow') }}</span>
            </label>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            @click="showEditor = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="saveChangelog"
            :disabled="saving || !form.version || !form.title || !form.content"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? t('settingsSecurity.common.saving') : (editingItem ? t('settingsSecurity.changelog.saveChanges') : t('settingsSecurity.changelog.publish')) }}
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
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">{{ t('settingsSecurity.changelog.confirmDelete') }}</h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          {{ t('settingsSecurity.changelog.deleteConfirmPrefix') }}<strong>{{ deletingItem?.version }}</strong>{{ t('settingsSecurity.changelog.deleteConfirmSuffix') }}
        </p>
        <div class="flex justify-end gap-3">
          <button
            @click="showDeleteConfirm = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="deleteLog"
            :disabled="deleting"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {{ deleting ? t('settingsSecurity.changelog.deleting') : t('settingsSecurity.changelog.confirmDelete') }}
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
const { sanitizeEmailHtml } = useSanitize()
const toast = useToast()
const { t } = useI18n()

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
  } catch (e: any) {
    console.error('加载更新日志失败:', e)
    toast.error(e.data?.detail || t('settingsSecurity.changelog.loadFailed'))
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
  } catch (e: any) {
    console.error('保存失败:', e)
    toast.error(e.data?.detail || t('settingsSecurity.changelog.saveFailed'))
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
  } catch (e: any) {
    console.error('删除失败:', e)
    toast.error(e.data?.detail || t('settingsSecurity.changelog.deleteFailed'))
  } finally {
    deleting.value = false
  }
}

const publishLog = async (log: Changelog) => {
  try {
    await publishChangelog(log.id)
    loadData()
  } catch (e: any) {
    console.error('发布失败:', e)
    toast.error(e.data?.detail || t('settingsSecurity.changelog.publishFailed'))
  }
}

const unpublishLog = async (log: Changelog) => {
  try {
    await unpublishChangelog(log.id)
    loadData()
  } catch (e: any) {
    console.error('取消发布失败:', e)
    toast.error(e.data?.detail || t('settingsSecurity.changelog.unpublishFailed'))
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
    release: t('settingsSecurity.changelog.typeRelease'),
    hotfix: t('settingsSecurity.changelog.typeHotfix'),
    beta: t('settingsSecurity.changelog.typeBeta'),
    alpha: t('settingsSecurity.changelog.typeAlpha')
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
    .replace(/\[(.+?)\]\((.+?)\)/g, (_match, linkText, href) => {
      // 只允许安全的 URL 协议（renderMarkdown 最终也会过 DOMPurify，这里做第一道防线）
      if (/^(?:https?:\/\/|mailto:|\/)/i.test(href)) {
        return `<a href="${href}" class="text-blue-600 dark:text-blue-400 hover:underline" target="_blank">${linkText}</a>`
      }
      return linkText  // 不安全的 URL 只保留文本
    })
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

  return sanitizeEmailHtml(result.join(''))
}

watch([filterType, filterCategory, showMajorOnly, sortOrder], () => {
  loadData()
})

onMounted(() => {
  checkAdmin()
  loadData()
})
</script>