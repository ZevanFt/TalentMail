<script setup lang="ts">
import { Plus, Workflow, Play, Edit, Trash2, RefreshCw, Clock, CheckCircle, Send, MoreVertical, Eye, X, Copy, BookOpen } from 'lucide-vue-next'
import { VueFlow, MarkerType } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const router = useRouter()
const { getWorkflows, getWorkflow, deleteWorkflow: deleteWorkflowApi, getNodeTypes } = useApi()

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

// 加载工作流列表
const loadWorkflows = async () => {
  loading.value = true
  try {
    workflows.value = await getWorkflows()
  } catch (e) {
    console.error('加载工作流列表失败:', e)
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
  if (!confirm('确定要删除这个工作流吗？此操作不可恢复。')) return
  
  deleting.value = id
  try {
    await deleteWorkflowApi(id)
    workflows.value = workflows.value.filter(w => w.id !== id)
  } catch (e) {
    console.error('删除失败:', e)
    alert('删除失败')
  } finally {
    deleting.value = null
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
  } catch (e) {
    console.error('加载工作流预览失败:', e)
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
  } catch (e) {
    console.error('加载节点类型失败:', e)
  }
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
    <div v-else-if="workflows.length > 0" class="space-y-3">
      <div
        v-for="workflow in workflows"
        :key="workflow.id"
        class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between">
          <!-- 左侧信息 -->
          <div class="flex items-center gap-4 flex-1">
            <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <Workflow class="w-5 h-5 text-primary" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="font-semibold text-gray-900 dark:text-white truncate">
                  {{ workflow.name }}
                </h3>
                <span :class="['px-2 py-0.5 text-xs font-medium rounded-full shrink-0', getStatusColor(workflow.status)]">
                  {{ getStatusLabel(workflow.status) }}
                </span>
              </div>
              <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
                {{ workflow.description || '暂无描述' }}
              </p>
            </div>
          </div>

          <!-- 统计 -->
          <div class="hidden md:flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400 mx-4">
            <span class="flex items-center gap-1">
              <Play class="w-4 h-4" />
              {{ workflow.execution_count || 0 }}
            </span>
            <span class="flex items-center gap-1">
              v{{ workflow.version }}
            </span>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2">
            <button
              @click="openPreviewModal(workflow)"
              class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="预览流程图"
            >
              <Eye class="w-4 h-4" />
              预览
            </button>
            <button
              @click="editWorkflow(workflow.id)"
              class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <Edit class="w-4 h-4" />
              编辑
            </button>
            <button
              @click="deleteWorkflow(workflow.id)"
              :disabled="deleting === workflow.id"
              class="flex items-center justify-center w-8 h-8 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
            >
              <Trash2 v-if="deleting !== workflow.id" class="w-4 h-4" />
              <RefreshCw v-else class="w-4 h-4 animate-spin" />
            </button>
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
                    {{ selectedWorkflow?.description || '暂无描述' }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <button
                  @click="editWorkflow(selectedWorkflow?.id)"
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
              <!-- 加载状态 -->
              <div v-if="loadingPreview" class="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <RefreshCw class="w-8 h-8 text-primary animate-spin" />
              </div>
              
              <!-- 空状态 -->
              <div v-else-if="previewNodes.length === 0" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
                <Workflow class="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
                <p class="text-gray-500 dark:text-gray-400 mb-4">该工作流暂无节点</p>
                <button
                  @click="editWorkflow(selectedWorkflow?.id)"
                  class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
                >
                  <Edit class="w-4 h-4" />
                  开始编辑
                </button>
              </div>
              
              <div v-else class="absolute inset-0">
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
              </div>
              
              <!-- 统计信息 -->
              <div v-if="previewNodes.length > 0" class="absolute bottom-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-4 py-2 shadow-lg">
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
      @use="onTemplateUsed"
      @create-blank="createBlankWorkflow"
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