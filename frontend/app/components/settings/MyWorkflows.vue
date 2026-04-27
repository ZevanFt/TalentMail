<script setup lang="ts">
import { Plus, Workflow, Play, Edit, Trash2, RefreshCw, Clock, CheckCircle, Send, MoreVertical, Eye, Copy, BookOpen, Settings, Power, XCircle } from 'lucide-vue-next'
import { MarkerType } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const router = useRouter()
const { getWorkflows, getWorkflow, updateWorkflow, deleteWorkflow: deleteWorkflowApi, getNodeTypes, publishWorkflow, getWorkflowExecutions } = useApi()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()

const loading = ref(false)
const workflows = ref<any[]>([])

// 模板选择弹窗
const showTemplateSelector = ref(false)

// 预览状态
const showPreviewModal = ref(false)
const selectedWorkflow = ref<any>(null)
const previewNodes = ref<any[]>([])
const previewEdges = ref<any[]>([])
const nodeTypes = ref<any[]>([])
const loadingPreview = ref(false)

// 执行记录状态
const showExecutionModal = ref(false)
const executions = ref<any[]>([])
const loadingExecutions = ref(false)

// 配置状态
const showConfigModal = ref(false)
const configForm = ref<any>({})
const savingConfig = ref(false)

// 加载工作流列表
const loadWorkflows = async () => {
  loading.value = true
  try {
    workflows.value = await getWorkflows()
  } catch (e: any) {
    console.error('加载工作流列表失败:', e)
    toast.error(e.data?.detail || '加载工作流列表失败')
  } finally {
    loading.value = false
  }
}

// 创建新工作流 - 打开模板选择弹窗
const createWorkflow = () => {
  showTemplateSelector.value = true
}

// 直接创建空白工作流
const createBlankWorkflow = () => {
  showTemplateSelector.value = false
  router.push('/workflows/new')
}

// 从模板创建后的回调
const onTemplateUsed = (template: any) => {
  showTemplateSelector.value = false
  // 路由跳转由 TemplateSelector 组件内部处理
}

// 编辑工作流
const editWorkflow = (id: number) => {
  router.push(`/workflows/${id}`)
}

// 删除工作流
const deleting = ref<number | null>(null)
const deleteWorkflow = async (id: number) => {
  const ok = await confirmDialog({ message: '确定要删除这个工作流吗？此操作不可恢复。', type: 'danger' })
  if (!ok) return

  deleting.value = id
  try {
    await deleteWorkflowApi(id)
    workflows.value = workflows.value.filter(w => w.id !== id)
  } catch (e: any) {
    console.error('删除失败:', e)
    toast.error(e.data?.detail || '删除失败')
  } finally {
    deleting.value = null
  }
}

// 切换工作流启用状态
const togglingActive = ref<number | null>(null)
const toggleWorkflowActive = async (workflow: any) => {
  togglingActive.value = workflow.id
  try {
    const newState = !workflow.is_active
    await updateWorkflow(workflow.id, { is_active: newState })
    workflow.is_active = newState
    // 如果要启用但还是草稿状态，自动发布
    if (newState && workflow.status === 'draft') {
      await publishWorkflow(workflow.id)
      workflow.status = 'published'
    }
  } catch (e: any) {
    console.error('切换状态失败:', e)
    toast.error('操作失败：' + (e.data?.detail || e.message || '未知错误'))
  } finally {
    togglingActive.value = null
  }
}

// 打开预览模态框
const openPreviewModal = async (workflow: any) => {
  selectedWorkflow.value = workflow
  loadingPreview.value = true
  showPreviewModal.value = true
  
  try {
    // 加载完整工作流详情
    const detail = await getWorkflow(workflow.id)

    // 转换节点数据为 Vue Flow 格式
    previewNodes.value = (detail.nodes || []).map((n: any) => ({
      id: n.node_id,
      type: 'custom',
      position: { x: n.position_x || 0, y: n.position_y || 0 },
      data: {
        label: n.name || n.node_subtype,
        nodeType: n.node_type,
        nodeSubtype: n.node_subtype,
        icon: getNodeIcon(n.node_subtype),
        color: getNodeColor(n.node_type)
      }
    }))
    
    // 转换边数据
    previewEdges.value = (detail.edges || []).map((e: any) => ({
      id: e.edge_id,
      source: e.source_node_id,
      target: e.target_node_id,
      sourceHandle: e.source_handle,
      targetHandle: e.target_handle,
      type: 'smoothstep',
      animated: true,
      markerEnd: MarkerType.ArrowClosed,
      label: e.label
    }))
  } catch (e: any) {
    console.error('加载工作流预览失败:', e)
    toast.error(e.data?.detail || '加载工作流预览失败')
  } finally {
    loadingPreview.value = false
  }
}

// 获取节点图标
const getNodeIcon = (subtype: string): string => {
  const nodeType = nodeTypes.value.find((nt: any) => nt.code === subtype)
  return nodeType?.icon || '📦'
}

// 获取节点颜色
const getNodeColor = (category: string): string => {
  const colors: Record<string, string> = {
    trigger: '#10b981',
    logic: '#3b82f6',
    email_action: '#f59e0b',
    email_operation: '#8b5cf6',
    action: '#f59e0b',
    data: '#06b6d4',
    integration: '#ec4899',
    end: '#6b7280'
  }
  return colors[category] || '#6b7280'
}

// 加载节点类型
const loadNodeTypes = async () => {
  try {
    nodeTypes.value = await getNodeTypes()
  } catch (e: any) {
    console.error('加载节点类型失败:', e)
    toast.error(e.data?.detail || '加载节点类型失败')
  }
}

// 查看执行记录
const openExecutionModal = async (workflow: any) => {
  selectedWorkflow.value = workflow
  loadingExecutions.value = true
  showExecutionModal.value = true
  try {
    executions.value = await getWorkflowExecutions('user', workflow.id, undefined, 20)
  } catch (e: any) {
    console.error('加载执行记录失败:', e)
    toast.error(e.data?.detail || '加载执行记录失败')
  } finally {
    loadingExecutions.value = false
  }
}

// 打开配置模态框
const openConfigModal = async (workflow: any) => {
  selectedWorkflow.value = workflow
  try {
    const detail = await getWorkflow(workflow.id)
    configForm.value = detail.workflow.config ? { ...detail.workflow.config } : {}
    showConfigModal.value = true
  } catch (e: any) {
    console.error('加载配置失败:', e)
    toast.error(e.data?.detail || '加载配置失败')
  }
}

// 保存配置
const saveConfig = async () => {
  if (!selectedWorkflow.value) return
  savingConfig.value = true
  try {
    await updateWorkflow(selectedWorkflow.value.id, { config: configForm.value })
    showConfigModal.value = false
  } catch (e: any) {
    console.error('保存配置失败:', e)
    toast.error(e.data?.detail || '保存配置失败')
  } finally {
    savingConfig.value = false
  }
}

// 获取状态图标
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return CheckCircle
    case 'failed': return XCircle
    case 'running': return RefreshCw
    default: return Clock
  }
}

// 获取执行状态颜色
const getExecStatusColor = (status: string) => {
  switch (status) {
    case 'success': return 'text-green-500'
    case 'failed': return 'text-red-500'
    case 'running': return 'text-blue-500 animate-spin'
    default: return 'text-gray-400'
  }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'published': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    case 'draft': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
    case 'disabled': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
    default: return 'bg-gray-100 text-gray-800'
  }
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  switch (status) {
    case 'published': return '已发布'
    case 'draft': return '草稿'
    case 'disabled': return '已禁用'
    default: return status
  }
}

// 跳转到教程
const goToTutorial = () => {
  router.push('/workflows/tutorial')
}

onMounted(() => {
  loadWorkflows()
  loadNodeTypes()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 标题和操作 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">我的工作流</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          创建自动化规则，让邮件处理更智能。例如：自动标记重要邮件、自动转发、自动回复等。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="goToTutorial"
          class="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="查看教程"
        >
          <BookOpen class="w-4 h-4" />
          <span class="hidden sm:inline">教程</span>
        </button>
        <button
          @click="loadWorkflows"
          class="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        </button>
        <button
          @click="createWorkflow"
          class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
        >
          <Plus class="w-4 h-4" />
          新建工作流
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <RefreshCw class="w-8 h-8 text-primary animate-spin" />
    </div>

    <!-- 工作流列表 -->
    <div v-else-if="workflows.length > 0" class="grid gap-4">
      <div
        v-for="workflow in workflows"
        :key="workflow.id"
        class="relative bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6 hover:shadow-md transition-shadow min-h-[140px]"
      >
        <!-- 右上角按钮组 -->
        <div class="absolute top-4 right-4 flex items-center gap-2">
          <button
            @click="openPreviewModal(workflow)"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="预览流程图"
          >
            <Eye class="w-4 h-4" />
            <span>预览</span>
          </button>
          <button
            @click="openExecutionModal(workflow)"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="查看执行记录"
          >
            <Clock class="w-4 h-4" />
            <span>记录</span>
          </button>
          <button
            @click="openConfigModal(workflow)"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="配置工作流"
          >
            <Settings class="w-4 h-4" />
            <span>配置</span>
          </button>
          <button
            @click="editWorkflow(workflow.id)"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="编辑工作流"
          >
            <Edit class="w-4 h-4" />
            <span>编辑</span>
          </button>
          <!-- 启用/禁用开关 -->
          <div class="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200 dark:border-gray-700">
            <button
              @click="toggleWorkflowActive(workflow)"
              :disabled="togglingActive === workflow.id"
              :class="[
                'relative w-11 h-6 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50',
                workflow.is_active ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
              ]"
              :title="workflow.is_active ? '点击禁用' : '点击启用'"
            >
              <span
                :class="[
                  'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform shadow',
                  workflow.is_active ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
              <RefreshCw v-if="togglingActive === workflow.id" class="absolute inset-0 m-auto w-3 h-3 text-white animate-spin" />
            </button>
          </div>
        </div>

        <!-- 右下角删除按钮 -->
        <button
          @click="deleteWorkflow(workflow.id)"
          :disabled="deleting === workflow.id"
          class="absolute bottom-4 right-4 flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
          title="删除工作流"
        >
          <Trash2 class="w-4 h-4" />
          <span>{{ deleting === workflow.id ? '删除中...' : '删除' }}</span>
        </button>

        <!-- 左侧信息 -->
        <div class="pr-96">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Workflow class="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ workflow.name }}
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                v{{ workflow.version }}
              </p>
            </div>
            <span :class="['px-2 py-1 text-xs font-medium rounded-full whitespace-nowrap', getStatusColor(workflow.status)]">
              {{ getStatusLabel(workflow.status) }}
            </span>
          </div>

          <p class="mt-3 text-sm text-gray-600 dark:text-gray-400">
            {{ workflow.description || '暂无描述' }}
          </p>

          <!-- 统计信息 -->
          <div class="mt-4 flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
            <span class="flex items-center gap-1">
              <Play class="w-3.5 h-3.5" />
              执行 {{ workflow.execution_count || 0 }} 次
            </span>
            <span v-if="workflow.category" class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">
              {{ workflow.category }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="text-center py-16 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
        <Workflow class="w-8 h-8 text-gray-400" />
      </div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        暂无工作流
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
        创建您的第一个自动化工作流，可以实现自动标记、转发、回复等功能
      </p>
      <button
        @click="createWorkflow"
        class="inline-flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
      >
        <Plus class="w-5 h-5" />
        创建工作流
      </button>
    </div>

    <!-- 使用提示 -->
    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
      <h4 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">💡 工作流用途示例</h4>
      <ul class="text-sm text-blue-700 dark:text-blue-400 space-y-1">
        <li>• 收到老板邮件时自动标记为重要</li>
        <li>• 特定主题的邮件自动转发给团队</li>
        <li>• 收到客户询盘时自动回复确认邮件</li>
        <li>• 垃圾邮件自动移动到垃圾箱</li>
      </ul>
    </div>

    <!-- 预览模态框 -->
    <WorkflowPreviewModal
      v-model="showPreviewModal"
      :workflow="selectedWorkflow"
      :nodes="previewNodes"
      :edges="previewEdges"
      :loading="loadingPreview"
      @edit="editWorkflow(selectedWorkflow?.id)"
    />

    <!-- 工作流模板选择弹窗 -->
    <WorkflowTemplateSelector
      v-model="showTemplateSelector"
      @use="onTemplateUsed"
      @create-blank="createBlankWorkflow"
    />

    <!-- 执行记录模态框 -->
    <CommonModal v-model="showExecutionModal" title="执行记录" size="lg">
      <div v-if="selectedWorkflow" class="space-y-4">
        <!-- 工作流信息 -->
        <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <h4 class="font-medium text-gray-900 dark:text-white">{{ selectedWorkflow.name }}</h4>
        </div>

        <!-- 加载状态 -->
        <div v-if="loadingExecutions" class="flex items-center justify-center py-8">
          <RefreshCw class="w-6 h-6 text-primary animate-spin" />
        </div>

        <!-- 执行记录列表 -->
        <div v-else class="space-y-3">
          <div
            v-for="exec in executions"
            :key="exec.id"
            class="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
          >
            <div class="flex items-center gap-3">
              <component
                :is="getStatusIcon(exec.status)"
                :class="['w-5 h-5', getExecStatusColor(exec.status)]"
              />
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  执行 #{{ exec.id }}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ formatTime(exec.started_at) }}
                  <span v-if="exec.finished_at"> → {{ formatTime(exec.finished_at) }}</span>
                </p>
              </div>
            </div>
            <div class="text-right">
              <span :class="[
                'px-2 py-1 text-xs font-medium rounded-full whitespace-nowrap',
                exec.status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                exec.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                exec.status === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
              ]">
                {{ exec.status === 'success' ? '成功' : exec.status === 'failed' ? '失败' : exec.status === 'running' ? '运行中' : '等待中' }}
              </span>
              <p v-if="exec.error_message" class="text-xs text-red-500 mt-1 max-w-xs truncate">
                {{ exec.error_message }}
              </p>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="executions.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
            暂无执行记录
          </div>
        </div>
      </div>
    </CommonModal>

    <!-- 配置模态框 -->
    <CommonModal v-model="showConfigModal" title="工作流配置" size="lg">
      <div v-if="selectedWorkflow" class="space-y-6">
        <!-- 工作流信息 -->
        <div class="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <h4 class="font-medium text-gray-900 dark:text-white">{{ selectedWorkflow.name }}</h4>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ selectedWorkflow.description }}</p>
        </div>

        <!-- 配置表单 -->
        <div class="space-y-4">
          <h5 class="font-medium text-gray-900 dark:text-white">配置选项</h5>

          <!-- 动态渲染配置项 -->
          <template v-if="selectedWorkflow.config_schema?.properties">
            <div
              v-for="(prop, key) in selectedWorkflow.config_schema.properties"
              :key="key"
              class="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700 last:border-0"
            >
              <div class="flex-1">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {{ prop.title || key }}
                </label>
                <p v-if="prop.description" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {{ prop.description }}
                </p>
              </div>
              <div class="ml-4">
                <!-- 布尔类型：开关 -->
                <CommonToggle
                  v-if="prop.type === 'boolean'"
                  v-model="configForm[key]"
                />
                <!-- 数字类型：输入框 -->
                <input
                  v-else-if="prop.type === 'integer' || prop.type === 'number'"
                  v-model.number="configForm[key]"
                  type="number"
                  :min="prop.minimum"
                  :max="prop.maximum"
                  class="w-24 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
                <!-- 枚举类型：下拉框 -->
                <select
                  v-else-if="prop.enum"
                  v-model="configForm[key]"
                  class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option v-for="(opt, idx) in prop.enum" :key="opt" :value="opt">
                    {{ prop.enumNames?.[idx] || opt }}
                  </option>
                </select>
                <!-- 字符串类型：文本框 -->
                <input
                  v-else
                  v-model="configForm[key]"
                  type="text"
                  class="w-48 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </template>

          <div v-else class="text-center py-4 text-gray-500 dark:text-gray-400">
            该工作流暂无可配置项
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button
            @click="showConfigModal = false"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="saveConfig"
            :disabled="savingConfig"
            class="px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors disabled:opacity-50"
          >
            {{ savingConfig ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </CommonModal>
  </div>
</template>
