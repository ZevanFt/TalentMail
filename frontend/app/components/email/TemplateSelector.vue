<script setup lang="ts">
/**
 * 模板选择器组件
 * 用于在 ComposeModal 中选择邮件模板
 */
import { FileText, Search, ChevronRight, X } from 'lucide-vue-next'

const { getEmailTemplates, getTemplateMetadata, previewEmailTemplate } = useApi()

interface TemplateVariable {
  key: string
  label: string
  type: string
  example: string
  required: boolean
}

interface EmailTemplate {
  id: number
  code: string
  name: string
  category: string
  description: string | null
  subject: string
  body_html: string
  variables: string[] | null
}

interface TemplateMetadata {
  code: string
  name: string
  category: string
  variables: TemplateVariable[]
}

const emit = defineEmits<{
  (e: 'select', data: { 
    template: EmailTemplate
    metadata: TemplateMetadata | null
    variables: Record<string, string>
    renderedSubject: string
    renderedBody: string
  }): void
  (e: 'clear'): void
}>()

// 状态
const showDropdown = ref(false)
const showVariableForm = ref(false)
const searchQuery = ref('')
const templates = ref<EmailTemplate[]>([])
const loading = ref(false)
const selectedTemplate = ref<EmailTemplate | null>(null)
const selectedMetadata = ref<TemplateMetadata | null>(null)
const variableValues = ref<Record<string, string>>({})
const previewing = ref(false)

// 分类定义
const categories: Record<string, { label: string; icon: string }> = {
  'auth': { label: '认证相关', icon: '🔐' },
  'notification': { label: '系统通知', icon: '🔔' },
  'collaboration': { label: '协作分享', icon: '🤝' },
  'finance': { label: '财务通知', icon: '📄' },
  'hr': { label: '人事通知', icon: '👥' },
  'marketing': { label: '营销推广', icon: '📢' },
  'customer': { label: '客户服务', icon: '💬' },
  'custom': { label: '自定义', icon: '✏️' },
}

// 按分类分组的模板
const groupedTemplates = computed(() => {
  const groups: Record<string, EmailTemplate[]> = {}
  
  const filtered = templates.value.filter(t => {
    if (!searchQuery.value) return true
    const q = searchQuery.value.toLowerCase()
    return t.name.toLowerCase().includes(q) || 
           t.code.toLowerCase().includes(q) ||
           (t.description || '').toLowerCase().includes(q)
  })
  
  for (const template of filtered) {
    const cat = template.category
    if (!groups[cat]) {
      groups[cat] = []
    }
    groups[cat].push(template)
  }
  
  return groups
})

// 加载可用模板（只加载手动触发的模板）
const loadTemplates = async () => {
  loading.value = true
  try {
    // 这里应该调用一个专门获取可手动使用模板的 API
    // 暂时使用现有 API
    templates.value = await getEmailTemplates()
  } catch (e) {
    console.error('加载模板失败:', e)
  } finally {
    loading.value = false
  }
}

// 选择模板
const selectTemplate = async (template: EmailTemplate) => {
  selectedTemplate.value = template
  showDropdown.value = false
  
  // 加载模板元数据
  try {
    selectedMetadata.value = await getTemplateMetadata(template.code)
  } catch (e) {
    selectedMetadata.value = null
  }
  
  // 初始化变量值
  variableValues.value = {}
  if (selectedMetadata.value?.variables) {
    for (const v of selectedMetadata.value.variables) {
      variableValues.value[v.key] = v.example || ''
    }
  } else if (template.variables) {
    for (const v of template.variables) {
      variableValues.value[v] = ''
    }
  }
  
  showVariableForm.value = true
}

// 预览效果
const previewTemplate = async () => {
  if (!selectedTemplate.value) return
  
  previewing.value = true
  try {
    const result = await previewEmailTemplate(selectedTemplate.value.id, variableValues.value)
    
    // 发送选择事件
    emit('select', {
      template: selectedTemplate.value,
      metadata: selectedMetadata.value,
      variables: { ...variableValues.value },
      renderedSubject: result.subject,
      renderedBody: result.body_html
    })
  } catch (e) {
    console.error('预览失败:', e)
  } finally {
    previewing.value = false
  }
}

// 清除模板
const clearTemplate = () => {
  selectedTemplate.value = null
  selectedMetadata.value = null
  variableValues.value = {}
  showVariableForm.value = false
  emit('clear')
}

// 打开下拉菜单时加载模板
watch(showDropdown, (val) => {
  if (val && templates.value.length === 0) {
    loadTemplates()
  }
})

// 点击外部关闭下拉菜单
const dropdownRef = ref<HTMLElement | null>(null)
onMounted(() => {
  document.addEventListener('click', (e) => {
    if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
      showDropdown.value = false
    }
  })
})
</script>

<template>
  <div class="space-y-4">
    
    <!-- 模板选择按钮 -->
    <div ref="dropdownRef" class="relative">
      <button 
        @click="showDropdown = !showDropdown"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition',
          selectedTemplate 
            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-300 dark:border-blue-700' 
            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
        ]"
      >
        <FileText class="w-4 h-4" />
        <span v-if="selectedTemplate">{{ selectedTemplate.name }}</span>
        <span v-else>使用模板</span>
        <ChevronRight :class="['w-4 h-4 transition', showDropdown ? 'rotate-90' : '']" />
      </button>
      
      <!-- 清除按钮 -->
      <button 
        v-if="selectedTemplate"
        @click.stop="clearTemplate"
        class="absolute right-0 top-0 -mr-2 -mt-2 p-1 bg-gray-200 dark:bg-gray-600 hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-500 hover:text-red-500 rounded-full"
      >
        <X class="w-3 h-3" />
      </button>
      
      <!-- 下拉菜单 -->
      <div 
        v-if="showDropdown"
        class="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-20"
      >
        <!-- 搜索框 -->
        <div class="p-3 border-b border-gray-200 dark:border-gray-700">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索模板..." 
              class="w-full pl-9 pr-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
        </div>
        
        <!-- 模板列表 -->
        <div class="max-h-64 overflow-y-auto">
          <template v-if="loading">
            <div class="p-4 text-center text-gray-500">
              加载中...
            </div>
          </template>
          <template v-else-if="Object.keys(groupedTemplates).length === 0">
            <div class="p-4 text-center text-gray-500">
              没有可用模板
            </div>
          </template>
          <template v-else>
            <div v-for="(group, category) in groupedTemplates" :key="category" class="p-2">
              <div class="px-3 py-1 text-xs text-gray-400 font-medium">
                {{ categories[category]?.icon || '📧' }} {{ categories[category]?.label || category }}
              </div>
              <button 
                v-for="template in group" 
                :key="template.id"
                @click="selectTemplate(template)"
                class="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm transition"
              >
                <div class="font-medium text-gray-900 dark:text-white">{{ template.name }}</div>
                <div v-if="template.description" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                  {{ template.description }}
                </div>
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
    
    <!-- 变量填写表单 -->
    <div 
      v-if="showVariableForm && selectedTemplate"
      class="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl"
    >
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <FileText class="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span class="font-medium text-blue-700 dark:text-blue-400">填写模板变量</span>
        </div>
        <button 
          @click="clearTemplate"
          class="text-sm text-gray-500 hover:text-red-500"
        >
          清空
        </button>
      </div>
      
      <!-- 变量输入 -->
      <div class="grid grid-cols-2 gap-4">
        <template v-if="selectedMetadata?.variables?.length">
          <div 
            v-for="v in selectedMetadata.variables" 
            :key="v.key"
            :class="v.type === 'textarea' || v.key.includes('url') ? 'col-span-2' : ''"
          >
            <label class="text-sm text-gray-600 dark:text-gray-400 mb-1 block">
              {{ v.label }}
              <span v-if="v.required" class="text-red-500">*</span>
            </label>
            <input 
              v-if="v.type !== 'textarea'"
              v-model="variableValues[v.key]"
              :type="v.type === 'number' ? 'number' : v.type === 'url' ? 'url' : v.type === 'email' ? 'email' : 'text'"
              :placeholder="v.example || `请输入${v.label}`"
              class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
            <textarea 
              v-else
              v-model="variableValues[v.key]"
              :placeholder="v.example || `请输入${v.label}`"
              rows="2"
              class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        </template>
        <template v-else-if="selectedTemplate.variables?.length">
          <div v-for="v in selectedTemplate.variables" :key="v">
            <label class="text-sm text-gray-600 dark:text-gray-400 mb-1 block">
              {{ v }}
            </label>
            <input 
              v-model="variableValues[v]"
              type="text"
              :placeholder="`请输入 ${v}`"
              class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
        </template>
        <template v-else>
          <div class="col-span-2 text-center text-gray-500 text-sm py-2">
            此模板无需填写变量
          </div>
        </template>
      </div>
      
      <!-- 预览按钮 -->
      <div class="mt-4 flex justify-center">
        <button 
          @click="previewTemplate"
          :disabled="previewing"
          class="flex items-center gap-2 px-4 py-2 text-sm text-blue-600 dark:text-blue-400 border border-blue-300 dark:border-blue-700 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition disabled:opacity-50"
        >
          <span v-if="previewing">生成中...</span>
          <span v-else>✨ 应用模板</span>
        </button>
      </div>
    </div>
    
  </div>
</template>