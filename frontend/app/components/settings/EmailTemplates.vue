<script setup lang="ts">
import { Mail, Plus, Edit, Trash2, Eye, Search, X, Save, Code, FileText } from 'lucide-vue-next'

const { getEmailTemplates, getEmailTemplate, createEmailTemplate, updateEmailTemplate, deleteEmailTemplate, previewEmailTemplate } = useApi()

interface EmailTemplate {
  id: number
  code: string
  name: string
  category: string
  description: string | null
  subject: string
  body_html: string
  body_text: string | null
  variables: string[] | null
  is_active: boolean
  created_at: string
  updated_at: string
}

const templates = ref<EmailTemplate[]>([])
const loading = ref(false)
const error = ref('')

// 筛选
const selectedCategory = ref('')
const categories = ['system', 'notification', 'marketing']

// 编辑弹窗
const showEditModal = ref(false)
const editingTemplate = ref<EmailTemplate | null>(null)
const editForm = reactive({
  code: '',
  name: '',
  category: 'system',
  description: '',
  subject: '',
  body_html: '',
  body_text: '',
  variables: '',
  is_active: true
})
const saving = ref(false)

// 预览弹窗
const showPreviewModal = ref(false)
const previewData = ref<{ subject: string; body_html: string; body_text: string } | null>(null)
const previewVariables = ref<Record<string, string>>({})
const previewing = ref(false)

// 删除确认
const showDeleteConfirm = ref(false)
const deletingTemplate = ref<EmailTemplate | null>(null)
const deleting = ref(false)

// 加载模板列表
const loadTemplates = async () => {
  loading.value = true
  error.value = ''
  try {
    const category = selectedCategory.value || undefined
    templates.value = await getEmailTemplates(category)
  } catch (e: any) {
    error.value = e.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

// 打开编辑弹窗
const openEditModal = (template?: EmailTemplate) => {
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
  } else {
    editingTemplate.value = null
    editForm.code = ''
    editForm.name = ''
    editForm.category = 'system'
    editForm.description = ''
    editForm.subject = ''
    editForm.body_html = ''
    editForm.body_text = ''
    editForm.variables = ''
    editForm.is_active = true
  }
  showEditModal.value = true
}

// 保存模板
const saveTemplate = async () => {
  saving.value = true
  error.value = ''
  try {
    const variables = editForm.variables
      .split(',')
      .map(v => v.trim())
      .filter(v => v)
    
    const data = {
      code: editForm.code,
      name: editForm.name,
      category: editForm.category,
      description: editForm.description || undefined,
      subject: editForm.subject,
      body_html: editForm.body_html,
      body_text: editForm.body_text || undefined,
      variables: variables.length > 0 ? variables : undefined,
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

// 打开预览弹窗
const openPreviewModal = async (template: EmailTemplate) => {
  // 初始化预览变量
  previewVariables.value = {}
  if (template.variables) {
    template.variables.forEach(v => {
      previewVariables.value[v] = `[${v}]`
    })
  }
  
  editingTemplate.value = template
  showPreviewModal.value = true
  await doPreview(template.id)
}

// 执行预览
const doPreview = async (templateId: number) => {
  previewing.value = true
  try {
    previewData.value = await previewEmailTemplate(templateId, previewVariables.value)
  } catch (e: any) {
    error.value = e.data?.detail || '预览失败'
  } finally {
    previewing.value = false
  }
}

// 确认删除
const confirmDelete = (template: EmailTemplate) => {
  deletingTemplate.value = template
  showDeleteConfirm.value = true
}

// 执行删除
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

// 分类名称映射
const categoryNames: Record<string, string> = {
  system: '系统',
  notification: '通知',
  marketing: '营销'
}

// 格式化变量显示
const formatVariable = (v: string) => `\{\{${v}\}\}`

onMounted(() => {
  loadTemplates()
})

watch(selectedCategory, () => {
  loadTemplates()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">邮件模板管理</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">管理系统邮件模板，如验证码、欢迎邮件等</p>
      </div>
      <button
        @click="openEditModal()"
        class="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors"
      >
        <Plus class="w-4 h-4" />
        <span>新建模板</span>
      </button>
    </div>

    <!-- 筛选 -->
    <div class="flex items-center gap-4">
      <select
        v-model="selectedCategory"
        class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
      >
        <option value="">全部分类</option>
        <option v-for="cat in categories" :key="cat" :value="cat">
          {{ categoryNames[cat] || cat }}
        </option>
      </select>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
      {{ error }}
    </div>

    <!-- 模板列表 -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      加载中...
    </div>
    <div v-else-if="templates.length === 0" class="text-center py-8 text-gray-500">
      暂无模板
    </div>
    <div v-else class="space-y-4">
      <div
        v-for="template in templates"
        :key="template.id"
        class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h3 class="font-medium text-gray-900 dark:text-white">{{ template.name }}</h3>
              <span
                :class="[
                  'px-2 py-0.5 text-xs rounded-full',
                  template.is_active
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500'
                ]"
              >
                {{ template.is_active ? '启用' : '禁用' }}
              </span>
              <span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                {{ categoryNames[template.category] || template.category }}
              </span>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              <code class="text-xs bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded">{{ template.code }}</code>
              <span v-if="template.description" class="ml-2">{{ template.description }}</span>
            </p>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-2">
              <strong>主题：</strong>{{ template.subject }}
            </p>
            <div v-if="template.variables && template.variables.length > 0" class="mt-2 flex items-center gap-1 flex-wrap">
              <span class="text-xs text-gray-500">变量：</span>
              <span
                v-for="v in template.variables"
                :key="v"
                class="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
              >
                {{ formatVariable(v) }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="openPreviewModal(template)"
              class="p-2 text-gray-500 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="预览"
            >
              <Eye class="w-4 h-4" />
            </button>
            <button
              @click="openEditModal(template)"
              class="p-2 text-gray-500 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="编辑"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              @click="confirmDelete(template)"
              class="p-2 text-gray-500 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="删除"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <Teleport to="body">
      <div v-if="showEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ editingTemplate ? '编辑模板' : '新建模板' }}
            </h3>
            <button @click="showEditModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">模板代码</label>
                <input
                  v-model="editForm.code"
                  type="text"
                  :disabled="!!editingTemplate"
                  class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm disabled:opacity-50"
                  placeholder="如 verification_code_register"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">模板名称</label>
                <input
                  v-model="editForm.name"
                  type="text"
                  class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                  placeholder="如 注册验证码"
                >
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分类</label>
                <select
                  v-model="editForm.category"
                  class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                >
                  <option v-for="cat in categories" :key="cat" :value="cat">
                    {{ categoryNames[cat] || cat }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">变量（逗号分隔）</label>
                <input
                  v-model="editForm.variables"
                  type="text"
                  class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                  placeholder="如 code, expires_minutes"
                >
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
              <input
                v-model="editForm.description"
                type="text"
                class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                placeholder="模板用途说明"
              >
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮件主题</label>
              <input
                v-model="editForm.subject"
                type="text"
                class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                placeholder="支持变量如 { {code} }"
              >
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">HTML 内容</label>
              <textarea
                v-model="editForm.body_html"
                rows="10"
                class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-mono"
                placeholder="HTML 邮件内容，支持变量"
              ></textarea>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">纯文本内容（可选）</label>
              <textarea
                v-model="editForm.body_text"
                rows="3"
                class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                placeholder="纯文本版本，用于不支持 HTML 的邮件客户端"
              ></textarea>
            </div>
            
            <div class="flex items-center gap-2">
              <input
                v-model="editForm.is_active"
                type="checkbox"
                id="is_active"
                class="w-4 h-4 text-primary rounded"
              >
              <label for="is_active" class="text-sm text-gray-700 dark:text-gray-300">启用此模板</label>
            </div>
          </div>
          
          <div class="flex items-center justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
            <button
              @click="showEditModal = false"
              class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              @click="saveTemplate"
              :disabled="saving"
              class="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50"
            >
              <Save class="w-4 h-4" />
              <span>{{ saving ? '保存中...' : '保存' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 预览弹窗 -->
    <Teleport to="body">
      <div v-if="showPreviewModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">预览模板</h3>
            <button @click="showPreviewModal = false" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <!-- 变量输入 -->
            <div v-if="editingTemplate?.variables && editingTemplate.variables.length > 0" class="space-y-2">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">预览变量</label>
              <div class="grid grid-cols-2 gap-2">
                <div v-for="v in editingTemplate.variables" :key="v" class="flex items-center gap-2">
                  <span class="text-sm text-gray-500 w-24">{{ formatVariable(v) }}</span>
                  <input
                    v-model="previewVariables[v]"
                    type="text"
                    class="flex-1 px-2 py-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded text-sm"
                  >
                </div>
              </div>
              <button
                @click="doPreview(editingTemplate!.id)"
                :disabled="previewing"
                class="px-3 py-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm rounded transition-colors"
              >
                {{ previewing ? '刷新中...' : '刷新预览' }}
              </button>
            </div>
            
            <!-- 预览内容 -->
            <div v-if="previewData" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">主题</label>
                <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm">
                  {{ previewData.subject }}
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">HTML 预览</label>
                <div class="p-4 bg-white border border-gray-200 dark:border-gray-700 rounded-lg">
                  <iframe
                    :srcdoc="previewData.body_html"
                    class="w-full h-64 border-0"
                  ></iframe>
                </div>
              </div>
              
              <div v-if="previewData.body_text">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">纯文本预览</label>
                <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm whitespace-pre-wrap">
                  {{ previewData.body_text }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="flex items-center justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
            <button
              @click="showPreviewModal = false"
              class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">确认删除</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            确定要删除模板 <strong>{{ deletingTemplate?.name }}</strong> 吗？此操作不可撤销。
          </p>
          <div class="flex items-center justify-end gap-3">
            <button
              @click="showDeleteConfirm = false"
              class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              @click="doDelete"
              :disabled="deleting"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {{ deleting ? '删除中...' : '删除' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>