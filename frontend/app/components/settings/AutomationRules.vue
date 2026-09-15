<script setup lang="ts">
import { Plus, Play, Pause, Trash2, Edit, Clock, Zap, Mail, User, ChevronRight, AlertCircle, CheckCircle, XCircle, RefreshCw } from 'lucide-vue-next'

const { api } = useApi()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { t, locale } = useI18n()

// 状态
const rules = ref<any[]>([])
const logs = ref<any[]>([])
const metadata = ref<any>(null)
const loading = ref(false)
const logsLoading = ref(false)
const showEditor = ref(false)
const showLogs = ref(false)
const editingRule = ref<any>(null)
const selectedRuleId = ref<number | null>(null)

// 分页
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const logsPage = ref(1)
const logsTotal = ref(0)

// 加载元数据
const loadMetadata = async () => {
  try {
    const res = await api<any>('/automation/metadata')
    metadata.value = res
  } catch (e: any) {
    console.error('加载元数据失败:', e)
    toast.error(e.data?.detail || t('settings.automation.loadMetadataFailed'))
  }
}

// 加载规则列表
const loadRules = async () => {
  loading.value = true
  try {
    const res = await api<any>(`/automation/rules?page=${page.value}&page_size=${pageSize.value}`)
    rules.value = res.items
    total.value = res.total
  } catch (e: any) {
    console.error('加载规则失败:', e)
    toast.error(e.data?.detail || t('settings.automation.loadRulesFailed'))
  } finally {
    loading.value = false
  }
}

// 加载日志
const loadLogs = async (ruleId?: number) => {
  logsLoading.value = true
  try {
    let url = `/automation/logs?page=${logsPage.value}&page_size=10`
    if (ruleId) url += `&rule_id=${ruleId}`
    const res = await api<any>(url)
    logs.value = res.items
    logsTotal.value = res.total
  } catch (e: any) {
    console.error('加载日志失败:', e)
    toast.error(e.data?.detail || t('settings.automation.loadLogsFailed'))
  } finally {
    logsLoading.value = false
  }
}

// 切换规则状态
const toggleRule = async (rule: any) => {
  try {
    const res = await api<any>(`/automation/rules/${rule.id}/toggle`, 'POST')
    rule.is_active = res.is_active
  } catch (e: any) {
    console.error('切换状态失败:', e)
    toast.error(e.data?.detail || t('settings.automation.toggleFailed'))
  }
}

// 删除规则
const deleteRule = async (rule: any) => {
  const ok = await confirmDialog({ message: t('settings.automation.confirmDelete', { name: rule.name }), type: 'danger' })
  if (!ok) return
  try {
    await api(`/automation/rules/${rule.id}`, 'DELETE')
    await loadRules()
  } catch (e: any) {
    console.error('删除失败:', e)
    toast.error(e.data?.detail || t('settings.automation.deleteFailed'))
  }
}

// 手动触发规则
const triggerRule = async (rule: any) => {
  try {
    const res = await api<any>(`/automation/rules/${rule.id}/trigger`, 'POST', { context: {} })
    if (res.success) {
      toast.success(t('settings.automation.triggerSuccess'))
    } else {
      toast.error(t('settings.automation.triggerFailed', { msg: res.error_message }))
    }
    await loadLogs(rule.id)
  } catch (e: any) {
    toast.error(t('settings.automation.triggerFailed', { msg: e.data?.detail || e.message }))
  }
}

// 编辑规则
const editRule = (rule: any) => {
  editingRule.value = { ...rule }
  showEditor.value = true
}

// 新建规则
const createRule = () => {
  editingRule.value = {
    name: '',
    description: '',
    is_active: true,
    priority: 0,
    trigger_type: 'email_received',
    trigger_config: {},
    conditions: [],
    actions: []
  }
  showEditor.value = true
}

// 保存规则
const saveRule = async (ruleData: any) => {
  try {
    if (ruleData.id) {
      await api(`/automation/rules/${ruleData.id}`, 'PUT', ruleData)
    } else {
      await api('/automation/rules', 'POST', ruleData)
    }
    showEditor.value = false
    await loadRules()
  } catch (e: any) {
    toast.error(t('settings.automation.saveFailed', { msg: e.data?.detail || e.message }))
  }
}

// 查看规则日志
const viewRuleLogs = (rule: any) => {
  selectedRuleId.value = rule.id
  logsPage.value = 1
  loadLogs(rule.id)
  showLogs.value = true
}

// 获取触发器类型名称
const getTriggerTypeName = (type: string) => {
  const found = metadata.value?.trigger_types?.find((t: any) => t.type === type)
  return found?.name || type
}

// 获取状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return CheckCircle
    case 'failed': return XCircle
    case 'partial': return AlertCircle
    case 'skipped': return RefreshCw
    default: return Clock
  }
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'success': return 'text-green-500'
    case 'failed': return 'text-red-500'
    case 'partial': return 'text-yellow-500'
    case 'skipped': return 'text-gray-400'
    default: return 'text-gray-500'
  }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString(locale.value)
}

onMounted(() => {
  loadMetadata()
  loadRules()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('settings.tabs.automation') }}</h2>
        <p class="text-gray-500 dark:text-gray-400 mt-1">{{ t('settings.automation.subtitle') }}</p>
      </div>
      <div class="flex gap-2">
        <button @click="showLogs = true; loadLogs()" 
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2">
          <Clock class="w-4 h-4" />
          {{ t('settings.automation.executionLogs') }}
        </button>
        <button @click="createRule" 
          class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 flex items-center gap-2">
          <Plus class="w-4 h-4" />
          {{ t('settings.automation.newRule') }}
        </button>
      </div>
    </div>

    <!-- 规则列表 -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <div v-else-if="rules.length === 0" class="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
      <Zap class="w-12 h-12 mx-auto text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">{{ t('settings.automation.emptyTitle') }}</h3>
      <p class="text-gray-500 dark:text-gray-400 mb-4">{{ t('settings.automation.emptyDesc') }}</p>
      <button @click="createRule" class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90">
        {{ t('settings.automation.createFirst') }}
      </button>
    </div>

    <div v-else class="space-y-3">
      <div v-for="rule in rules" :key="rule.id"
        class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <div :class="['w-2 h-2 rounded-full', rule.is_active ? 'bg-green-500' : 'bg-gray-400']"></div>
              <h3 class="font-medium text-gray-900 dark:text-white">{{ rule.name }}</h3>
              <span v-if="rule.is_system" class="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded whitespace-nowrap">
                {{ t('settings.automation.systemRule') }}
              </span>
            </div>
            <p v-if="rule.description" class="text-sm text-gray-500 dark:text-gray-400 mt-1 ml-5">
              {{ rule.description }}
            </p>
            <div class="flex items-center gap-4 mt-2 ml-5 text-xs text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1">
                <Zap class="w-3 h-3" />
                {{ getTriggerTypeName(rule.trigger_type) }}
              </span>
              <span class="flex items-center gap-1">
                <Play class="w-3 h-3" />
                {{ t('settings.automation.executionCount', { n: rule.execution_count || 0 }) }}
              </span>
              <span v-if="rule.last_executed_at" class="flex items-center gap-1">
                <Clock class="w-3 h-3" />
                {{ formatTime(rule.last_executed_at) }}
              </span>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <button @click="viewRuleLogs(rule)" 
              class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" :title="t('settings.automation.viewLogs')">
              <Clock class="w-4 h-4" />
            </button>
            <button @click="triggerRule(rule)" 
              class="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400" :title="t('settings.automation.manualTrigger')">
              <Play class="w-4 h-4" />
            </button>
            <button v-if="!rule.is_system" @click="editRule(rule)" 
              class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" :title="t('settings.automation.edit')">
              <Edit class="w-4 h-4" />
            </button>
            <button @click="toggleRule(rule)" 
              :class="['p-2', rule.is_active ? 'text-green-500 hover:text-green-600' : 'text-gray-400 hover:text-gray-600']"
              :title="rule.is_active ? t('settings.automation.disable') : t('settings.automation.enable')">
              <component :is="rule.is_active ? Pause : Play" class="w-4 h-4" />
            </button>
            <button v-if="!rule.is_system" @click="deleteRule(rule)" 
              class="p-2 text-gray-400 hover:text-red-600" :title="t('common.delete')">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 规则编辑器弹窗 -->
    <CommonModal v-model="showEditor" :title="editingRule?.id ? t('settings.automation.editRule') : t('settings.automation.newRule')" size="xl">
      <AutomationRuleEditor 
        v-if="showEditor && metadata"
        :rule="editingRule"
        :metadata="metadata"
        @save="saveRule"
        @cancel="showEditor = false"
      />
    </CommonModal>

    <!-- 日志弹窗 -->
    <CommonModal v-model="showLogs" :title="t('settings.automation.executionLogs')" size="xl">
      <div class="space-y-4">
        <div v-if="logsLoading" class="flex justify-center py-8">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
        </div>
        
        <div v-else-if="logs.length === 0" class="text-center py-8 text-gray-500">
          {{ t('settings.automation.noLogs') }}
        </div>
        
        <div v-else class="space-y-2 max-h-96 overflow-y-auto">
          <div v-for="log in logs" :key="log.id"
            class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="getStatusIcon(log.status)" :class="['w-4 h-4', getStatusColor(log.status)]" />
                <span class="font-medium text-gray-900 dark:text-white">{{ log.rule_name || t('settings.automation.ruleFallback', { id: log.rule_id }) }}</span>
              </div>
              <span class="text-xs text-gray-500">{{ formatTime(log.created_at) }}</span>
            </div>
            <div class="mt-2 text-sm text-gray-600 dark:text-gray-400">
              <span>{{ t('settings.automation.triggerLabel') }}: {{ getTriggerTypeName(log.trigger_type) }}</span>
              <span class="mx-2">|</span>
              <span>{{ t('settings.automation.conditionsLabel') }}: {{ log.conditions_matched ? t('settings.automation.matched') : t('settings.automation.notMatched') }}</span>
              <span class="mx-2">|</span>
              <span>{{ t('settings.automation.durationLabel') }}: {{ log.execution_time_ms }}ms</span>
            </div>
            <div v-if="log.error_message" class="mt-2 text-sm text-red-500">
              {{ t('settings.automation.errorLabel') }}: {{ log.error_message }}
            </div>
          </div>
        </div>
        
        <div v-if="logsTotal > 10" class="flex justify-center gap-2">
          <button @click="logsPage--; loadLogs(selectedRuleId || undefined)" :disabled="logsPage <= 1"
            class="px-3 py-1 text-sm border rounded disabled:opacity-50">{{ t('settings.automation.prevPage') }}</button>
          <span class="px-3 py-1 text-sm">{{ logsPage }} / {{ Math.ceil(logsTotal / 10) }}</span>
          <button @click="logsPage++; loadLogs(selectedRuleId || undefined)" :disabled="logsPage >= Math.ceil(logsTotal / 10)"
            class="px-3 py-1 text-sm border rounded disabled:opacity-50">{{ t('settings.automation.nextPage') }}</button>
        </div>
      </div>
    </CommonModal>
  </div>
</template>