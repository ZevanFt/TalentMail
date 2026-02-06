<script setup lang="ts">
import { VueFlow, useVueFlow, Panel, MarkerType, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import {
  ArrowLeft, Save, Play, Plus, Settings, Trash2, GripVertical, Send, Check, X, BookOpen,
  // 节点图标
  Mail, User, Clock, Link, MousePointer, FileText, FileCode,
  GitBranch, ListFilter, Timer, GitMerge, Pause,
  Reply, Forward, FolderInput, Tag, Star, CheckCircle, Archive,
  ShieldCheck, Hash, UserPlus, UserCog, KeyRound, Lock,
  Globe, ScrollText, Zap, Bell, Database, Flag,
  CircleCheck, CircleX, Package, XCircle,
  // 版本历史
  History, RotateCcw, Eye
} from 'lucide-vue-next'
import type { Component } from 'vue'

const route = useRoute()
const router = useRouter()
const workflowId = computed(() => route.params.id as string)
const isNew = computed(() => workflowId.value === 'new')
const isSystemWorkflow = computed(() => {
  const typeParam = route.query.type as string
  return typeParam === 'system' || workflowId.value.startsWith('system-')
})
const systemWorkflowCode = computed(() => {
  if (workflowId.value.startsWith('system-')) {
    return workflowId.value.replace('system-', '')
  }
  return null
})

const { getNodeTypes, createWorkflow, getWorkflow, updateWorkflow, saveWorkflowCanvas, publishWorkflow, getSystemWorkflow, getEmailTemplates, getWorkflowVersions, getWorkflowVersion, restoreWorkflowVersion } = useApi()

// 邮件模板列表（用于"发送邮件"节点的模板选择）
const emailTemplates = ref<any[]>([])

// 工作流数据
const workflow = ref<any>({
  id: null,
  name: '新工作流',
  description: '',
  category: 'email',
  status: 'draft',
  version: 1
})

// 新建工作流触发器选择弹窗
const showTriggerSelector = ref(false)
const selectedTriggerType = ref<any>(null)

// 获取触发器类型列表
const triggerTypes = computed(() => {
  return nodeTypes.value.filter(nt => nt.category === 'trigger')
})

// Vue Flow 实例
const { 
  nodes, 
  edges, 
  addNodes, 
  addEdges, 
  removeNodes,
  setNodes,
  setEdges,
  onConnect, 
  onNodeDragStop,
  project,
  fitView
} = useVueFlow()

// 节点类型数据
const nodeTypes = ref<any[]>([])
const nodeTypesByCategory = computed(() => {
  const grouped: Record<string, any[]> = {}
  for (const nt of nodeTypes.value) {
    const category = nt.category as string
    if (!grouped[category]) {
      grouped[category] = []
    }
    grouped[category].push(nt)
  }
  return grouped
})

// 分类排序顺序
const categoryOrder = ['trigger', 'logic', 'email_action', 'email_operation', 'data', 'integration', 'end']
const sortedCategories = computed(() => {
  return Object.keys(nodeTypesByCategory.value).sort((a, b) => {
    return categoryOrder.indexOf(a) - categoryOrder.indexOf(b)
  })
})

// 分类标签（使用 Lucide 图标名称）
const categoryLabels: Record<string, { label: string; icon: string }> = {
  trigger: { label: '触发器', icon: 'Zap' },
  logic: { label: '逻辑控制', icon: 'GitBranch' },
  email_action: { label: '邮件动作', icon: 'Send' },
  email_operation: { label: '邮件处理', icon: 'Mail' },
  data: { label: '数据处理', icon: 'Database' },
  integration: { label: '集成', icon: 'Link' },
  end: { label: '结束节点', icon: 'Flag' }
}

// 图标组件映射
const iconComponents: Record<string, Component> = {
  // 触发器
  Mail, User, Clock, Link, MousePointer, FileText, FileCode,
  // 逻辑
  GitBranch, ListFilter, Timer, GitMerge, Pause,
  // 邮件动作
  Send, Reply, Forward,
  // 邮件处理
  FolderInput, Tag, Star, CheckCircle, Trash2, Archive,
  // TagOff 不存在于 lucide-vue-next，用 XCircle 替代
  TagOff: XCircle,
  // 数据处理
  ShieldCheck, Hash, UserPlus, UserCog, KeyRound, Lock,
  // 集成
  Globe, ScrollText, Zap, Bell,
  // 结束
  CircleCheck, CircleX,
  // 分类图标
  Database, Flag,
  // 默认
  Package
}

// 获取图标组件
const getIconComponent = (iconName: string): Component => {
  return iconComponents[iconName] ?? Package
}

// 选中的节点
const selectedNode = ref<any>(null)
const showNodeConfig = ref(false)

// 获取选中节点的配置模式（优先从节点数据获取，否则从节点类型获取）
const selectedNodeConfigSchema = computed(() => {
  if (!selectedNode.value) return null
  // 先尝试从节点数据获取
  if (selectedNode.value.data?.configSchema) {
    return selectedNode.value.data.configSchema
  }
  // 否则从节点类型获取
  const subtype = selectedNode.value.data?.nodeSubtype
  if (subtype) {
    const nodeType = nodeTypes.value.find(nt => nt.code === subtype)
    return nodeType?.config_schema || null
  }
  return null
})

// 加载状态
const loading = ref(false)
const saving = ref(false)
const publishing = ref(false)

// 版本历史
const showVersionHistory = ref(false)
const loadingVersions = ref(false)
const versions = ref<any[]>([])
const previewingVersion = ref<any>(null)
const restoringVersion = ref(false)

// 工作流设置面板
const showWorkflowSettings = ref(false)
const savingSettings = ref(false)

// 工作流配置项（从节点自动提取 + 手动添加）
const workflowConfigItems = computed(() => {
  const items: Array<{
    key: string
    title: string
    type: string
    description?: string
    default?: any
    source: 'auto' | 'manual'
    nodeId?: string
    nodeName?: string
    enabled: boolean
  }> = []

  // 自动从节点提取可提升的配置项
  for (const node of nodes.value) {
    const nodeType = nodeTypes.value.find((nt: any) => nt.code === node.data?.nodeSubtype)
    if (nodeType?.config_schema?.properties) {
      for (const [key, prop] of Object.entries(nodeType.config_schema.properties) as any) {
        if (prop.promotable === true) {
          items.push({
            key: `${node.id}_${key}`,
            title: prop.title || key,
            type: prop.type || 'string',
            description: prop.description,
            default: prop.default,
            source: 'auto',
            nodeId: node.id,
            nodeName: node.data?.label,
            enabled: workflow.value.config_schema?.properties?.[`${node.id}_${key}`] !== undefined
          })
        }
      }
    }
  }

  return items
})

// 保存工作流设置
const saveWorkflowSettings = async () => {
  savingSettings.value = true
  try {
    // 如果是新工作流，需要先创建
    if (!workflow.value.id) {
      const created = await createWorkflow({
        name: workflow.value.name,
        description: workflow.value.description,
        category: workflow.value.category || 'email'
      })
      workflow.value.id = created.id
      // 更新 URL（不刷新页面）
      window.history.replaceState({}, '', `/workflows/${created.id}`)
    }

    await updateWorkflow(workflow.value.id, {
      name: workflow.value.name,
      description: workflow.value.description,
      config_schema: workflow.value.config_schema,
      default_config: workflow.value.default_config,
      config: workflow.value.config
    } as any)
    showWorkflowSettings.value = false
    showMessage('success', '设置保存成功')
  } catch (e: any) {
    console.error('保存设置失败:', e)
    showMessage('error', e.data?.detail || '保存设置失败')
  } finally {
    savingSettings.value = false
  }
}

// 添加自定义配置项
const addCustomConfigItem = () => {
  if (!workflow.value.config_schema) {
    workflow.value.config_schema = { type: 'object', properties: {} }
  }
  if (!workflow.value.config_schema.properties) {
    workflow.value.config_schema.properties = {}
  }
  const key = `custom_${Date.now()}`
  workflow.value.config_schema.properties[key] = {
    type: 'boolean',
    title: '新配置项',
    description: '',
    default: false,
    bindings: [] // 关联的节点配置：[{ nodeId: 'xxx', field: 'yyy' }]
  }
  if (!workflow.value.default_config) {
    workflow.value.default_config = {}
  }
  workflow.value.default_config[key] = false
}

// 删除配置项
const removeConfigItem = (key: string) => {
  if (workflow.value.config_schema?.properties?.[key]) {
    delete workflow.value.config_schema.properties[key]
  }
  if (workflow.value.default_config?.[key] !== undefined) {
    delete workflow.value.default_config[key]
  }
}

// 添加节点绑定
const addConfigBinding = (configKey: string) => {
  const prop = workflow.value.config_schema?.properties?.[configKey]
  if (!prop) return
  if (!prop.bindings) {
    prop.bindings = []
  }
  prop.bindings.push({ nodeId: '', field: '' })
}

// 删除节点绑定
const removeConfigBinding = (configKey: string, index: number) => {
  const prop = workflow.value.config_schema?.properties?.[configKey]
  if (prop?.bindings) {
    prop.bindings.splice(index, 1)
  }
}

// 获取节点可配置字段列表
const getNodeConfigFields = (nodeId: string): Array<{ key: string; title: string }> => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return []

  const nodeSubtype = node.data?.nodeSubtype
  const nodeType = nodeTypes.value.find((nt: any) => nt.code === nodeSubtype)
  if (!nodeType?.config_schema?.properties) return []

  return Object.entries(nodeType.config_schema.properties).map(([key, prop]: [string, any]) => ({
    key,
    title: prop.title || key
  }))
}

// 消息提示
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)
const showMessage = (type: 'success' | 'error', text: string) => {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 3000)
}

// 加载节点类型
const loadNodeTypes = async () => {
  try {
    nodeTypes.value = await getNodeTypes()
  } catch (e) {
    console.error('加载节点类型失败:', e)
    showMessage('error', '加载节点类型失败')
  }
}

// 加载邮件模板列表
const loadEmailTemplates = async () => {
  try {
    emailTemplates.value = await getEmailTemplates()
  } catch (e) {
    console.error('加载邮件模板失败:', e)
  }
}

// 判断是否是需要模板选择的节点类型
const isTemplateSelectNode = (nodeSubtype: string): boolean => {
  const templateNodes = ['action_send_email', 'action_reply', 'action_auto_reply', 'email_send_template']
  return templateNodes.includes(nodeSubtype)
}

// 跳转到教程页面（新标签页打开）
const goToTutorial = () => {
  window.open('/workflows/tutorial', '_blank')
}

// 确认选择触发器并添加到画布
const confirmTriggerSelection = () => {
  if (!selectedTriggerType.value) return
  
  const trigger = selectedTriggerType.value
  addNodes([
    {
      id: 'trigger_1',
      type: 'custom',
      position: { x: 250, y: 50 },
      data: {
        label: trigger.name,
        nodeType: 'trigger',
        nodeSubtype: trigger.code,
        icon: trigger.icon,
        color: trigger.color || '#10b981',
        config: {},
        configSchema: trigger.config_schema
      }
    }
  ])
  
  showTriggerSelector.value = false
  selectedTriggerType.value = null
}

// 加载工作流数据
const loadWorkflow = async () => {
  if (isNew.value) {
    // 新建工作流，显示触发器选择弹窗
    showTriggerSelector.value = true
    return
  }
  
  loading.value = true
  try {
    // 根据是否是系统工作流，调用不同的 API
    if (systemWorkflowCode.value) {
      // 系统工作流
      const data = await getSystemWorkflow(systemWorkflowCode.value)
      workflow.value = {
        id: data.id,
        name: data.name,
        description: data.description,
        category: data.category,
        status: data.is_active ? 'published' : 'draft',
        version: data.version,
        is_system: true,
        code: data.code
      }
      
      // 转换节点数据为 Vue Flow 格式
      const vfNodes = (data.nodes || []).map((n: any) => ({
        id: n.node_id,
        type: 'custom',
        position: { x: n.position_x || 0, y: n.position_y || 0 },
        data: {
          label: n.name || n.node_subtype,
          nodeType: n.node_type,
          nodeSubtype: n.node_subtype,
          icon: getNodeIcon(n.node_subtype),
          color: getNodeColor(n.node_type),
          config: n.config || {},
          configSchema: getConfigSchema(n.node_subtype)
        }
      }))
      
      // 转换边数据
      const vfEdges = (data.edges || []).map((e: any) => ({
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
      
      setNodes(vfNodes)
      setEdges(vfEdges)
    } else {
      // 用户自定义工作流
      const data = await getWorkflow(parseInt(workflowId.value))
      workflow.value = data.workflow
      
      // 转换节点数据为 Vue Flow 格式
      const vfNodes = data.nodes.map((n: any) => ({
        id: n.node_id,
        type: 'custom',
        position: { x: n.position_x, y: n.position_y },
        data: {
          label: n.name || n.node_subtype,
          nodeType: n.node_type,
          nodeSubtype: n.node_subtype,
          icon: getNodeIcon(n.node_subtype),
          color: getNodeColor(n.node_type),
          config: n.config || {},
          configSchema: getConfigSchema(n.node_subtype)
        }
      }))
      
      // 转换边数据
      const vfEdges = data.edges.map((e: any) => ({
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
      
      setNodes(vfNodes)
      setEdges(vfEdges)
    }
  } catch (e: any) {
    console.error('加载工作流失败:', e)
    showMessage('error', e.data?.detail || '加载工作流失败')
  } finally {
    loading.value = false
  }
}

// 获取节点图标
const getNodeIcon = (subtype: string): string => {
  const nodeType = nodeTypes.value.find(nt => nt.code === subtype)
  return nodeType?.icon || '📦'
}

// 获取节点颜色
const getNodeColor = (category: string): string => {
  const colors: Record<string, string> = {
    trigger: '#10b981',
    logic: '#8b5cf6',
    email_action: '#3b82f6',
    email_operation: '#06b6d4',
    data: '#f59e0b',
    integration: '#ec4899',
    end: '#6b7280'
  }
  return colors[category] || '#6b7280'
}

// 获取配置 Schema
const getConfigSchema = (subtype: string) => {
  const nodeType = nodeTypes.value.find(nt => nt.code === subtype)
  return nodeType?.config_schema || null
}

// 添加节点 - 拖拽
const onDragStart = (event: DragEvent, nodeType: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify(nodeType))
    event.dataTransfer.effectAllowed = 'move'
  }
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const onDrop = (event: DragEvent) => {
  const data = event.dataTransfer?.getData('application/vueflow')
  if (!data) return

  const nodeType = JSON.parse(data)
  
  // 获取画布位置
  const canvasElement = document.querySelector('.vue-flow') as HTMLElement
  if (!canvasElement) return
  
  const { left, top } = canvasElement.getBoundingClientRect()
  const position = project({
    x: event.clientX - left,
    y: event.clientY - top
  })

  // 生成唯一 ID
  const nodeId = `${nodeType.code}_${Date.now()}`
  
  addNodes([
    {
      id: nodeId,
      type: 'custom',
      position,
      data: {
        label: nodeType.name,
        nodeType: nodeType.category,
        nodeSubtype: nodeType.code,
        icon: nodeType.icon,
        color: nodeType.color,
        config: {},
        configSchema: nodeType.config_schema
      }
    }
  ])
}

// 连接节点
onConnect((params: any) => {
  addEdges([
    {
      ...params,
      id: `e_${params.source}_${params.target}_${Date.now()}`,
      type: 'smoothstep',
      animated: true,
      markerEnd: MarkerType.ArrowClosed
    }
  ])
})

// 选中节点
const onNodeClick = (event: any) => {
  const node = event.node
  selectedNode.value = node
  showNodeConfig.value = true
}

// 点击画布空白处
const onPaneClick = () => {
  showNodeConfig.value = false
  selectedNode.value = null
}

// 删除选中节点
const deleteSelectedNode = () => {
  if (selectedNode.value) {
    removeNodes([selectedNode.value.id])
    selectedNode.value = null
    showNodeConfig.value = false
  }
}

// 保存工作流
const saveWorkflowData = async () => {
  saving.value = true
  try {
    // 如果是新工作流，先创建
    if (isNew.value || !workflow.value.id) {
      const created = await createWorkflow({
        name: workflow.value.name,
        description: workflow.value.description,
        category: workflow.value.category
      })
      workflow.value.id = created.id
      
      // 使用 history.replaceState 更新 URL，不触发组件重载
      window.history.replaceState({}, '', `/workflows/${created.id}`)
    } else {
      // 更新基本信息
      await updateWorkflow(workflow.value.id, {
        name: workflow.value.name,
        description: workflow.value.description
      })
    }
    
    // 保存画布（节点和边）
    const nodesData = nodes.value.map(n => ({
      node_id: n.id,
      node_type: n.data.nodeType,
      node_subtype: n.data.nodeSubtype,
      name: n.data.label,
      position_x: Math.round(n.position.x),
      position_y: Math.round(n.position.y),
      config: n.data.config || {}
    }))
    
    const edgesData = edges.value.map(e => ({
      edge_id: e.id,
      source_node_id: e.source,
      target_node_id: e.target,
      source_handle: e.sourceHandle || null,
      target_handle: e.targetHandle || null,
      label: (e as any).label || null
    }))
    
    const result = await saveWorkflowCanvas(workflow.value.id, nodesData, edgesData)
    workflow.value.version = result.version
    
    showMessage('success', '保存成功')
  } catch (e: any) {
    console.error('保存失败:', e)
    showMessage('error', e.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 发布工作流
const publishWorkflowData = async () => {
  if (!workflow.value.id) {
    showMessage('error', '请先保存工作流')
    return
  }
  
  if (nodes.value.length === 0) {
    showMessage('error', '工作流没有任何节点')
    return
  }
  
  publishing.value = true
  try {
    const result = await publishWorkflow(workflow.value.id)
    workflow.value.status = result.status
    showMessage('success', '发布成功')
  } catch (e: any) {
    console.error('发布失败:', e)
    showMessage('error', e.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

// 返回到设置页面
const goBack = () => {
  // 判断是系统工作流还是用户工作流，返回到对应的设置页面
  // 1. 检查 URL 参数 type=system（新建工作流时使用）
  // 2. 检查 workflowId 是否以 system- 开头（已有工作流）
  // 3. 检查工作流数据的 is_system 标志
  const typeParam = route.query.type as string
  const isSystemWorkflow = typeParam === 'system' ||
                           workflowId.value.startsWith('system-') ||
                           workflow.value?.is_system === true
  
  if (isSystemWorkflow) {
    router.push('/settings?tab=system-workflows')
  } else {
    router.push('/settings?tab=my-workflows')
  }
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadNodeTypes(),
    loadEmailTemplates()
  ])
  await loadWorkflow()
  
  // 延迟适配视图
  setTimeout(() => {
    fitView({ padding: 0.2 })
  }, 100)
})

// 加载版本历史
const loadVersions = async () => {
  if (!workflow.value.id || isNew.value) return
  
  loadingVersions.value = true
  try {
    versions.value = await getWorkflowVersions(workflow.value.id)
  } catch (e: any) {
    console.error('加载版本历史失败:', e)
    showMessage('error', e.data?.detail || '加载版本历史失败')
  } finally {
    loadingVersions.value = false
  }
}

// 打开版本历史面板
const openVersionHistory = async () => {
  showVersionHistory.value = true
  await loadVersions()
}

// 预览某个版本
const previewVersion = async (version: any) => {
  try {
    const detail = await getWorkflowVersion(workflow.value.id, version.version)
    previewingVersion.value = detail
    
    // 将版本的节点和边加载到画布上进行预览
    const vfNodes = (detail.nodes_snapshot || []).map((n: any) => ({
      id: n.node_id,
      type: 'custom',
      position: { x: n.position_x || 0, y: n.position_y || 0 },
      data: {
        label: n.name || n.node_subtype,
        nodeType: n.node_type,
        nodeSubtype: n.node_subtype,
        icon: getNodeIcon(n.node_subtype),
        color: getNodeColor(n.node_type),
        config: n.config || {},
        configSchema: getConfigSchema(n.node_subtype)
      }
    }))
    
    const vfEdges = (detail.edges_snapshot || []).map((e: any) => ({
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
    
    setNodes(vfNodes)
    setEdges(vfEdges)
    
    showMessage('success', `正在预览版本 v${version.version}`)
  } catch (e: any) {
    console.error('加载版本详情失败:', e)
    showMessage('error', e.data?.detail || '加载版本详情失败')
  }
}

// 退出预览模式，恢复当前版本
const exitPreview = async () => {
  previewingVersion.value = null
  await loadWorkflow()
  showMessage('success', '已恢复到当前版本')
}

// 恢复到某个版本
const restoreToVersion = async (version: any) => {
  if (!confirm(`确定要恢复到版本 v${version.version} 吗？这将创建一个新版本。`)) return
  
  restoringVersion.value = true
  try {
    const result = await restoreWorkflowVersion(workflow.value.id, version.version)
    workflow.value.version = result.new_version
    previewingVersion.value = null
    
    // 重新加载工作流和版本历史
    await loadWorkflow()
    await loadVersions()
    
    showMessage('success', `已恢复到版本 v${version.version}，当前版本为 v${result.new_version}`)
  } catch (e: any) {
    console.error('恢复版本失败:', e)
    showMessage('error', e.data?.detail || '恢复版本失败')
  } finally {
    restoringVersion.value = false
  }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 编辑器使用全屏布局（无侧边栏）+ 禁用 SSR
definePageMeta({
  layout: false,
  ssr: false
})
</script>

<template>
  <div class="flex h-screen bg-gray-50 dark:bg-bg-dark overflow-hidden">
    <!-- 左侧节点面板 -->
    <div class="w-64 bg-white dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0 h-full">
      <!-- 返回按钮和名称 -->
      <div class="h-14 flex items-center px-4 gap-2 border-b border-gray-100 dark:border-gray-800">
        <button
          @click="goBack"
          class="flex items-center justify-center w-8 h-8 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ArrowLeft class="w-5 h-5" />
        </button>
        <input
          v-model="workflow.name"
          class="flex-1 bg-transparent font-bold text-gray-900 dark:text-white focus:outline-none text-sm"
          placeholder="工作流名称"
        />
      </div>

      <!-- 节点列表 - 添加 min-h-0 确保 flex 子元素可以滚动 -->
      <div class="flex-1 min-h-0 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        <div v-for="category in sortedCategories" :key="category" class="space-y-2">
          <h3 class="flex items-center gap-1.5 text-xs font-bold text-gray-400 uppercase tracking-wider">
            <component :is="getIconComponent(categoryLabels[category]?.icon || 'Package')" class="w-3.5 h-3.5" />
            {{ categoryLabels[category]?.label || category }}
          </h3>
          <div class="space-y-1">
            <div
              v-for="nodeType in nodeTypesByCategory[category]"
              :key="nodeType.code"
              draggable="true"
              @dragstart="(e) => onDragStart(e, nodeType)"
              class="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-grab active:cursor-grabbing transition-colors group"
            >
              <component :is="getIconComponent(nodeType.icon)" class="w-4 h-4" :style="{ color: nodeType.color }" />
              <span class="text-sm text-gray-700 dark:text-gray-300 flex-1">{{ nodeType.name }}</span>
              <GripVertical class="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="nodeTypes.length === 0" class="text-center py-8">
          <div class="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
          <p class="text-sm text-gray-500 mt-2">加载节点类型...</p>
        </div>
      </div>
    </div>

    <!-- 中间画布区域 -->
    <div 
      class="flex-1 relative"
      @dragover="onDragOver"
      @drop="onDrop"
    >
      <!-- 加载状态 -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-50/80 dark:bg-bg-dark/80 z-50">
        <div class="text-center">
          <div class="animate-spin w-8 h-8 border-3 border-primary border-t-transparent rounded-full mx-auto"></div>
          <p class="text-sm text-gray-500 mt-3">加载工作流...</p>
        </div>
      </div>
      
      <!-- 消息提示 -->
      <Transition name="fade">
        <div
          v-if="message"
          :class="[
            'absolute top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-lg shadow-lg flex items-center gap-2',
            message.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          ]"
        >
          <Check v-if="message.type === 'success'" class="w-4 h-4" />
          <X v-else class="w-4 h-4" />
          {{ message.text }}
        </div>
      </Transition>
      
      <ClientOnly>
        <VueFlow
          :nodes="nodes"
          :edges="edges"
          :default-viewport="{ zoom: 1 }"
        :min-zoom="0.2"
        :max-zoom="4"
        fit-view-on-init
        @nodeClick="onNodeClick"
        @paneClick="onPaneClick"
      >
        <!-- 背景 -->
        <Background pattern-color="#94a3b8" :gap="20" />
        
        <!-- 控制栏 -->
        <Controls position="bottom-left" />
        
        <!-- 小地图 -->
        <MiniMap position="bottom-right" />

        <!-- 顶部工具栏 -->
        <Panel position="top-right" class="flex items-center gap-2">
          <!-- 教程按钮 -->
          <button
            @click="goToTutorial"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="查看教程"
          >
            <BookOpen class="w-4 h-4" />
            <span class="hidden sm:inline">教程</span>
          </button>

          <!-- 工作流设置按钮 -->
          <button
            @click="showWorkflowSettings = true"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="工作流设置"
          >
            <Settings class="w-4 h-4" />
            <span class="hidden sm:inline">设置</span>
          </button>

          <!-- 版本历史按钮 -->
          <button
            @click="openVersionHistory"
            :disabled="isNew || !workflow.id"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="版本历史"
          >
            <History class="w-4 h-4" />
            <span class="hidden sm:inline">历史</span>
          </button>

          <!-- 分隔线 -->
          <div class="w-px h-6 bg-gray-300 dark:bg-gray-600"></div>
          
          <!-- 状态标签 -->
          <span
            v-if="workflow.status"
            :class="[
              'px-2 py-1 text-xs font-medium rounded-full',
              workflow.status === 'published' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
              workflow.status === 'draft' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
              'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
            ]"
          >
            {{ workflow.status === 'published' ? '已发布' : workflow.status === 'draft' ? '草稿' : workflow.status }}
          </span>
          
          <span class="text-xs text-gray-400">v{{ workflow.version }}</span>
          
          <button
            @click="saveWorkflowData"
            :disabled="saving"
            class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            <Save class="w-4 h-4" />
            {{ saving ? '保存中...' : '保存' }}
          </button>
          
          <button
            @click="publishWorkflowData"
            :disabled="publishing || !workflow.id"
            class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Send class="w-4 h-4" />
            {{ publishing ? '发布中...' : '发布' }}
          </button>
        </Panel>

        <!-- 自定义节点 -->
        <template #node-custom="{ data }">
          <!-- 输入连接点（顶部）- 触发器节点不显示输入 -->
          <Handle
            v-if="data.nodeType !== 'trigger'"
            type="target"
            :position="Position.Top"
            class="!w-3 !h-3 !bg-gray-400 hover:!bg-primary !border-2 !border-white dark:!border-gray-900 !-top-1.5 transition-colors"
          />
          
          <!-- 节点主体 -->
          <div
            class="px-4 py-3 rounded-xl shadow-lg border-2 min-w-[160px] transition-shadow hover:shadow-xl"
            :style="{
              backgroundColor: data.color + '20',
              borderColor: data.color
            }"
          >
            <div class="flex items-center gap-2">
              <component :is="getIconComponent(data.icon)" class="w-5 h-5" :style="{ color: data.color }" />
              <span class="font-medium text-gray-800 dark:text-white text-sm">{{ data.label }}</span>
            </div>
          </div>
          
          <!-- 输出连接点（底部） -->
          <!-- 条件分支节点显示两个输出端口（是/否） -->
          <template v-if="data.nodeSubtype === 'logic_condition'">
            <!-- 左侧输出（否/false） -->
            <Handle
              id="false"
              type="source"
              :position="Position.Bottom"
              class="!w-3 !h-3 !bg-red-400 hover:!bg-red-500 !border-2 !border-white dark:!border-gray-900 !-bottom-1.5 transition-colors"
              :style="{ left: '30%' }"
            />
            <!-- 右侧输出（是/true） -->
            <Handle
              id="true"
              type="source"
              :position="Position.Bottom"
              class="!w-3 !h-3 !bg-green-400 hover:!bg-green-500 !border-2 !border-white dark:!border-gray-900 !-bottom-1.5 transition-colors"
              :style="{ left: '70%' }"
            />
          </template>
          <!-- 普通节点显示单个输出端口（结束节点除外） -->
          <Handle
            v-else-if="data.nodeType !== 'end'"
            type="source"
            :position="Position.Bottom"
            class="!w-3 !h-3 !bg-gray-400 hover:!bg-primary !border-2 !border-white dark:!border-gray-900 !-bottom-1.5 transition-colors"
          />
        </template>
        </VueFlow>
      </ClientOnly>
    </div>

    <!-- 右侧配置面板 -->
    <Transition name="slide">
      <div
        v-if="showNodeConfig && selectedNode"
        class="w-80 bg-white dark:bg-bg-panelDark border-l border-gray-200 dark:border-border-dark flex flex-col shrink-0"
      >
        <!-- 标题 -->
        <div class="h-14 flex items-center justify-between px-4 border-b border-gray-100 dark:border-gray-800">
          <div class="flex items-center gap-2">
            <component :is="getIconComponent(selectedNode.data.icon)" class="w-5 h-5" :style="{ color: selectedNode.data.color }" />
            <span class="font-bold text-gray-900 dark:text-white text-sm">{{ selectedNode.data.label }}</span>
          </div>
          <button
            @click="showNodeConfig = false"
            class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X class="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <!-- 配置表单 -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
          <!-- 节点名称 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              节点名称
            </label>
            <input
              v-model="selectedNode.data.label"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
            />
          </div>

          <!-- 节点类型信息 -->
          <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p class="text-xs text-gray-500 dark:text-gray-400">节点类型</p>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ selectedNode.data.nodeSubtype }}</p>
          </div>

          <!-- 动态配置项 -->
          <template v-if="selectedNodeConfigSchema?.properties">
            <div
              v-for="(prop, key) in selectedNodeConfigSchema.properties"
              :key="key"
              class="space-y-1"
            >
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ prop.title || key }}
                <span v-if="selectedNodeConfigSchema.required?.includes(key)" class="text-red-500">*</span>
              </label>
              <p v-if="prop.description" class="text-xs text-gray-500 dark:text-gray-400">
                {{ prop.description }}
              </p>
              
              <!-- 邮件模板选择（特殊处理 template_code 字段） -->
              <select
                v-if="key === 'template_code'"
                v-model="selectedNode.data.config[key]"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              >
                <option value="">请选择邮件模板</option>
                <option v-for="template in emailTemplates" :key="template.code" :value="template.code">
                  {{ template.name }} ({{ template.code }})
                </option>
              </select>
              
              <!-- 布尔类型 -->
              <CommonToggle
                v-else-if="prop.type === 'boolean'"
                v-model="selectedNode.data.config[key]"
              />
              
              <!-- 数字类型 -->
              <input
                v-else-if="prop.type === 'integer' || prop.type === 'number'"
                v-model.number="selectedNode.data.config[key]"
                type="number"
                :min="prop.minimum"
                :max="prop.maximum"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              />
              
              <!-- 枚举类型 -->
              <select
                v-else-if="prop.enum"
                v-model="selectedNode.data.config[key]"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              >
                <option v-for="(opt, idx) in prop.enum" :key="opt" :value="opt">
                  {{ prop.enumNames?.[idx] || opt }}
                </option>
              </select>
              
              <!-- 多行文本 -->
              <textarea
                v-else-if="prop.format === 'html' || prop.format === 'textarea'"
                v-model="selectedNode.data.config[key]"
                rows="4"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              />
              
              <!-- 普通文本 -->
              <input
                v-else
                v-model="selectedNode.data.config[key]"
                type="text"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              />
            </div>
          </template>
          
          <!-- 无配置项 -->
          <div v-else class="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
            此节点无需配置
          </div>
        </div>

        <!-- 删除按钮 -->
        <div class="p-4 border-t border-gray-100 dark:border-gray-800">
          <button
            @click="deleteSelectedNode"
            class="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
          >
            <Trash2 class="w-4 h-4" />
            删除节点
          </button>
        </div>
      </div>
    </Transition>

    <!-- 工作流设置面板 -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showWorkflowSettings"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          @click.self="showWorkflowSettings = false"
        >
          <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
            <!-- 头部 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Settings class="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">工作流设置</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">配置工作流的基本信息和全局配置项</p>
                </div>
              </div>
              <button
                @click="showWorkflowSettings = false"
                class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X class="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <!-- 内容 -->
            <div class="flex-1 overflow-y-auto p-6 space-y-6">
              <!-- 基础信息 -->
              <div class="space-y-4">
                <h4 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <span class="w-1 h-4 bg-primary rounded-full"></span>
                  基础信息
                </h4>
                <div class="grid gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">工作流名称</label>
                    <input
                      v-model="workflow.name"
                      type="text"
                      class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
                    <textarea
                      v-model="workflow.description"
                      rows="3"
                      class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>

              <!-- 全局配置项 -->
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <h4 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="w-1 h-4 bg-primary rounded-full"></span>
                    全局配置项
                  </h4>
                  <button
                    @click="addCustomConfigItem"
                    class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors"
                  >
                    <Plus class="w-4 h-4" />
                    添加配置项
                  </button>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  这些配置项会在工作流列表的「配置」按钮中显示，并会同步到关联的节点配置
                </p>

                <!-- 已有配置项 -->
                <div v-if="workflow.config_schema?.properties && Object.keys(workflow.config_schema.properties).length > 0" class="space-y-4">
                  <div
                    v-for="(prop, key) in workflow.config_schema.properties"
                    :key="key"
                    class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg space-y-4"
                  >
                    <!-- 基本信息 -->
                    <div class="flex items-start gap-4">
                      <div class="flex-1 grid grid-cols-2 gap-4">
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">配置名称</label>
                          <input
                            v-model="prop.title"
                            type="text"
                            placeholder="例如：需要邮箱验证"
                            class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">类型</label>
                          <select
                            v-model="prop.type"
                            class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          >
                            <option value="boolean">开关（布尔值）</option>
                            <option value="string">文本</option>
                            <option value="integer">数字</option>
                          </select>
                        </div>
                        <div class="col-span-2">
                          <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">描述</label>
                          <input
                            v-model="prop.description"
                            type="text"
                            placeholder="配置项说明..."
                            class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">默认值</label>
                          <template v-if="prop.type === 'boolean'">
                            <select
                              v-model="workflow.default_config[key]"
                              class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            >
                              <option :value="true">开启</option>
                              <option :value="false">关闭</option>
                            </select>
                          </template>
                          <template v-else-if="prop.type === 'integer'">
                            <input
                              v-model.number="workflow.default_config[key]"
                              type="number"
                              class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                          </template>
                          <template v-else>
                            <input
                              v-model="workflow.default_config[key]"
                              type="text"
                              class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                          </template>
                        </div>
                      </div>
                      <button
                        @click="removeConfigItem(key as string)"
                        class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        title="删除配置项"
                      >
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>

                    <!-- 节点绑定 -->
                    <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <div class="flex items-center justify-between mb-2">
                        <label class="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                          <Link class="w-3.5 h-3.5" />
                          关联节点配置
                        </label>
                        <button
                          @click="addConfigBinding(key as string)"
                          class="text-xs text-primary hover:text-primary/80 flex items-center gap-1"
                        >
                          <Plus class="w-3 h-3" />
                          添加关联
                        </button>
                      </div>
                      <p class="text-xs text-gray-400 dark:text-gray-500 mb-2">
                        当此配置项的值改变时，会自动同步到关联的节点配置字段
                      </p>

                      <!-- 绑定列表 -->
                      <div v-if="prop.bindings && prop.bindings.length > 0" class="space-y-2">
                        <div
                          v-for="(binding, bIndex) in prop.bindings"
                          :key="bIndex"
                          class="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                        >
                          <select
                            v-model="binding.nodeId"
                            class="flex-1 px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="">选择节点...</option>
                            <option v-for="node in nodes" :key="node.id" :value="node.id">
                              {{ node.data?.label || node.id }}
                            </option>
                          </select>
                          <span class="text-gray-400 text-xs">→</span>
                          <select
                            v-model="binding.field"
                            :disabled="!binding.nodeId"
                            class="flex-1 px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50"
                          >
                            <option value="">选择字段...</option>
                            <option
                              v-for="field in getNodeConfigFields(binding.nodeId)"
                              :key="field.key"
                              :value="field.key"
                            >
                              {{ field.title }}
                            </option>
                          </select>
                          <button
                            @click="removeConfigBinding(key as string, bIndex as number)"
                            class="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <X class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <div v-else class="text-xs text-gray-400 dark:text-gray-500 italic">
                        暂无关联，配置值不会同步到任何节点
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 空状态 -->
                <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Settings class="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p class="text-sm">暂无配置项</p>
                  <p class="text-xs mt-1">点击上方「添加配置项」按钮来创建</p>
                </div>
              </div>
            </div>

            <!-- 底部按钮 -->
            <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <button
                @click="showWorkflowSettings = false"
                class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                @click="saveWorkflowSettings"
                :disabled="savingSettings"
                class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors disabled:opacity-50"
              >
                <Save class="w-4 h-4" />
                {{ savingSettings ? '保存中...' : '保存设置' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 触发器选择弹窗（新建工作流时显示） -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showTriggerSelector"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        >
          <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <!-- 头部 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                  <Zap class="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">选择触发器类型</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">选择工作流的启动方式</p>
                </div>
              </div>
              <button
                @click="goBack"
                class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                title="取消并返回"
              >
                <X class="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <!-- 触发器列表 -->
            <div class="flex-1 overflow-y-auto p-6">
              <div class="grid grid-cols-2 gap-4">
                <button
                  v-for="trigger in triggerTypes"
                  :key="trigger.code"
                  @click="selectedTriggerType = trigger"
                  :class="[
                    'flex items-start gap-3 p-4 rounded-xl border-2 text-left transition-all hover:shadow-md',
                    selectedTriggerType?.code === trigger.code
                      ? 'border-primary bg-primary/5 shadow-md'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  ]"
                >
                  <div
                    class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                    :style="{ backgroundColor: (trigger.color || '#10b981') + '20' }"
                  >
                    <component
                      :is="getIconComponent(trigger.icon)"
                      class="w-5 h-5"
                      :style="{ color: trigger.color || '#10b981' }"
                    />
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ trigger.name }}</h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                      {{ trigger.description || '暂无描述' }}
                    </p>
                  </div>
                  <div
                    v-if="selectedTriggerType?.code === trigger.code"
                    class="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0"
                  >
                    <Check class="w-3 h-3 text-white" />
                  </div>
                </button>
              </div>

              <!-- 空状态 -->
              <div v-if="triggerTypes.length === 0" class="text-center py-12">
                <div class="animate-spin w-8 h-8 border-3 border-primary border-t-transparent rounded-full mx-auto"></div>
                <p class="text-sm text-gray-500 mt-3">加载触发器类型...</p>
              </div>
            </div>

            <!-- 底部按钮 -->
            <div class="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <button
                @click="goBack"
                class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                @click="confirmTriggerSelection"
                :disabled="!selectedTriggerType"
                class="flex items-center gap-2 px-5 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Check class="w-4 h-4" />
                确认选择
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 版本历史面板 -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showVersionHistory"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          @click.self="showVersionHistory = false"
        >
          <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
            <!-- 头部 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <History class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white">版本历史</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    {{ previewingVersion ? `正在预览 v${previewingVersion.version}` : '查看和恢复历史版本' }}
                  </p>
                </div>
              </div>
              <button
                @click="showVersionHistory = false; previewingVersion = null"
                class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X class="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <!-- 预览模式提示 -->
            <div v-if="previewingVersion" class="px-6 py-3 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                  <Eye class="w-4 h-4" />
                  <span class="text-sm font-medium">预览模式</span>
                  <span class="text-xs text-amber-600 dark:text-amber-500">- 画布显示的是 v{{ previewingVersion.version }} 的内容</span>
                </div>
                <button
                  @click="exitPreview"
                  class="text-xs px-2 py-1 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded transition-colors"
                >
                  退出预览
                </button>
              </div>
            </div>

            <!-- 版本列表 -->
            <div class="flex-1 overflow-y-auto p-4">
              <!-- 加载状态 -->
              <div v-if="loadingVersions" class="flex items-center justify-center py-12">
                <div class="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full"></div>
              </div>

              <!-- 版本列表 -->
              <div v-else-if="versions.length > 0" class="space-y-2">
                <div
                  v-for="version in versions"
                  :key="version.version"
                  :class="[
                    'p-4 rounded-lg border-2 transition-all',
                    previewingVersion?.version === version.version
                      ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/10'
                      : version.version === workflow.version
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  ]"
                >
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <div class="flex items-center gap-2">
                        <span class="font-semibold text-gray-900 dark:text-white">v{{ version.version }}</span>
                        <span v-if="version.version === workflow.version" class="px-2 py-0.5 text-xs bg-primary/20 text-primary rounded-full">
                          当前版本
                        </span>
                        <span v-if="previewingVersion?.version === version.version" class="px-2 py-0.5 text-xs bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 rounded-full">
                          预览中
                        </span>
                      </div>
                      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {{ formatTime(version.created_at) }}
                      </p>
                      <p v-if="version.change_summary" class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {{ version.change_summary }}
                      </p>
                      <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                        <span>{{ version.nodes_count || 0 }} 个节点</span>
                        <span>{{ version.edges_count || 0 }} 条连接</span>
                      </div>
                    </div>
                    <div class="flex items-center gap-1">
                      <!-- 预览按钮 -->
                      <button
                        v-if="version.version !== workflow.version"
                        @click="previewVersion(version)"
                        class="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                        title="预览此版本"
                      >
                        <Eye class="w-4 h-4" />
                      </button>
                      <!-- 恢复按钮 -->
                      <button
                        v-if="version.version !== workflow.version"
                        @click="restoreToVersion(version)"
                        :disabled="restoringVersion"
                        class="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors disabled:opacity-50"
                        title="恢复到此版本"
                      >
                        <RotateCcw class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-else class="text-center py-12 text-gray-500 dark:text-gray-400">
                <History class="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p class="text-sm">暂无版本历史</p>
                <p class="text-xs mt-1">保存工作流后会自动创建版本记录</p>
              </div>
            </div>

            <!-- 底部 -->
            <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
              <button
                v-if="previewingVersion"
                @click="exitPreview"
                class="px-4 py-2 text-sm text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors"
              >
                退出预览
              </button>
              <button
                @click="showVersionHistory = false; if (previewingVersion) exitPreview()"
                class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>