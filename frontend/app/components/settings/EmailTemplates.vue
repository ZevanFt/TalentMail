
<script setup lang="ts">
import { Plus, Edit, Trash2, Eye, X, Save, RotateCcw, Info, Zap, Variable, Settings, Send, Cog, Mail, Loader2 } from 'lucide-vue-next'
import TemplateTriggerConfig from './TemplateTriggerConfig.vue'

const {
  getEmailTemplates, createEmailTemplate, updateEmailTemplate, deleteEmailTemplate,
  previewEmailTemplate, sendTestEmail, getMe,
  getTemplateMetadataList, getTemplateMetadata, getGlobalVariables, updateGlobalVariable, resetTemplateToDefault,
  sendTemplateEmail
} = useApi()
const toast = useToast()

interface TemplateVariable {
  key: string
  label: string
  type: string
  example: string
  required: boolean
}

interface TemplateMetadata {
  id: number
  code: string
  name: string
  category: string
  description: string | null
  trigger_description: string | null
  variables: TemplateVariable[]
  default_subject: string
  default_body_html: string
  default_body_text: string | null
  is_system: boolean
  sort_order: number
}

interface EmailTemplate {
  id: number
  code: string
  name: string
  category: string
  description: string | null
  subject: string
  body_html: string
  body_text: string | null
  variables: (string | TemplateVariable)[] | null
  is_active: boolean
  created_at: string
  updated_at: string
}

interface GlobalVariable {
  id: number
  key: string
  label: string
  value: string
  value_type: string
  description: string | null
}

const templates = ref<EmailTemplate[]>([])
const metadataList = ref<TemplateMetadata[]>([])
const globalVariables = ref<GlobalVariable[]>([])
const loading = ref(false)
const error = ref('')
const selectedCategory = ref('')
const categories = [
  { value: 'auth', label: '认证相关' },
  { value: 'notification', label: '系统通知' },
  { value: 'collaboration', label: '协作分享' }
]

const showEditModal = ref(false)
const editingTemplate = ref<EmailTemplate | null>(null)
const editingMetadata = ref<TemplateMetadata | null>(null)
const editForm = reactive({
  code: '', name: '', category: 'auth', description: '', subject: '', body_html: '', body_text: '', variables: '', is_active: true
})
const saving = ref(false)

const showPreviewModal = ref(false)
const previewData = ref<{ subject: string; body_html: string; body_text: string } | null>(null)
const previewVariables = ref<Record<string, string>>({})
const previewing = ref(false)
const previewError = ref('')
const testEmailTo = ref('')
const sendingTest = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const showTextPreview = ref(false) // 控制纯文本预览的折叠状态

// 防抖函数
let previewDebounceTimer: ReturnType<typeof setTimeout> | null = null
const debouncedPreview = () => {
  if (previewDebounceTimer) clearTimeout(previewDebounceTimer)
  previewDebounceTimer = setTimeout(() => {
    if (editingTemplate.value) {
      doPreview(editingTemplate.value.id)
    }
  }, 500)
}

// 监听变量变化，实时预览
watch(previewVariables, () => {
  if (showPreviewModal.value && editingTemplate.value) {
    debouncedPreview()
  }
}, { deep: true })

// 组件卸载时清理防抖定时器
onBeforeUnmount(() => {
  if (previewDebounceTimer) clearTimeout(previewDebounceTimer)
})

const showDeleteConfirm = ref(false)
const deletingTemplate = ref<EmailTemplate | null>(null)
const deleting = ref(false)

const showGlobalVarsModal = ref(false)
const editingGlobalVars = ref<GlobalVariable[]>([])
const savingGlobalVars = ref(false)

// 触发配置弹窗
const showTriggerConfig = ref(false)
const triggerConfigTemplate = ref<EmailTemplate | null>(null)

const openTriggerConfig = (template: EmailTemplate) => {
  triggerConfigTemplate.value = template
  showTriggerConfig.value = true
}

const handleTriggerConfigSave = (_config: any) => {
  // 刷新模板列表（可能有规则数量变化）
  loadTemplates()
}

// 手动发送弹窗
const showSendModal = ref(false)
const sendingTemplate = ref<EmailTemplate | null>(null)
const sendingMetadata = ref<TemplateMetadata | null>(null)
const sendForm = reactive({
  to: '',
  cc: '',
  variables: {} as Record<string, string>
})
const sending = ref(false)
const sendResult = ref<{ success: boolean; message: string } | null>(null)

const openSendModal = async (template: EmailTemplate) => {
  sendingTemplate.value = template
  sendForm.to = ''
  sendForm.cc = ''
  sendForm.variables = {}
  sendResult.value = null
  
  // 加载元数据获取变量定义
  try {
    sendingMetadata.value = await getTemplateMetadata(template.code)
    // 初始化变量值为示例值
    if (sendingMetadata.value?.variables) {
      sendingMetadata.value.variables.forEach(v => {
        sendForm.variables[v.key] = v.example || ''
      })
    }
  } catch (e) {
    sendingMetadata.value = null
    // 使用模板自带的变量列表
    if (template.variables) {
      template.variables.forEach(v => {
        const key = typeof v === 'object' ? v.key : v
        sendForm.variables[key] = ''
      })
    }
  }
  
  showSendModal.value = true
}

const doSend = async () => {
  if (!sendingTemplate.value || !sendForm.to) return
  
  sending.value = true
  sendResult.value = null
  
  try {
    const res = await sendTemplateEmail(sendingTemplate.value.id, {
      to: sendForm.to,
      cc: sendForm.cc || undefined,
      variables: sendForm.variables
    })
    sendResult.value = { success: true, message: res.message }
  } catch (e: any) {
    sendResult.value = { success: false, message: e.data?.detail || '发送失败' }
  } finally {
    sending.value = false
  }
}

const loadTemplates = async () => {
  loading.value = true
  error.value = ''
  try {
    const category = selectedCategory.value || undefined
    const [templatesRes, metadataRes] = await Promise.all([
      getEmailTemplates(category),
      getTemplateMetadataList(category)
    ])
    templates.value = templatesRes
    metadataList.value = metadataRes
  } catch (e: any) {
    error.value = e.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

const loadGlobalVariables = async () => {
  try {
    globalVariables.value = await getGlobalVariables()
  } catch (e: any) {
    console.error('加载全局变量失败:', e)
    toast.error(e.data?.detail || '加载全局变量失败')
  }
}

const getMetadataForTemplate = (template: EmailTemplate): TemplateMetadata | undefined => {
  return metadataList.value.find(m => m.code === template.code)
}

const openEditModal = async (template?: EmailTemplate) => {
  if (template) {
    editingTemplate.value = template
    editForm.code = template.code
    editForm.name = template.name
    editForm.category = template.category
    editForm.description = template.description || ''
    editForm.subject = template.subject
    editForm.body_html = template.body_html
    editForm.body_text = template.body_text || ''
    editForm.variables = (template.variables || []).join(', ')
    editForm.is_active = template.is_active
    try {
      editingMetadata.value = await getTemplateMetadata(template.code)
    } catch (e) {
      editingMetadata.value = null
    }
  } else {
    editingTemplate.value = null
    editingMetadata.value = null
    Object.assign(editForm, { code: '', name: '', category: 'auth', description: '', subject: '', body_html: '', body_text: '', variables: '', is_active: true })
  }
  showEditModal.value = true
}

const saveTemplate = async () => {
  saving.value = true
  error.value = ''
  try {
    // 优先使用 customVariables (包含完整元数据)，如果为空则尝试从字符串解析
    let variables_payload: any[] = []
    
    if (customVariables.value.length > 0) {
      variables_payload = customVariables.value
    } else {
      // 兼容手动输入逗号分隔的情况
      const rawVars = editForm.variables.split(',').map(v => v.trim()).filter(v => v)
      variables_payload = rawVars.map(v => ({
        key: v,
        label: v, // 默认中文名为变量名
        type: 'string',
        required: false
      }))
    }
    
    const data = {
      code: editForm.code, name: editForm.name, category: editForm.category,
      description: editForm.description || undefined, subject: editForm.subject,
      body_html: editForm.body_html, body_text: editForm.body_text || undefined,
      variables: variables_payload.length > 0 ? variables_payload : undefined,
      is_active: editForm.is_active
    }
    if (editingTemplate.value) {
      await updateEmailTemplate(editingTemplate.value.id, data)
    } else {
      await createEmailTemplate(data)
    }
    showEditModal.value = false
    await loadTemplates()
  } catch (e: any) {
    error.value = e.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

const resetToDefault = async () => {
  if (!editingTemplate.value) return
  saving.value = true
  try {
    const updated = await resetTemplateToDefault(editingTemplate.value.id)
    editForm.subject = updated.subject
    editForm.body_html = updated.body_html
    editForm.body_text = updated.body_text || ''
    editorRef.value?.setContent(updated.body_html)
  } catch (e: any) {
    error.value = e.data?.detail || '重置失败'
  } finally {
    saving.value = false
  }
}

const openPreviewModal = async (template: EmailTemplate) => {
  // 重置状态
  previewData.value = null
  previewError.value = ''
  testResult.value = null
  
  let metadata: TemplateMetadata | null = null
  try { metadata = await getTemplateMetadata(template.code) } catch (e) { console.warn('加载模板元数据失败:', e) }
  
  previewVariables.value = {}
  if (metadata?.variables) {
    metadata.variables.forEach(v => { previewVariables.value[v.key] = v.example || `[${v.key}]` })
  } else if (template.variables) {
    template.variables.forEach(v => {
      const key = typeof v === 'object' ? v.key : v
      previewVariables.value[key] = `[${key}]`
    })
  }
  
  try { const user = await getMe(); testEmailTo.value = user.email } catch (e) { console.warn('加载用户邮箱失败:', e) }
  
  editingTemplate.value = template
  editingMetadata.value = metadata
  showPreviewModal.value = true
  await doPreview(template.id)
}

const doPreview = async (templateId: number) => {
  previewing.value = true
  previewError.value = ''
  try {
    previewData.value = await previewEmailTemplate(templateId, previewVariables.value)
  } catch (e: any) {
    previewError.value = e.data?.detail || '预览失败，请检查模板是否存在'
    previewData.value = null
  } finally {
    previewing.value = false
  }
}

const doSendTest = async () => {
  if (!editingTemplate.value || !testEmailTo.value) return
  sendingTest.value = true
  testResult.value = null
  try {
    const res = await sendTestEmail(editingTemplate.value.id, testEmailTo.value, previewVariables.value)
    testResult.value = { success: true, message: res.message }
  } catch (e: any) {
    testResult.value = { success: false, message: e.data?.detail || '发送失败' }
  } finally {
    sendingTest.value = false
  }
}

const confirmDelete = (template: EmailTemplate) => {
  deletingTemplate.value = template
  showDeleteConfirm.value = true
}

const doDelete = async () => {
  if (!deletingTemplate.value) return
  deleting.value = true
  try {
    await deleteEmailTemplate(deletingTemplate.value.id)
    showDeleteConfirm.value = false
    deletingTemplate.value = null
    await loadTemplates()
  } catch (e: any) {
    error.value = e.data?.detail || '删除失败'
  } finally {
    deleting.value = false
  }
}

const openGlobalVarsModal = async () => {
  await loadGlobalVariables()
  editingGlobalVars.value = JSON.parse(JSON.stringify(globalVariables.value))
  showGlobalVarsModal.value = true
}

const saveGlobalVars = async () => {
  savingGlobalVars.value = true
  try {
    for (const v of editingGlobalVars.value) {
      const original = globalVariables.value.find(g => g.id === v.id)
      if (original && original.value !== v.value) await updateGlobalVariable(v.id, v.value)
    }
    await loadGlobalVariables()
    showGlobalVarsModal.value = false
  } catch (e: any) {
    error.value = e.data?.detail || '保存失败'
  } finally {
    savingGlobalVars.value = false
  }
}

const categoryNames: Record<string, string> = { auth: '认证相关', notification: '系统通知', collaboration: '协作分享', system: '系统' }
const formatVariable = (v: string) => `{{${v}}}`
const togglingTemplates = ref<Set<number>>(new Set())

const toggleTemplateActive = async (template: EmailTemplate) => {
  if (togglingTemplates.value.has(template.id)) return
  togglingTemplates.value.add(template.id)
  try {
    await updateEmailTemplate(template.id, { is_active: !template.is_active })
    template.is_active = !template.is_active
  } catch (e: any) {
    error.value = e.data?.detail || '更新失败'
  } finally {
    togglingTemplates.value.delete(template.id)
  }
}

onMounted(() => { Promise.allSettled([loadTemplates(), loadGlobalVariables()]) })
watch(selectedCategory, () => { loadTemplates() })

const editorRef = ref<any>(null)

// 从模板内容中自动提取 {{variable}} 格式的变量
const extractVariablesFromContent = () => {
  // 如果已有元数据定义的变量，不自动提取
  if (editingMetadata.value?.variables?.length) return
  
  // 匹配 {{variable}} 格式，提取变量名（不包含括号）
  const regex = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g
  const content = editForm.body_html + ' ' + editForm.subject
  const matches = new Set<string>()
  let match
  while ((match = regex.exec(content)) !== null) {
    if (match[1]) {
      matches.add(match[1])
    }
  }
  
  // 更新变量列表（去重）
  if (matches.size > 0) {
    editForm.variables = Array.from(matches).join(', ')
  }
}

// 监听弹窗打开，初始化自定义变量
watch(() => showEditModal.value, (val) => {
  if (val) {
    initCustomVariables()
  }
})

// 自定义变量列表（用于新建模板时）
const customVariables = ref<TemplateVariable[]>([])

// 添加新变量的表单
const newVariable = reactive({
  key: '',
  label: '',
  type: 'string',
  example: '',
  required: false
})

const showAddVariableModal = ref(false)

const addVariable = () => {
  if (!newVariable.key || !newVariable.label) return
  
  // 检查是否已存在
  const exists = customVariables.value.some(v => v.key === newVariable.key)
  if (exists) {
    error.value = '变量名已存在'
    return
  }
  
  customVariables.value.push({
    key: newVariable.key,
    label: newVariable.label,
    type: newVariable.type,
    example: newVariable.example,
    required: newVariable.required
  })
  
  // 更新 editForm.variables
  syncVariablesToForm()
  
  // 重置表单
  newVariable.key = ''
  newVariable.label = ''
  newVariable.type = 'string'
  newVariable.example = ''
  newVariable.required = false
  showAddVariableModal.value = false
}

const removeVariable = (key: string) => {
  customVariables.value = customVariables.value.filter(v => v.key !== key)
  syncVariablesToForm()
}

const syncVariablesToForm = () => {
  editForm.variables = customVariables.value.map(v => v.key).join(', ')
}

// 初始化自定义变量（编辑时从模板加载）
const initCustomVariables = () => {
  if (editingMetadata.value?.variables?.length) {
    // 系统模板，使用元数据变量
    customVariables.value = [...editingMetadata.value.variables]
  } else if (editingTemplate.value?.variables?.length) {
    // 已有模板，从变量列表恢复
    // 兼容旧数据（字符串数组）和新数据（对象数组）
    customVariables.value = editingTemplate.value.variables.map(v => {
      if (typeof v === 'string') {
        return {
          key: v,
          label: v,
          type: 'string',
          example: '',
          required: false
        }
      } else {
        return v as TemplateVariable
      }
    })
    
    // 同步到表单字符串显示（用于快速查看）
    editForm.variables = customVariables.value.map(v => v.key).join(', ')
  } else {
    customVariables.value = []
    editForm.variables = ''
  }
}

const availableVariables = computed(() => {
  // 优先使用元数据定义的变量
  if (editingMetadata.value?.variables?.length) return editingMetadata.value.variables
  
  // 使用自定义变量列表
  if (customVariables.value.length > 0) {
    return customVariables.value
  }
  
  // 最后尝试从正文中自动提取变量
  const regex = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g
  const content = editForm.body_html + ' ' + editForm.subject
  const matches = new Set<string>()
  let match
  while ((match = regex.exec(content)) !== null) {
    if (match[1]) {
      matches.add(match[1])
    }
  }
  
  return Array.from(matches).map(v => ({ key: v, label: v, type: 'string', example: '', required: false }))
})
const getVariableTypeIcon = (type: string) => {
  switch (type) { case 'url': return '🔗'; case 'datetime': return '📅'; case 'number': return '🔢'; default: return '📝' }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">邮件模板管理</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">管理系统邮件模板，如验证码、欢迎邮件等</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="openGlobalVarsModal" class="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors">
          <Settings class="w-4 h-4" /><span>全局变量</span>
        </button>
        <button @click="openEditModal()" class="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors">
          <Plus class="w-4 h-4" /><span>新建模板</span>
        </button>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <select v-model="selectedCategory" class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm">
        <option value="">全部分类</option>
        <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
      </select>
    </div>

    <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">{{ error }}</div>

    <div v-if="loading" class="text-center py-8 text-gray-500">加载中...</div>
    <div v-else-if="templates.length === 0" class="text-center py-8 text-gray-500">暂无模板</div>
    <div v-else class="space-y-4">
      <div v-for="template in templates" :key="template.id" :class="['bg-white dark:bg-gray-800 border rounded-xl p-4 transition-all', template.is_active ? 'border-gray-200 dark:border-gray-700' : 'border-gray-200 dark:border-gray-700 opacity-60']">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <Toggle :model-value="template.is_active" @update:model-value="toggleTemplateActive(template)" :disabled="togglingTemplates.has(template.id)" />
              <h3 class="font-medium text-gray-900 dark:text-white">{{ template.name }}</h3>
              <span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">{{ categoryNames[template.category] || template.category }}</span>
              <span v-if="getMetadataForTemplate(template)?.is_system" class="px-2 py-0.5 text-xs rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">系统模板</span>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-2 ml-12">
              <code class="text-xs bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded">{{ template.code }}</code>
              <span v-if="template.description" class="ml-2">{{ template.description }}</span>
            </p>
            <div v-if="getMetadataForTemplate(template)?.trigger_description" class="mt-2 ml-12 flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
              <Zap class="w-4 h-4" /><span>{{ getMetadataForTemplate(template)?.trigger_description }}</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-2 ml-12"><strong>主题：</strong>{{ template.subject }}</p>
            <div v-if="getMetadataForTemplate(template)?.variables?.length" class="mt-3 ml-12">
              <div class="flex items-center gap-1 mb-2"><Variable class="w-4 h-4 text-gray-400" /><span class="text-xs text-gray-500">可用变量：</span></div>
              <div class="flex flex-wrap gap-2">
                <div v-for="v in getMetadataForTemplate(template)?.variables" :key="v.key" class="group relative">
                  <span :class="['px-2 py-1 text-xs rounded cursor-help transition-colors', v.required ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300']">
                    {{ getVariableTypeIcon(v.type) }} {{ formatVariable(v.key) }}
                  </span>
                  <div class="absolute bottom-full left-0 mb-2 hidden group-hover:block z-10">
                    <div class="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                      <div class="font-medium">{{ v.label }}</div>
                      <div class="text-gray-400 mt-1">类型: {{ v.type }}</div>
                      <div v-if="v.example" class="text-gray-400">示例: {{ v.example }}</div>
                      <div v-if="v.required" class="text-red-400 mt-1">* 必填</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="template.variables && template.variables.length > 0" class="mt-2 ml-12 flex items-center gap-1 flex-wrap">
              <span class="text-xs text-gray-500">变量：</span>
              <span v-for="(v, idx) in template.variables" :key="idx" class="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded" :title="typeof v === 'object' ? v.label : v">
                {{ formatVariable(typeof v === 'object' ? v.key : v) }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="openSendModal(template)" class="p-2 text-gray-500 hover:text-green-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="发送邮件"><Mail class="w-4 h-4" /></button>
            <button @click="openTriggerConfig(template)" class="p-2 text-gray-500 hover:text-amber-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="触发设置"><Cog class="w-4 h-4" /></button>
            <button @click="openPreviewModal(template)" class="p-2 text-gray-500 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="预览"><Eye class="w-4 h-4" /></button>
            <button @click="openEditModal(template)" class="p-2 text-gray-500 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="编辑"><Edit class="w-4 h-4" /></button>
            <button @click="confirmDelete(template)" class="p-2 text-gray-500 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors" title="删除"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <CommonModal v-model="showEditModal" :title="editingTemplate ? '编辑模板' : '新建模板'" width-class="w-full max-w-4xl">
      <template #header-actions>
        <button v-if="editingTemplate && editingMetadata" @click="resetToDefault" :disabled="saving" class="flex items-center gap-1 px-3 py-1.5 text-sm text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg whitespace-nowrap transition-colors" title="重置为默认模板">
          <RotateCcw class="w-4 h-4" /><span>重置为默认</span>
        </button>
      </template>
      <div class="space-y-4">
        <div v-if="editingMetadata" class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl space-y-3">
          <div class="flex items-start gap-3">
            <Info class="w-5 h-5 text-blue-500 mt-0.5" />
            <div class="flex-1">
              <h4 class="font-medium text-blue-900 dark:text-blue-100">{{ editingMetadata.name }}</h4>
              <p class="text-sm text-blue-700 dark:text-blue-300 mt-1">{{ editingMetadata.description }}</p>
              <div v-if="editingMetadata.trigger_description" class="flex items-center gap-2 mt-2 text-sm text-blue-600 dark:text-blue-400">
                <Zap class="w-4 h-4" /><span>触发条件：{{ editingMetadata.trigger_description }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">模板代码</label>
            <input v-model="editForm.code" type="text" :disabled="!!editingTemplate" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm disabled:opacity-50" placeholder="如 verification_code_register">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">模板名称</label>
            <input v-model="editForm.name" type="text" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" placeholder="如 注册验证码">
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分类</label>
            <select v-model="editForm.category" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm">
              <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
            </select>
          </div>
          <div v-if="!editingMetadata">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">模板变量</label>
            <div class="space-y-2">
              <div v-if="customVariables.length > 0" class="flex flex-wrap gap-2 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                <div v-for="v in customVariables" :key="v.key" class="flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm group">
                  <span class="font-medium">{{ v.label }}</span>
                  <code class="text-xs opacity-70">({{ v.key }})</code>
                  <button @click="removeVariable(v.key)" class="ml-1 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-opacity">
                    <X class="w-3 h-3" />
                  </button>
                </div>
              </div>
              <div v-else class="text-sm text-gray-400 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                暂无变量，点击下方按钮添加
              </div>
              <button @click="showAddVariableModal = true" type="button" class="flex items-center gap-1 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg whitespace-nowrap transition-colors">
                <Plus class="w-4 h-4" />
                <span>添加变量</span>
              </button>
            </div>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
          <input v-model="editForm.description" type="text" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" placeholder="模板用途说明">
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮件主题</label>
          <input v-model="editForm.subject" type="text" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" placeholder="支持变量如 {{code}}">
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮件内容</label>
          <LazyEditorRichEditor
            ref="editorRef"
            v-model="editForm.body_html"
            :show-variable-bar="true"
            :variables="availableVariables.map(v => ({ key: v.key, label: v.label || v.key }))"
            :min-height="256"
            placeholder="编辑邮件模板内容..."
            @update:model-value="extractVariablesFromContent"
          />
          <details class="mt-2">
            <summary class="text-xs text-gray-500 cursor-pointer hover:text-primary">查看 HTML 源码</summary>
            <textarea v-model="editForm.body_html" @input="editorRef?.setContent(editForm.body_html)" rows="5" class="w-full mt-2 px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-xs font-mono text-gray-600 dark:text-gray-400"></textarea>
          </details>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">纯文本内容（可选）</label>
          <textarea v-model="editForm.body_text" rows="3" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" placeholder="纯文本版本"></textarea>
        </div>
        <div class="flex items-center gap-2">
          <input v-model="editForm.is_active" type="checkbox" id="is_active" class="w-4 h-4 text-primary rounded">
          <label for="is_active" class="text-sm text-gray-700 dark:text-gray-300">启用此模板</label>
        </div>
      </div>
      <template #footer>
        <button @click="showEditModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">取消</button>
        <button @click="saveTemplate" :disabled="saving" class="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50">
          <Save class="w-4 h-4" /><span>{{ saving ? '保存中...' : '保存' }}</span>
        </button>
      </template>
    </CommonModal>

    <!-- 预览弹窗 - 左右分栏设计 -->
    <CommonModal v-model="showPreviewModal" :title="`预览模板: ${editingTemplate?.name || ''}`" width-class="w-full max-w-6xl">
      <!-- 主体内容 - 左右分栏 -->
      <div class="flex -mx-6 -my-6 min-h-[60vh]">
        <!-- 左侧：变量设置 + 测试邮件 -->
        <div class="w-80 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <!-- 变量设置区 -->
            <div class="space-y-3">
              <div class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <Variable class="w-4 h-4" />
                <span>变量设置</span>
                <span v-if="previewing" class="ml-auto text-xs text-primary animate-pulse">刷新中...</span>
              </div>

              <div v-if="editingMetadata?.variables?.length" class="space-y-3">
                <div v-for="v in editingMetadata.variables" :key="v.key" class="space-y-1">
                  <label class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                    <span>{{ v.label }}</span>
                    <span v-if="v.required" class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="previewVariables[v.key]"
                    type="text"
                    class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                    :placeholder="v.example"
                  >
                </div>
              </div>
              <div v-else class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                此模板没有变量
              </div>
            </div>

            <!-- 分隔线 -->
            <div class="border-t border-gray-200 dark:border-gray-700"></div>

            <!-- 发送测试邮件区 -->
            <div class="space-y-3">
              <div class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <Send class="w-4 h-4" />
                <span>发送测试邮件</span>
              </div>

              <div class="space-y-2">
                <input
                  v-model="testEmailTo"
                  type="email"
                  class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
                  placeholder="收件人邮箱"
                >
                <button
                  @click="doSendTest"
                  :disabled="sendingTest || !testEmailTo"
                  class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send class="w-4 h-4" />
                  <span>{{ sendingTest ? '发送中...' : '发送测试' }}</span>
                </button>
              </div>

              <!-- 测试结果 -->
              <div
                v-if="testResult"
                :class="[
                  'p-3 rounded-lg text-sm',
                  testResult.success
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-800'
                    : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800'
                ]"
              >
                {{ testResult.message }}
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：预览效果 -->
        <div class="flex-1 flex flex-col overflow-hidden">
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <!-- 加载状态 -->
            <div v-if="previewing && !previewData" class="flex items-center justify-center h-full">
              <div class="text-center">
                <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
                <p class="mt-3 text-gray-500 dark:text-gray-400">正在加载预览...</p>
              </div>
            </div>

            <!-- 错误提示 -->
            <div v-else-if="previewError" class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p class="text-red-600 dark:text-red-400 text-sm font-medium">{{ previewError }}</p>
              <p class="text-red-500 dark:text-red-500 text-xs mt-2">请确保模板已正确初始化，或尝试重新加载页面。</p>
              <button
                @click="doPreview(editingTemplate!.id)"
                class="mt-3 px-3 py-1.5 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 text-sm rounded-lg transition-colors"
              >
                重试
              </button>
            </div>

            <!-- 预览内容 -->
            <div v-else-if="previewData" class="space-y-4">
              <div>
                <div class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Eye class="w-4 h-4" />
                  <span>主题</span>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm border border-gray-200 dark:border-gray-700">
                  {{ previewData.subject }}
                </div>
              </div>

              <div class="flex-1">
                <div class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Eye class="w-4 h-4" />
                  <span>HTML 邮件预览</span>
                </div>
                <div class="bg-white border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <iframe
                    :srcdoc="previewData.body_html"
                    class="w-full h-80 border-0"
                    sandbox=""
                  ></iframe>
                </div>
              </div>

              <div v-if="previewData.body_text">
                <button
                  @click="showTextPreview = !showTextPreview"
                  class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary transition-colors"
                >
                  <Eye class="w-4 h-4" />
                  <span>纯文本预览</span>
                  <svg :class="['w-4 h-4 transition-transform', showTextPreview ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div v-show="showTextPreview" class="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm whitespace-pre-wrap border border-gray-200 dark:border-gray-700 max-h-40 overflow-y-auto">
                  {{ previewData.body_text }}
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              <div class="text-center">
                <Eye class="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>输入变量后将自动预览</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button @click="showPreviewModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
          关闭
        </button>
      </template>
    </CommonModal>

    <!-- 删除确认弹窗 -->
    <CommonModal v-model="showDeleteConfirm" title="确认删除" width-class="w-full max-w-md">
      <p class="text-gray-600 dark:text-gray-400">确定要删除模板 <strong>{{ deletingTemplate?.name }}</strong> 吗？此操作不可撤销。</p>
      <template #footer>
        <button @click="showDeleteConfirm = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">取消</button>
        <button @click="doDelete" :disabled="deleting" class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50">{{ deleting ? '删除中...' : '删除' }}</button>
      </template>
    </CommonModal>

    <!-- 全局变量弹窗 -->
    <CommonModal v-model="showGlobalVarsModal" title="全局变量设置" width-class="w-full max-w-lg">
      <!-- 使用说明 -->
      <div class="space-y-4">
        <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-700 dark:text-blue-300 space-y-2">
          <p class="font-medium">💡 全局变量使用说明</p>
          <ul class="list-disc list-inside space-y-1 text-xs">
            <li>全局变量可在所有邮件模板中使用</li>
            <li>在模板中使用 <code class="bg-blue-100 dark:bg-blue-800 px-1 rounded">&lbrace;&lbrace;变量名&rbrace;&rbrace;</code> 语法引用</li>
            <li><span class="text-amber-600 dark:text-amber-400">动态变量</span> 由系统自动计算，无法手动修改</li>
            <li><span class="text-green-600 dark:text-green-400">配置变量</span> 从 config.json 读取</li>
            <li><span class="text-purple-600 dark:text-purple-400">静态变量</span> 可自由编辑</li>
          </ul>
        </div>

        <!-- 变量列表 -->
        <div v-if="editingGlobalVars.length === 0" class="text-center py-4 text-gray-500">
          暂无全局变量，请重启后端服务初始化
        </div>
        <div v-for="v in editingGlobalVars" :key="v.id" class="space-y-1">
          <label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            {{ v.label }}
            <code class="text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded" v-text="'{{' + v.key + '}}'"></code>
            <span v-if="v.value_type === 'dynamic'" class="px-1.5 py-0.5 text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 rounded">动态</span>
            <span v-else-if="v.value_type === 'config'" class="px-1.5 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded">配置</span>
            <span v-else class="px-1.5 py-0.5 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded">静态</span>
          </label>
          <input
            v-model="v.value"
            type="text"
            :disabled="v.value_type === 'dynamic'"
            class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            :placeholder="v.description || ''"
          >
          <p v-if="v.description" class="text-xs text-gray-400">{{ v.description }}</p>
        </div>
      </div>
      <template #footer>
        <button @click="showGlobalVarsModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">取消</button>
        <button @click="saveGlobalVars" :disabled="savingGlobalVars" class="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50">
          <Save class="w-4 h-4" /><span>{{ savingGlobalVars ? '保存中...' : '保存' }}</span>
        </button>
      </template>
    </CommonModal>

    <!-- 触发配置弹窗 -->
    <TemplateTriggerConfig
      v-model="showTriggerConfig"
      :template="triggerConfigTemplate"
      @save="handleTriggerConfigSave"
    />

    <!-- 手动发送弹窗 -->
    <CommonModal v-model="showSendModal" :title="`发送邮件 — ${sendingTemplate?.name || ''}`" width-class="w-full max-w-lg">
      <div class="space-y-4">
        <!-- 收件人 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">收件人 <span class="text-red-500">*</span></label>
          <input v-model="sendForm.to" type="email" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" placeholder="recipient@example.com">
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">抄送（可选）</label>
          <input v-model="sendForm.cc" type="email" class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" placeholder="cc@example.com">
        </div>

        <!-- 变量填写 -->
        <div v-if="sendingMetadata?.variables?.length || (sendingTemplate?.variables && sendingTemplate.variables.length > 0)" class="space-y-3">
          <div class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <Variable class="w-4 h-4" />
            <span>模板变量</span>
          </div>
          <div class="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl space-y-3">
            <template v-if="sendingMetadata?.variables?.length">
              <div v-for="v in sendingMetadata.variables" :key="v.key">
                <label class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {{ v.label }}
                  <span v-if="v.required" class="text-red-500">*</span>
                  <code class="ml-1 text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded" v-text="'{{' + v.key + '}}'"></code>
                </label>
                <input v-model="sendForm.variables[v.key]" type="text" class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm" :placeholder="v.example">
              </div>
            </template>
            <template v-else-if="sendingTemplate?.variables?.length">
              <div v-for="(v, idx) in sendingTemplate.variables" :key="idx">
                <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">
                  {{ typeof v === 'object' ? v.label : v }}
                  <code class="ml-1 text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">{{ typeof v === 'object' ? v.key : v }}</code>
                </label>
                <input
                  v-model="sendForm.variables[typeof v === 'object' ? v.key : v]"
                  type="text"
                  class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                  :placeholder="typeof v === 'object' ? v.example : `输入 ${v}`"
                >
              </div>
            </template>
          </div>
        </div>

        <!-- 发送结果 -->
        <div v-if="sendResult" :class="['p-3 rounded-lg text-sm', sendResult.success ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800']">
          {{ sendResult.message }}
        </div>
      </div>
      <template #footer>
        <button @click="showSendModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">取消</button>
        <button @click="doSend" :disabled="sending || !sendForm.to" class="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors disabled:opacity-50">
          <Loader2 v-if="sending" class="w-4 h-4 animate-spin" />
          <Send v-else class="w-4 h-4" />
          <span>{{ sending ? '发送中...' : '发送' }}</span>
        </button>
      </template>
    </CommonModal>

    <!-- 添加变量弹窗 -->
    <CommonModal v-model="showAddVariableModal" title="添加模板变量" width-class="w-full max-w-md">
      <div class="space-y-4">
        <!-- 变量名（英文） -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            变量名 <span class="text-red-500">*</span>
            <span class="text-xs text-gray-400 ml-2">用于模板中引用，如 <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">&lbrace;&lbrace;variable&rbrace;&rbrace;</code></span>
          </label>
          <input
            v-model="newVariable.key"
            type="text"
            class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
            placeholder="如 user_name, email_code"
            pattern="[a-zA-Z_][a-zA-Z0-9_]*"
          >
        </div>

        <!-- 中文名称 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            中文名称 <span class="text-red-500">*</span>
            <span class="text-xs text-gray-400 ml-2">显示给用户看的名称</span>
          </label>
          <input
            v-model="newVariable.label"
            type="text"
            class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
            placeholder="如 用户名, 验证码"
          >
        </div>

        <!-- 变量类型 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">变量类型</label>
          <select
            v-model="newVariable.type"
            class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
          >
            <option value="string">📝 文本</option>
            <option value="number">🔢 数字</option>
            <option value="url">🔗 链接</option>
            <option value="datetime">📅 日期时间</option>
          </select>
        </div>

        <!-- 示例值 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            示例值
            <span class="text-xs text-gray-400 ml-2">用于预览和发送测试时的默认值</span>
          </label>
          <input
            v-model="newVariable.example"
            type="text"
            class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
            placeholder="如 张三, 123456"
          >
        </div>

        <!-- 是否必填 -->
        <div class="flex items-center gap-2">
          <input v-model="newVariable.required" type="checkbox" id="var_required" class="w-4 h-4 text-primary rounded">
          <label for="var_required" class="text-sm text-gray-700 dark:text-gray-300">必填变量</label>
        </div>
      </div>
      <template #footer>
        <button @click="showAddVariableModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">取消</button>
        <button @click="addVariable" :disabled="!newVariable.key || !newVariable.label" class="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50">
          <Plus class="w-4 h-4" />
          <span>添加</span>
        </button>
      </template>
    </CommonModal>
  </div>
</template>