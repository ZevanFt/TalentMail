<script setup lang="ts">
import { Search, Star, Bookmark, Filter, X, ChevronRight, Workflow, Plus, Heart, Tag, Package } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  modelValue: boolean
  scope?: 'personal' | 'system'  // 新增：创建工作流的范围
}>(), {
  scope: 'personal'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', template: any): void
  (e: 'use', template: any): void
  (e: 'create-blank'): void
}>()

const router = useRouter()
const { getWorkflowTemplates, getWorkflowTemplateCategories, getWorkflowTemplateTags, useWorkflowTemplate, toggleWorkflowTemplateFavorite } = useApi()

// 状态
const loading = ref(true)
const templates = ref<any[]>([])
const categories = ref<any[]>([])
const popularTags = ref<any[]>([])

// 筛选条件
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedTag = ref<string | null>(null)
const showFeaturedOnly = ref(false)
const showFavoritesOnly = ref(false)

// 选中的模板（用于预览）
const selectedTemplate = ref<any>(null)

// 使用模板
const usingTemplate = ref(false)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const [templatesRes, categoriesRes, tagsRes] = await Promise.all([
      getWorkflowTemplates({
        category: selectedCategory.value || undefined,
        tag: selectedTag.value || undefined,
        q: searchQuery.value || undefined,
        featured_only: showFeaturedOnly.value,
        favorites_only: showFavoritesOnly.value
      }),
      getWorkflowTemplateCategories(),
      getWorkflowTemplateTags()
    ])
    templates.value = templatesRes
    categories.value = categoriesRes
    popularTags.value = tagsRes.slice(0, 10)
  } catch (e) {
    console.error('加载模板失败:', e)
  } finally {
    loading.value = false
  }
}

// 搜索防抖
let searchTimeout: any = null
const onSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadData()
  }, 300)
}

// 当前激活的筛选模式：'all' | 'featured' | 'favorites' | 分类名
const activeFilter = ref<string>('all')

// 选择分类（互斥）
const selectCategory = (value: string | null) => {
  selectedCategory.value = value
  activeFilter.value = value || 'all'
  showFeaturedOnly.value = false
  showFavoritesOnly.value = false
  loadData()
}

// 选择标签
const selectTag = (tag: string | null) => {
  selectedTag.value = tag
  loadData()
}

// 切换收藏筛选（与分类互斥）
const toggleFavoritesFilter = () => {
  if (activeFilter.value === 'favorites') {
    activeFilter.value = 'all'
    showFavoritesOnly.value = false
  } else {
    activeFilter.value = 'favorites'
    showFavoritesOnly.value = true
    showFeaturedOnly.value = false
    selectedCategory.value = null
  }
  loadData()
}

// 切换推荐筛选（与分类互斥）
const toggleFeaturedFilter = () => {
  if (activeFilter.value === 'featured') {
    activeFilter.value = 'all'
    showFeaturedOnly.value = false
  } else {
    activeFilter.value = 'featured'
    showFeaturedOnly.value = true
    showFavoritesOnly.value = false
    selectedCategory.value = null
  }
  loadData()
}

// 预览模板
const previewTemplate = (template: any) => {
  selectedTemplate.value = template
  emit('select', template)
}

// 使用模板创建工作流
const useTemplate = async (template: any) => {
  usingTemplate.value = true
  try {
    const result = await useWorkflowTemplate(template.id, { scope: props.scope })
    if (result.success) {
      emit('use', template)
      emit('update:modelValue', false)
      // 跳转到新创建的工作流编辑页面
      router.push(`/workflows/${result.workflow_id}`)
    }
  } catch (e: any) {
    console.error('使用模板失败:', e)
  } finally {
    usingTemplate.value = false
  }
}

// 切换收藏
const toggleFavorite = async (template: any, event: Event) => {
  event.stopPropagation()
  try {
    const result = await toggleWorkflowTemplateFavorite(template.id)
    template.is_favorited = result.is_favorited
    template.favorite_count = result.favorite_count
  } catch (e) {
    console.error('收藏失败:', e)
  }
}

// 创建空白工作流
const createBlank = () => {
  emit('create-blank')
  emit('update:modelValue', false)
  router.push('/workflows/new')
}

// 关闭弹窗
const close = () => {
  emit('update:modelValue', false)
}

// 初始化
onMounted(() => {
  loadData()
})

// 监听弹窗显示
watch(() => props.modelValue, (value) => {
  if (value) {
    loadData()
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="close"
      >
        <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-[95vw] h-[90vh] max-w-7xl flex overflow-hidden">
          <!-- 左侧：分类筛选 -->
          <div class="w-56 border-r border-gray-200 dark:border-gray-700 flex flex-col shrink-0">
            <div class="p-4 border-b border-gray-100 dark:border-gray-800">
              <h3 class="font-bold text-gray-900 dark:text-white">工作流模板</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">选择一个模板快速开始</p>
            </div>
            
            <!-- 分类列表 -->
            <div class="flex-1 overflow-y-auto p-2 space-y-1">
              <button
                @click="selectCategory(null)"
                :class="[
                  'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors',
                  activeFilter === 'all'
                    ? 'bg-primary/10 text-primary'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                ]"
              >
                <Package class="w-4 h-4" />
                <span class="flex-1">全部模板</span>
                <span class="text-xs text-gray-400">{{ templates.length }}</span>
              </button>
              
              <button
                v-for="cat in categories"
                :key="cat.value"
                @click="selectCategory(cat.value)"
                :class="[
                  'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors',
                  activeFilter === cat.value
                    ? 'bg-primary/10 text-primary'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                ]"
              >
                <Workflow class="w-4 h-4" />
                <span class="flex-1">{{ cat.label }}</span>
                <span class="text-xs text-gray-400">{{ cat.count }}</span>
              </button>
              
              <!-- 分割线 -->
              <div class="my-3 border-t border-gray-100 dark:border-gray-800"></div>
              
              <!-- 快捷筛选 -->
              <button
                @click="toggleFeaturedFilter"
                :class="[
                  'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors',
                  activeFilter === 'featured'
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                ]"
              >
                <Star class="w-4 h-4" :class="{ 'fill-current': activeFilter === 'featured' }" />
                <span>推荐模板</span>
              </button>
              
              <button
                @click="toggleFavoritesFilter"
                :class="[
                  'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors',
                  activeFilter === 'favorites'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                ]"
              >
                <Heart class="w-4 h-4" :class="{ 'fill-current': activeFilter === 'favorites' }" />
                <span>我的收藏</span>
              </button>
            </div>
            
            <!-- 热门标签 -->
            <div class="p-3 border-t border-gray-100 dark:border-gray-800">
              <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">热门标签</p>
              <div class="flex flex-wrap gap-1">
                <button
                  v-for="tag in popularTags"
                  :key="tag.tag"
                  @click="selectTag(selectedTag === tag.tag ? null : tag.tag)"
                  :class="[
                    'px-2 py-0.5 text-xs rounded-full transition-colors',
                    selectedTag === tag.tag
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  ]"
                >
                  {{ tag.tag }}
                </button>
              </div>
            </div>
          </div>
          
          <!-- 中间：模板列表 -->
          <div class="flex-1 flex flex-col min-w-0">
            <!-- 搜索栏 -->
            <div class="p-4 border-b border-gray-100 dark:border-gray-800">
              <div class="flex items-center gap-3">
                <div class="flex-1 relative">
                  <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    v-model="searchQuery"
                    @input="onSearch"
                    type="text"
                    placeholder="搜索模板..."
                    class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <button
                  @click="createBlank"
                  class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm whitespace-nowrap"
                >
                  <Plus class="w-4 h-4" />
                  空白工作流
                </button>
                <button
                  @click="close"
                  class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X class="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
            
            <!-- 模板网格 -->
            <div class="flex-1 overflow-y-auto p-4">
              <!-- 加载状态 -->
              <div v-if="loading" class="flex items-center justify-center h-full">
                <div class="animate-spin w-8 h-8 border-3 border-primary border-t-transparent rounded-full"></div>
              </div>
              
              <!-- 模板列表 -->
              <div v-else-if="templates.length > 0" class="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div
                  v-for="template in templates"
                  :key="template.id"
                  @click="previewTemplate(template)"
                  :class="[
                    'group bg-white dark:bg-gray-800 rounded-xl border-2 p-4 cursor-pointer transition-all hover:shadow-lg',
                    selectedTemplate?.id === template.id
                      ? 'border-primary ring-2 ring-primary/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-primary/50'
                  ]"
                >
                  <!-- 预览图 -->
                  <div class="aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                    <img
                      v-if="template.thumbnail || template.preview_image"
                      :src="template.thumbnail || template.preview_image"
                      :alt="template.name"
                      class="w-full h-full object-cover"
                    />
                    <Workflow v-else class="w-12 h-12 text-gray-400" />
                  </div>
                  
                  <!-- 标题 -->
                  <div class="flex items-start justify-between gap-2 mb-2">
                    <h4 class="font-semibold text-gray-900 dark:text-white text-sm line-clamp-1">
                      {{ template.name }}
                    </h4>
                    <button
                      @click="toggleFavorite(template, $event)"
                      class="shrink-0 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <Heart
                        class="w-4 h-4"
                        :class="template.is_favorited ? 'text-red-500 fill-current' : 'text-gray-400'"
                      />
                    </button>
                  </div>
                  
                  <!-- 描述 -->
                  <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">
                    {{ template.description || '暂无描述' }}
                  </p>
                  
                  <!-- 标签 -->
                  <div class="flex flex-wrap gap-1 mb-3">
                    <span
                      v-for="tag in template.tags.slice(0, 3)"
                      :key="tag"
                      class="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded"
                    >
                      {{ tag }}
                    </span>
                    <span v-if="template.tags.length > 3" class="text-xs text-gray-400">
                      +{{ template.tags.length - 3 }}
                    </span>
                  </div>
                  
                  <!-- 底部信息 -->
                  <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{{ template.node_count }} 个节点</span>
                    <div class="flex items-center gap-3">
                      <span class="flex items-center gap-1">
                        <Workflow class="w-3 h-3" />
                        {{ template.use_count }}
                      </span>
                      <span class="flex items-center gap-1">
                        <Heart class="w-3 h-3" />
                        {{ template.favorite_count }}
                      </span>
                    </div>
                  </div>
                  
                  <!-- 推荐标记 -->
                  <div
                    v-if="template.is_featured"
                    class="absolute top-2 right-2 px-2 py-0.5 bg-yellow-500 text-white text-xs font-medium rounded-full"
                  >
                    推荐
                  </div>
                </div>
              </div>
              
              <!-- 空状态 -->
              <div v-else class="flex flex-col items-center justify-center h-full text-center">
                <div class="w-16 h-16 mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                  <Package class="w-8 h-8 text-gray-400" />
                </div>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  暂无模板
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  {{ searchQuery ? '没有找到匹配的模板' : '该分类下暂无模板' }}
                </p>
                <button
                  @click="createBlank"
                  class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm"
                >
                  <Plus class="w-4 h-4" />
                  创建空白工作流
                </button>
              </div>
            </div>
          </div>
          
          <!-- 右侧：模板预览 -->
          <Transition name="slide-right">
            <div
              v-if="selectedTemplate"
              class="w-80 border-l border-gray-200 dark:border-gray-700 flex flex-col shrink-0"
            >
              <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
                <h3 class="font-bold text-gray-900 dark:text-white">模板详情</h3>
                <button
                  @click="selectedTemplate = null"
                  class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                >
                  <X class="w-4 h-4 text-gray-500" />
                </button>
              </div>
              
              <div class="flex-1 overflow-y-auto p-4 space-y-4">
                <!-- 预览图 -->
                <div class="aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center overflow-hidden">
                  <img
                    v-if="selectedTemplate.preview_image"
                    :src="selectedTemplate.preview_image"
                    :alt="selectedTemplate.name"
                    class="w-full h-full object-cover"
                  />
                  <Workflow v-else class="w-16 h-16 text-gray-400" />
                </div>
                
                <!-- 标题 -->
                <div>
                  <h4 class="text-lg font-bold text-gray-900 dark:text-white">
                    {{ selectedTemplate.name }}
                  </h4>
                  <p v-if="selectedTemplate.name_en" class="text-sm text-gray-500 dark:text-gray-400">
                    {{ selectedTemplate.name_en }}
                  </p>
                </div>
                
                <!-- 描述 -->
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  {{ selectedTemplate.description || '暂无描述' }}
                </p>
                
                <!-- 统计信息 -->
                <div class="grid grid-cols-3 gap-3">
                  <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p class="text-lg font-bold text-gray-900 dark:text-white">{{ selectedTemplate.node_count }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">节点</p>
                  </div>
                  <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p class="text-lg font-bold text-gray-900 dark:text-white">{{ selectedTemplate.use_count }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">使用</p>
                  </div>
                  <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p class="text-lg font-bold text-gray-900 dark:text-white">{{ selectedTemplate.favorite_count }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">收藏</p>
                  </div>
                </div>
                
                <!-- 标签 -->
                <div v-if="selectedTemplate.tags?.length > 0">
                  <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">标签</p>
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="tag in selectedTemplate.tags"
                      :key="tag"
                      class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full"
                    >
                      {{ tag }}
                    </span>
                  </div>
                </div>
                
                <!-- 作者 -->
                <div v-if="selectedTemplate.author_name" class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <span>作者:</span>
                  <span class="text-gray-900 dark:text-white">{{ selectedTemplate.author_name }}</span>
                </div>
                
                <!-- 来源 -->
                <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <span>来源:</span>
                  <span
                    :class="[
                      'px-2 py-0.5 text-xs rounded-full',
                      selectedTemplate.source_type === 'official' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                      selectedTemplate.source_type === 'community' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                    ]"
                  >
                    {{ selectedTemplate.source_type === 'official' ? '官方' : selectedTemplate.source_type === 'community' ? '社区' : '用户' }}
                  </span>
                </div>
              </div>
              
              <!-- 操作按钮 -->
              <div class="p-4 border-t border-gray-100 dark:border-gray-800 space-y-2">
                <button
                  @click="useTemplate(selectedTemplate)"
                  :disabled="usingTemplate"
                  class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  <Plus class="w-5 h-5" />
                  {{ usingTemplate ? '创建中...' : '使用此模板' }}
                </button>
                <button
                  @click="toggleFavorite(selectedTemplate, $event)"
                  class="w-full flex items-center justify-center gap-2 px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <Heart
                    class="w-4 h-4"
                    :class="selectedTemplate.is_favorited ? 'text-red-500 fill-current' : 'text-gray-400'"
                  />
                  {{ selectedTemplate.is_favorited ? '取消收藏' : '收藏模板' }}
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>