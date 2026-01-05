<script setup lang="ts">
import { Play, Settings, Eye, Clock, CheckCircle, XCircle, RefreshCw, Workflow, Plus, Edit, FileText, X, BookOpen } from 'lucide-vue-next'
import { VueFlow, MarkerType } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const router = useRouter()
const { getSystemWorkflows, getSystemWorkflowConfig, updateSystemWorkflowConfig, getWorkflowExecutions, getNodeTypes } = useApi()

// 状态
const loading = ref(true)
const workflows = ref<any[]>([])

// 模板选择弹窗
const showTemplateSelector = ref(false)
const selectedWorkflow = ref<any>(null)
const showConfigModal = ref(false)
const showExecutionModal = ref(false)
const showPreviewModal = ref(false)
const executions = ref<any[]>([])
const loadingExecutions = ref(false)

// 预览用节点类型
const nodeTypes = ref<any[]>([])

// Vue Flow 数据
const previewNodes = ref<any[]>([])
const previewEdges = ref<any[]>([])

// 配置表单
const configForm = ref<any>({})
const savingConfig = ref(false)

// 加载系统工作流列表
const loadWorkflows = async () => {
  loading.value = true
  try {
    workflows.value = await getSystemWorkflows()
  } catch (e: any) {
    console.error('加载工作流失败:', e)
  } finally {
    loading.value = false
  }
}

// 打开配置模态框
const openConfigModal = async (workflow: any) => {
  selectedWorkflow.value = workflow
  try {
    const response = await getSystemWorkflowConfig(workflow.code)
    configForm.value = { ...response.effective_config }
    showConfigModal.value = true
  } catch (e: any) {
    console.error('加载配置失败:', e)
  }
}

// 保存配置
const saveConfig = async () => {
  if (!selectedWorkflow.value) return
  savingConfig.value = true
  try {
    await updateSystemWorkflowConfig(selectedWorkflow.value.code, configForm.value)
    showConfigModal.value = false
  } catch (e: any) {
    console.error('保存配置失败:', e)
  } finally {
    savingConfig.value = false
  }
}

// 查看执行记录
const openExecutionModal = async (workflow: any) => {
  selectedWorkflow.value = workflow
  loadingExecutions.value = true
  showExecutionModal.value = true
  try {
    executions.value = await getWorkflowExecutions('system', workflow.id, undefined, 20)
  } catch (e: any) {
    console.error('加载执行记录失败:', e)
  } finally {
    loadingExecutions.value = false
  }
}

// 打开预览模态框
const openPreviewModal = (workflow: any) => {
  selectedWorkflow.value = workflow
  
  // 转换节点数据为 Vue Flow 格式
  previewNodes.value = (workflow.nodes || []).map((n: any) => ({
    id: n.node_id,
    type: 'custom',
    position: { x: n.position_x || 0, y: n.position_y || 0 },
    data: {
      label: n.name || n.node_subtype,
      nodeType: n.node_type,
      nodeSubtype: n.node_subtype,
      icon: getNodeIcon(n.node_subtype),
      color: getNodeColor(n.node_type),
      config: n.config || {}
    }
  }))
  
  // 转换边数据
  previewEdges.value = (workflow.edges || []).map((e: any) => ({
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
  
  showPreviewModal.value = true
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

// 获取分类标签
const getCategoryLabel = (category: string) => {
  const labels: Record<string, string> = {
    auth: '认证流程',
    email: '邮件流程',
    billing: '计费流程',
    admin: '管理流程'
  }
  return labels[category] || category
}

// 获取分类颜色
const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    auth: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    email: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    billing: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    admin: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400'
  }
  return colors[category] || 'bg-gray-100 text-gray-800'
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

// 获取状态颜色
const getStatusColor = (status: string) => {
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

// 编辑系统工作流（跳转到编辑器，传递系统工作流标识）
const editSystemWorkflow = (workflow: any) => {
  router.push(`/workflows/system-${workflow.code}`)
}

// 创建新系统工作流 - 打开模板选择弹窗
const createSystemWorkflow = () => {
  showTemplateSelector.value = true
}

// 直接创建空白系统工作流
const createBlankSystemWorkflow = () => {
  showTemplateSelector.value = false
  router.push('/workflows/new?type=system')
}

// 从模板创建后的回调
const onTemplateUsed = (template: any) => {
  showTemplateSelector.value = false
}

// 加载节点类型
const loadNodeTypes = async () => {
  try {
    nodeTypes.value = await getNodeTypes()
  } catch (e) {
    console.error('加载节点类型失败:', e)
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
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">系统工作流</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          管理系统核心业务流程，这些工作流会在特定事件时自动触发（如用户注册、密码重置等）
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
          @click="createSystemWorkflow"
          class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
        >
          <Plus class="w-4 h-4" />
          新建系统工作流
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <RefreshCw class="w-8 h-8 text-primary animate-spin" />
    </div>

    <!-- 工作流列表 -->
    <div v-else class="grid gap-4">
      <div
        v-for="workflow in workflows"
        :key="workflow.id"
        class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-6 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <!-- 左侧信息 -->
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Workflow class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ workflow.name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ workflow.name_en }} · {{ workflow.code }}
                </p>
              </div>
              <span :class="['px-2 py-1 text-xs font-medium rounded-full', getCategoryColor(workflow.category)]">
                {{ getCategoryLabel(workflow.category) }}
              </span>
            </div>
            
            <p class="mt-3 text-sm text-gray-600 dark:text-gray-400">
              {{ workflow.description }}
            </p>

            <!-- 节点数量统计 -->
            <div class="mt-4 flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
              <span>{{ workflow.nodes?.length || 0 }} 个节点</span>
              <span>{{ workflow.edges?.length || 0 }} 条连接</span>
              <span>版本 v{{ workflow.version }}</span>
            </div>
          </div>

          <!-- 右侧操作按钮 -->
          <div class="flex items-center gap-2">
            <button
              @click="openPreviewModal(workflow)"
              class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="预览流程图"
            >
              <Eye class="w-4 h-4" />
              <span class="hidden sm:inline">预览</span>
            </button>
            <button
              @click="openExecutionModal(workflow)"
              class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="查看执行记录"
            >
              <Clock class="w-4 h-4" />
              <span class="hidden sm:inline">记录</span>
            </button>
            <button
              @click="openConfigModal(workflow)"
              class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="配置工作流"
            >
              <Settings class="w-4 h-4" />
              <span class="hidden sm:inline">配置</span>
            </button>
            <button
              @click="editSystemWorkflow(workflow)"
              class="flex items-center gap-1.5 px-3 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
              title="编辑工作流"
            >
              <Edit class="w-4 h-4" />
              <span class="hidden sm:inline">编辑</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="workflows.length === 0" class="text-center py-16 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <Workflow class="w-8 h-8 text-gray-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          暂无系统工作流
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
          创建系统工作流来自动化核心业务流程
        </p>
        <button
          @click="createSystemWorkflow"
          class="inline-flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
        >
          <Plus class="w-5 h-5" />
          创建系统工作流
        </button>
      </div>
    </div>

    <!-- 与邮件模板的关系提示 -->
    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
      <div class="flex items-start gap-3">
        <FileText class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
        <div>
          <h4 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-1">💡 系统工作流与邮件模板</h4>
          <p class="text-sm text-blue-700 dark:text-blue-400">
            系统工作流中的"发送邮件"节点会使用系统邮件模板。您可以在「邮件模板管理」中预览和编辑模板内容。
          </p>
        </div>
      </div>
    </div>

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
                :class="['w-5 h-5', getStatusColor(exec.status)]"
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
                'px-2 py-1 text-xs font-medium rounded-full',
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

    <!-- 预览模态框 -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showPreviewModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          @click.self="showPreviewModal = false"
        >
          <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-[90vw] h-[85vh] max-w-6xl flex flex-col overflow-hidden">
            <!-- 头部 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Workflow class="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ selectedWorkflow?.name }}
                  </h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    {{ selectedWorkflow?.description }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <button
                  @click="editSystemWorkflow(selectedWorkflow)"
                  class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
                >
                  <Edit class="w-4 h-4" />
                  编辑
                </button>
                <button
                  @click="showPreviewModal = false"
                  class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X class="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            <!-- 流程图预览 -->
            <div class="flex-1 relative">
              <ClientOnly>
                <VueFlow
                  :nodes="previewNodes"
                  :edges="previewEdges"
                :default-viewport="{ zoom: 0.8 }"
                :min-zoom="0.2"
                :max-zoom="2"
                fit-view-on-init
                :nodes-draggable="false"
                :nodes-connectable="false"
                :elements-selectable="false"
              >
                <Background pattern-color="#94a3b8" :gap="20" />
                
                <!-- 自定义节点 -->
                <template #node-custom="{ data }">
                  <div
                    class="px-4 py-3 rounded-xl shadow-lg border-2 min-w-[140px]"
                    :style="{
                      backgroundColor: data.color + '20',
                      borderColor: data.color
                    }"
                  >
                    <div class="flex items-center gap-2">
                      <span class="text-lg">{{ data.icon }}</span>
                      <span class="font-medium text-gray-800 dark:text-white text-sm">{{ data.label }}</span>
                    </div>
                  </div>
                </template>
                </VueFlow>
              </ClientOnly>
              
              <!-- 图例 -->
              <div class="absolute bottom-4 left-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
                <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">节点类型</p>
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div class="flex items-center gap-1.5">
                    <span class="w-3 h-3 rounded bg-[#10b981]"></span>
                    <span class="text-gray-600 dark:text-gray-400">触发器</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="w-3 h-3 rounded bg-[#3b82f6]"></span>
                    <span class="text-gray-600 dark:text-gray-400">逻辑控制</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="w-3 h-3 rounded bg-[#f59e0b]"></span>
                    <span class="text-gray-600 dark:text-gray-400">邮件动作</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="w-3 h-3 rounded bg-[#06b6d4]"></span>
                    <span class="text-gray-600 dark:text-gray-400">数据处理</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="w-3 h-3 rounded bg-[#6b7280]"></span>
                    <span class="text-gray-600 dark:text-gray-400">结束节点</span>
                  </div>
                </div>
              </div>
              
              <!-- 统计信息 -->
              <div class="absolute bottom-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-4 py-2 shadow-lg">
                <p class="text-sm text-gray-600 dark:text-gray-400">
                  <span class="font-medium">{{ previewNodes.length }}</span> 个节点，
                  <span class="font-medium">{{ previewEdges.length }}</span> 条连接
                </p>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 工作流模板选择弹窗 -->
    <WorkflowTemplateSelector
      v-model="showTemplateSelector"
      scope="system"
      @use="onTemplateUsed"
      @create-blank="createBlankSystemWorkflow"
    />
  </div>
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
</style>