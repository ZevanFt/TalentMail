<script setup lang="ts">
import { Plus, Pencil, Trash2, Loader2, FileText, AlertCircle, Search } from 'lucide-vue-next'

const { getComposeTemplates, createComposeTemplate, updateComposeTemplate, deleteComposeTemplate } = useApi()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()

interface ComposeTemplate {
  id: number
  name: string | null
  subject: string | null
  body_html: string | null
  body_text: string | null
  created_at: string | null
}

const templates = ref<ComposeTemplate[]>([])
const loading = ref(true)
const loadError = ref('')
const showModal = ref(false)
const editingTemplate = ref<ComposeTemplate | null>(null)
const saving = ref(false)
const deletingId = ref<number | null>(null)

const form = reactive({
  name: '',
  subject: '',
  body_html: '',
})

const formErrors = reactive({ name: '' })

const validateForm = (): boolean => {
  formErrors.name = ''
  if (!form.name.trim()) {
    formErrors.name = '模板名称不能为空'
    return false
  }
  return true
}

const loadTemplates = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getComposeTemplates()
    templates.value = res.items || []
  } catch (e: any) {
    console.error('加载模板失败', e)
    loadError.value = e.data?.detail || '加载模板失败'
    toast.error(loadError.value)
  } finally {
    loading.value = false
  }
}

const openModal = (tmpl?: ComposeTemplate) => {
  editingTemplate.value = tmpl || null
  form.name = tmpl?.name || ''
  form.subject = tmpl?.subject || ''
  form.body_html = tmpl?.body_html || ''
  formErrors.name = ''
  showModal.value = true
}

const save = async () => {
  if (!validateForm()) return
  saving.value = true
  try {
    if (editingTemplate.value) {
      await updateComposeTemplate(editingTemplate.value.id, {
        name: form.name,
        subject: form.subject,
        body_html: form.body_html,
      })
    } else {
      await createComposeTemplate({
        name: form.name,
        subject: form.subject,
        body_html: form.body_html,
      })
    }
    showModal.value = false
    toast.success(editingTemplate.value ? '模板已更新' : '模板已创建')
    await loadTemplates()
  } catch (e: any) {
    console.error('保存模板失败', e)
    toast.error(e.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const remove = async (id: number) => {
  const ok = await confirmDialog({ message: '确定删除此模板？', type: 'danger' })
  if (!ok) return
  deletingId.value = id
  try {
    await deleteComposeTemplate(id)
    templates.value = templates.value.filter(t => t.id !== id)
    toast.success('模板已删除')
  } catch (e: any) {
    console.error('删除模板失败', e)
    toast.error(e.data?.detail || '删除失败')
  } finally {
    deletingId.value = null
  }
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch { return '' }
}

// 简单的 HTML → 纯文本预览
const stripHtml = (html: string | null) => {
  if (!html) return ''
  return html.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim().slice(0, 120)
}

onMounted(loadTemplates)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">写信模板</h2>
        <p class="text-sm text-gray-500 mt-1">创建常用的邮件模板，写信时一键填充主题和内容（最多 50 个）</p>
      </div>
      <button @click="openModal()"
        class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium">
        <Plus class="w-4 h-4" /> 新建模板
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="bg-white dark:bg-bg-panelDark rounded-xl p-4 border border-gray-200 dark:border-border-dark animate-pulse">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-gray-700" />
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32" />
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <AlertCircle class="w-12 h-12 mx-auto mb-3 text-red-400 opacity-60" />
      <p class="text-red-500 mb-3">{{ loadError }}</p>
      <button @click="loadTemplates" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">重试</button>
    </div>

    <!-- Empty -->
    <div v-else-if="templates.length === 0" class="text-center py-12 text-gray-500">
      <FileText class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p class="text-lg font-medium mb-1">暂无写信模板</p>
      <p class="text-sm text-gray-400">创建常用的邮件模板，提升写信效率</p>
    </div>

    <!-- Template List -->
    <div v-else class="space-y-3">
      <div v-for="tmpl in templates" :key="tmpl.id"
        class="bg-white dark:bg-bg-panelDark rounded-xl p-4 border border-gray-200 dark:border-border-dark hover:shadow-sm transition-shadow">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
              <FileText class="w-4 h-4 text-primary" />
            </div>
            <div class="min-w-0 flex-1">
              <div class="font-medium text-gray-900 dark:text-white">{{ tmpl.name }}</div>
              <div v-if="tmpl.subject" class="text-sm text-gray-600 dark:text-gray-400 mt-0.5 truncate">
                <span class="text-gray-400">主题：</span>{{ tmpl.subject }}
              </div>
              <div v-if="tmpl.body_html" class="text-sm text-gray-400 mt-1 truncate">
                {{ stripHtml(tmpl.body_html) }}
              </div>
              <div v-if="tmpl.created_at" class="text-xs text-gray-400 mt-1.5">
                {{ formatDate(tmpl.created_at) }}
              </div>
            </div>
          </div>
          <div class="flex gap-1 shrink-0">
            <button @click="openModal(tmpl)"
              class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors" title="编辑">
              <Pencil class="w-4 h-4" />
            </button>
            <button @click="remove(tmpl.id)" :disabled="deletingId === tmpl.id"
              class="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-400 hover:text-red-500 transition-colors disabled:opacity-50" title="删除">
              <Loader2 v-if="deletingId === tmpl.id" class="w-4 h-4 animate-spin" />
              <Trash2 v-else class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <CommonModal v-model="showModal" :title="editingTemplate ? '编辑模板' : '新建模板'" size="lg">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            模板名称 <span class="text-red-500">*</span>
          </label>
          <input v-model="form.name" placeholder="例如：会议邀请、工作汇报"
            :class="['w-full px-3 py-2 border rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all', formErrors.name ? 'border-red-400' : 'border-gray-200 dark:border-border-dark']"
            @input="formErrors.name = ''" />
          <span v-if="formErrors.name" class="text-red-500 text-xs mt-1 block">{{ formErrors.name }}</span>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮件主题</label>
          <input v-model="form.subject" placeholder="模板的默认主题（可选）"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮件正文</label>
          <textarea v-model="form.body_html" placeholder="模板的默认正文内容（支持 HTML）" rows="8"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-y font-mono"></textarea>
          <p class="text-xs text-gray-400 mt-1">提示：正文支持 HTML 格式，写信时将自动填入编辑器</p>
        </div>
      </div>
      <template #footer>
        <button @click="showModal = false"
          class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-sm">取消</button>
        <button @click="save" :disabled="saving"
          class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </CommonModal>
  </div>
</template>
