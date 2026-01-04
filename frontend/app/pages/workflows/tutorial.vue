<script setup lang="ts">
import { 
  BookOpen, 
  Play, 
  MousePointer, 
  Link, 
  Settings, 
  Save, 
  Send,
  Workflow,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Sparkles,
  Mail,
  Tag,
  Forward,
  Reply,
  Trash2,
  Clock,
  Filter,
  Zap,
  Home,
  X
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()

// 展开/折叠状态
const expandedSections = ref<Record<string, boolean>>({
  basics: true,
  create: true,
  nodes: false,
  examples: false,
  tips: false
})

const toggleSection = (key: string) => {
  expandedSections.value[key] = !expandedSections.value[key]
}

// 展开全部/折叠全部
const expandAll = () => {
  Object.keys(expandedSections.value).forEach(key => {
    expandedSections.value[key] = true
  })
}

const collapseAll = () => {
  Object.keys(expandedSections.value).forEach(key => {
    expandedSections.value[key] = false
  })
}

// 跳转到创建工作流
const goToCreateWorkflow = () => {
  router.push('/workflows/new')
}

// 跳转到我的工作流
const goToMyWorkflows = () => {
  router.push('/settings?tab=my-workflows')
}

// 返回首页
const goHome = () => {
  router.push('/')
}

// 返回上一页（使用浏览器历史记录）
const goBack = () => {
  // 如果有来源参数，使用来源参数
  const from = route.query.from as string
  if (from) {
    router.push(from)
    return
  }
  
  // 否则使用浏览器历史记录返回
  if (window.history.length > 1) {
    router.back()
  } else {
    // 如果没有历史记录，返回我的工作流页面
    router.push('/settings?tab=my-workflows')
  }
}

// 节点类型分类说明
const nodeCategories = [
  {
    name: '触发器',
    icon: '🎯',
    color: '#10b981',
    description: '工作流的起点，定义何时开始执行',
    nodes: [
      { name: '邮件接收触发', desc: '当收到新邮件时触发' },
      { name: '邮件发送触发', desc: '当发送邮件时触发' },
      { name: '定时触发', desc: '按设定的时间周期触发' },
      { name: '手动触发', desc: '手动点击按钮触发' },
      { name: '事件触发', desc: '当特定系统事件发生时触发' }
    ]
  },
  {
    name: '逻辑控制',
    icon: '🔀',
    color: '#8b5cf6',
    description: '控制工作流的执行路径',
    nodes: [
      { name: '条件判断', desc: '根据条件选择不同分支' },
      { name: '分支', desc: '将流程分成多个并行分支' },
      { name: '合并', desc: '合并多个分支的执行结果' },
      { name: '循环', desc: '重复执行某些操作' },
      { name: '延迟', desc: '等待一段时间后继续' }
    ]
  },
  {
    name: '邮件动作',
    icon: '📧',
    color: '#3b82f6',
    description: '发送或处理邮件',
    nodes: [
      { name: '发送邮件', desc: '发送新邮件' },
      { name: '回复邮件', desc: '回复触发的邮件' },
      { name: '转发邮件', desc: '转发邮件给其他收件人' },
      { name: '自动回复', desc: '自动发送预设回复' },
      { name: '抄送/密送', desc: '添加抄送或密送收件人' }
    ]
  },
  {
    name: '邮件处理',
    icon: '📋',
    color: '#06b6d4',
    description: '对邮件进行操作',
    nodes: [
      { name: '添加标签', desc: '给邮件添加标签' },
      { name: '移动到文件夹', desc: '将邮件移动到指定文件夹' },
      { name: '标记已读/未读', desc: '更改邮件的阅读状态' },
      { name: '标记星标', desc: '给邮件添加星标' },
      { name: '删除邮件', desc: '将邮件移到垃圾箱' }
    ]
  },
  {
    name: '数据处理',
    icon: '💾',
    color: '#f59e0b',
    description: '处理和转换数据',
    nodes: [
      { name: '设置变量', desc: '定义或修改变量值' },
      { name: '提取数据', desc: '从邮件中提取特定信息' },
      { name: '格式转换', desc: '转换数据格式' },
      { name: '正则匹配', desc: '使用正则表达式匹配内容' },
      { name: '模板渲染', desc: '使用模板生成内容' }
    ]
  },
  {
    name: '外部集成',
    icon: '🔗',
    color: '#ec4899',
    description: '与外部服务交互',
    nodes: [
      { name: 'Webhook', desc: '调用外部 API' },
      { name: '发送通知', desc: '发送推送通知' },
      { name: '数据库操作', desc: '读写数据库记录' },
      { name: '文件操作', desc: '保存或读取文件' }
    ]
  },
  {
    name: '结束节点',
    icon: '🏁',
    color: '#6b7280',
    description: '工作流的终点',
    nodes: [
      { name: '结束', desc: '正常结束工作流' },
      { name: '成功结束', desc: '标记为成功完成' },
      { name: '失败结束', desc: '标记为执行失败' }
    ]
  }
]

// 使用示例
const examples = [
  {
    title: '自动标记重要邮件',
    icon: Tag,
    color: 'amber',
    description: '当收到来自老板或重要客户的邮件时，自动添加"重要"标签并标记星标',
    steps: [
      '添加"邮件接收触发"节点',
      '添加"条件判断"节点，设置条件：发件人包含"boss@company.com"',
      '添加"添加标签"节点，标签设为"重要"',
      '添加"标记星标"节点',
      '连接节点并保存'
    ]
  },
  {
    title: '自动转发客户询盘',
    icon: Forward,
    color: 'blue',
    description: '将来自客服邮箱的客户询盘自动转发给销售团队',
    steps: [
      '添加"邮件接收触发"节点',
      '添加"条件判断"节点，设置条件：收件人为"support@company.com"',
      '添加"转发邮件"节点，设置收件人为"sales@company.com"',
      '添加"添加标签"节点，标签设为"已转发"',
      '连接节点并发布'
    ]
  },
  {
    title: '自动回复休假通知',
    icon: Reply,
    color: 'green',
    description: '在休假期间自动回复所有邮件，告知发件人您不在办公室',
    steps: [
      '添加"邮件接收触发"节点',
      '添加"自动回复"节点',
      '设置回复内容："感谢您的邮件，我目前正在休假中..."',
      '设置回复频率（避免重复回复同一发件人）',
      '连接节点并在休假前发布'
    ]
  },
  {
    title: '垃圾邮件自动清理',
    icon: Trash2,
    color: 'red',
    description: '将包含特定关键词的垃圾邮件自动移到垃圾箱',
    steps: [
      '添加"邮件接收触发"节点',
      '添加"条件判断"节点，设置多个条件：主题包含"促销"/"广告"等',
      '添加"移动到文件夹"节点，目标文件夹设为"垃圾箱"',
      '添加"标记已读"节点',
      '连接节点并发布'
    ]
  }
]

// 默认颜色
const defaultColorClass = { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-800' }

// 获取颜色类
const getColorClasses = (color: string): { bg: string; text: string; border: string } => {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800' },
    blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-800' },
    green: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-400', border: 'border-green-200 dark:border-green-800' },
    red: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-400', border: 'border-red-200 dark:border-red-800' }
  }
  const result = colors[color]
  if (result) return result
  return defaultColorClass
}

// 全屏布局
definePageMeta({ layout: false })
</script>

<template>
  <div class="h-screen overflow-y-auto bg-gray-50 dark:bg-bg-dark">
    <!-- 顶部导航栏 -->
    <header class="sticky top-0 z-40 bg-white dark:bg-bg-panelDark border-b border-gray-200 dark:border-border-dark">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <!-- 左侧 -->
        <div class="flex items-center gap-4">
          <button
            @click="goBack"
            class="flex items-center justify-center w-10 h-10 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
            title="返回"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <BookOpen class="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 class="font-bold text-gray-900 dark:text-white">工作流使用教程</h1>
              <p class="text-xs text-gray-500 dark:text-gray-400">学习如何创建自动化工作流</p>
            </div>
          </div>
        </div>

        <!-- 右侧 -->
        <div class="flex items-center gap-3">
          <button
            @click="expandAll"
            class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            展开全部
          </button>
          <button
            @click="collapseAll"
            class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            折叠全部
          </button>
          <button
            @click="goToCreateWorkflow"
            class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
          >
            <Sparkles class="w-4 h-4" />
            创建工作流
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="max-w-6xl mx-auto px-6 py-8">
      <div class="space-y-6">
        
        <!-- 快速入门卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-900/20 rounded-2xl p-6 border border-green-200 dark:border-green-800">
            <div class="w-14 h-14 rounded-2xl bg-green-500 flex items-center justify-center mb-4 shadow-lg shadow-green-500/20">
              <MousePointer class="w-7 h-7 text-white" />
            </div>
            <h3 class="font-bold text-lg text-green-900 dark:text-green-200 mb-2">拖拽式操作</h3>
            <p class="text-sm text-green-700 dark:text-green-400">从左侧面板拖拽节点到画布，无需编写代码，轻松上手</p>
          </div>
          
          <div class="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800">
            <div class="w-14 h-14 rounded-2xl bg-blue-500 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
              <Link class="w-7 h-7 text-white" />
            </div>
            <h3 class="font-bold text-lg text-blue-900 dark:text-blue-200 mb-2">连接节点</h3>
            <p class="text-sm text-blue-700 dark:text-blue-400">用线条连接节点，定义执行顺序和逻辑分支</p>
          </div>
          
          <div class="bg-gradient-to-br from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/20 rounded-2xl p-6 border border-purple-200 dark:border-purple-800">
            <div class="w-14 h-14 rounded-2xl bg-purple-500 flex items-center justify-center mb-4 shadow-lg shadow-purple-500/20">
              <Play class="w-7 h-7 text-white" />
            </div>
            <h3 class="font-bold text-lg text-purple-900 dark:text-purple-200 mb-2">自动执行</h3>
            <p class="text-sm text-purple-700 dark:text-purple-400">发布后工作流会在满足条件时自动运行</p>
          </div>
        </div>

        <!-- 可折叠教程部分 -->
        <div class="space-y-4">
          
          <!-- 基础概念 -->
          <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark overflow-hidden shadow-sm">
            <button
              @click="toggleSection('basics')"
              class="w-full flex items-center justify-between p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <Lightbulb class="w-6 h-6 text-amber-600 dark:text-amber-400" />
                </div>
                <div class="text-left">
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">1. 什么是工作流？</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">了解工作流的基本概念</p>
                </div>
              </div>
              <ChevronDown 
                :class="['w-6 h-6 text-gray-400 transition-transform duration-300', expandedSections.basics ? 'rotate-180' : '']" 
              />
            </button>
            
            <Transition name="expand">
              <div v-if="expandedSections.basics" class="px-6 pb-6 space-y-4">
                <div class="prose dark:prose-invert max-w-none">
                  <p class="text-gray-600 dark:text-gray-400 text-lg leading-relaxed">
                    <strong>工作流</strong>是一种自动化规则，它定义了"当某个事件发生时，系统应该自动执行什么操作"。
                    通过工作流，您可以让邮件系统自动完成重复性工作，节省时间和精力。
                  </p>
                  
                  <div class="mt-6 p-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-800/30 rounded-xl">
                    <h4 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      🔄 工作流的三要素
                    </h4>
                    <div class="grid md:grid-cols-3 gap-4">
                      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-3">
                          <span class="text-lg font-bold text-green-600">1</span>
                        </div>
                        <h5 class="font-bold text-gray-900 dark:text-white mb-1">触发器</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">定义工作流何时启动</p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">例：收到新邮件</p>
                      </div>
                      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-3">
                          <span class="text-lg font-bold text-blue-600">2</span>
                        </div>
                        <h5 class="font-bold text-gray-900 dark:text-white mb-1">条件</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">判断是否满足执行条件</p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">例：发件人是老板</p>
                      </div>
                      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-3">
                          <span class="text-lg font-bold text-purple-600">3</span>
                        </div>
                        <h5 class="font-bold text-gray-900 dark:text-white mb-1">动作</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">满足条件后执行的操作</p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">例：添加标签</p>
                      </div>
                    </div>
                  </div>
                  
                  <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
                    <p class="text-blue-700 dark:text-blue-400">
                      💡 <strong>举个例子：</strong>当收到来自 boss@company.com 的邮件时，自动添加"重要"标签并标记星标。
                      这个流程包含：触发器（收到邮件）→ 条件（发件人是老板）→ 动作（加标签 + 加星标）
                    </p>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 创建工作流步骤 -->
          <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark overflow-hidden shadow-sm">
            <button
              @click="toggleSection('create')"
              class="w-full flex items-center justify-between p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                  <Workflow class="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div class="text-left">
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">2. 如何创建工作流？</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">6 步轻松创建你的第一个工作流</p>
                </div>
              </div>
              <ChevronDown 
                :class="['w-6 h-6 text-gray-400 transition-transform duration-300', expandedSections.create ? 'rotate-180' : '']" 
              />
            </button>
            
            <Transition name="expand">
              <div v-if="expandedSections.create" class="px-6 pb-6">
                <div class="space-y-8">
                  <!-- 步骤 1 -->
                  <div class="flex gap-6">
                    <div class="flex flex-col items-center">
                      <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center shrink-0">
                        <span class="font-bold text-white text-lg">1</span>
                      </div>
                      <div class="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-4"></div>
                    </div>
                    <div class="flex-1 pb-8">
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">进入工作流编辑器</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        点击「设置」→「我的工作流」→「新建工作流」按钮进入编辑器界面
                      </p>
                      <div class="bg-gray-100 dark:bg-gray-800 rounded-xl p-5">
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">编辑器分为三个区域：</p>
                        <div class="grid md:grid-cols-3 gap-3 text-sm">
                          <div class="bg-white dark:bg-gray-700 rounded-lg p-3">
                            <span class="font-medium text-gray-900 dark:text-white">📋 左侧面板</span>
                            <p class="text-gray-500 dark:text-gray-400 text-xs mt-1">包含所有可用节点类型</p>
                          </div>
                          <div class="bg-white dark:bg-gray-700 rounded-lg p-3">
                            <span class="font-medium text-gray-900 dark:text-white">🎨 中间画布</span>
                            <p class="text-gray-500 dark:text-gray-400 text-xs mt-1">用于设计工作流</p>
                          </div>
                          <div class="bg-white dark:bg-gray-700 rounded-lg p-3">
                            <span class="font-medium text-gray-900 dark:text-white">⚙️ 右侧配置</span>
                            <p class="text-gray-500 dark:text-gray-400 text-xs mt-1">设置节点参数</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 步骤 2 -->
                  <div class="flex gap-6">
                    <div class="flex flex-col items-center">
                      <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center shrink-0">
                        <span class="font-bold text-white text-lg">2</span>
                      </div>
                      <div class="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-4"></div>
                    </div>
                    <div class="flex-1 pb-8">
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">添加触发器节点</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        从左侧面板「触发器」分类中，<strong class="text-primary">拖拽</strong>一个触发器节点到画布上。每个工作流必须有一个触发器作为起点。
                      </p>
                      <div class="flex flex-wrap gap-2">
                        <span class="inline-flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm rounded-lg">
                          📨 邮件接收触发
                        </span>
                        <span class="inline-flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm rounded-lg">
                          ⏰ 定时触发
                        </span>
                        <span class="inline-flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm rounded-lg">
                          👆 手动触发
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- 步骤 3 -->
                  <div class="flex gap-6">
                    <div class="flex flex-col items-center">
                      <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center shrink-0">
                        <span class="font-bold text-white text-lg">3</span>
                      </div>
                      <div class="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-4"></div>
                    </div>
                    <div class="flex-1 pb-8">
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">添加条件和动作节点</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        继续拖拽需要的节点到画布上。通常的流程是：<span class="font-medium text-primary">触发器 → 条件判断 → 动作执行</span>
                      </p>
                      <div class="grid grid-cols-4 gap-3">
                        <div class="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">🔀</span>
                          <span class="text-sm text-purple-700 dark:text-purple-400 font-medium">条件判断</span>
                        </div>
                        <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">🏷️</span>
                          <span class="text-sm text-blue-700 dark:text-blue-400 font-medium">添加标签</span>
                        </div>
                        <div class="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">📁</span>
                          <span class="text-sm text-cyan-700 dark:text-cyan-400 font-medium">移动文件夹</span>
                        </div>
                        <div class="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">↗️</span>
                          <span class="text-sm text-orange-700 dark:text-orange-400 font-medium">转发邮件</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 步骤 4 -->
                  <div class="flex gap-6">
                    <div class="flex flex-col items-center">
                      <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center shrink-0">
                        <span class="font-bold text-white text-lg">4</span>
                      </div>
                      <div class="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-4"></div>
                    </div>
                    <div class="flex-1 pb-8">
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">连接节点</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        将鼠标移动到节点的边缘，会出现连接点。<strong class="text-primary">从一个节点的输出点拖动到另一个节点的输入点</strong>即可创建连接。
                      </p>
                      <div class="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
                        <p class="text-amber-700 dark:text-amber-400 flex items-start gap-2">
                          <span class="text-lg">⚠️</span>
                          <span>注意：连接的箭头方向代表执行顺序，从触发器开始依次执行到结束节点</span>
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- 步骤 5 -->
                  <div class="flex gap-6">
                    <div class="flex flex-col items-center">
                      <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center shrink-0">
                        <span class="font-bold text-white text-lg">5</span>
                      </div>
                      <div class="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-4"></div>
                    </div>
                    <div class="flex-1 pb-8">
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">配置节点参数</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        点击节点，右侧会显示配置面板。根据节点类型设置相应的参数，如条件规则、邮件内容等。
                      </p>
                      <div class="bg-gray-100 dark:bg-gray-800 rounded-xl p-5">
                        <p class="text-sm text-gray-700 dark:text-gray-300 mb-3">
                          <strong>例如「条件判断」节点的配置：</strong>
                        </p>
                        <div class="space-y-2 text-sm">
                          <div class="flex items-center gap-3 bg-white dark:bg-gray-700 rounded-lg px-4 py-2">
                            <span class="text-gray-500 w-20">字段：</span>
                            <span class="font-medium text-gray-900 dark:text-white">发件人地址</span>
                          </div>
                          <div class="flex items-center gap-3 bg-white dark:bg-gray-700 rounded-lg px-4 py-2">
                            <span class="text-gray-500 w-20">操作符：</span>
                            <span class="font-medium text-gray-900 dark:text-white">包含</span>
                          </div>
                          <div class="flex items-center gap-3 bg-white dark:bg-gray-700 rounded-lg px-4 py-2">
                            <span class="text-gray-500 w-20">值：</span>
                            <span class="font-medium text-gray-900 dark:text-white">boss@company.com</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 步骤 6 -->
                  <div class="flex gap-6">
                    <div class="flex flex-col items-center">
                      <div class="w-12 h-12 rounded-full bg-primary flex items-center justify-center shrink-0">
                        <span class="font-bold text-white text-lg">6</span>
                      </div>
                    </div>
                    <div class="flex-1">
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">保存并发布</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        完成设计后，点击「保存」按钮保存工作流。确认无误后，点击「发布」使工作流生效。
                      </p>
                      <div class="flex gap-4">
                        <div class="inline-flex items-center gap-2 px-5 py-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl">
                          <Save class="w-5 h-5" />
                          <span class="font-medium">保存草稿</span>
                        </div>
                        <div class="inline-flex items-center gap-2 px-5 py-3 bg-primary text-white rounded-xl">
                          <Send class="w-5 h-5" />
                          <span class="font-medium">发布上线</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 节点类型介绍 -->
          <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark overflow-hidden shadow-sm">
            <button
              @click="toggleSection('nodes')"
              class="w-full flex items-center justify-between p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <Zap class="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div class="text-left">
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">3. 节点类型详解</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">了解每种节点的功能和用途</p>
                </div>
              </div>
              <ChevronDown 
                :class="['w-6 h-6 text-gray-400 transition-transform duration-300', expandedSections.nodes ? 'rotate-180' : '']" 
              />
            </button>
            
            <Transition name="expand">
              <div v-if="expandedSections.nodes" class="px-6 pb-6">
                <div class="grid md:grid-cols-2 gap-4">
                  <div
                    v-for="category in nodeCategories"
                    :key="category.name"
                    class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden"
                  >
                    <div 
                      class="flex items-center gap-3 px-5 py-4"
                      :style="{ backgroundColor: category.color + '15' }"
                    >
                      <span class="text-3xl">{{ category.icon }}</span>
                      <div>
                        <h4 class="font-bold text-gray-900 dark:text-white">{{ category.name }}</h4>
                        <p class="text-xs text-gray-500 dark:text-gray-400">{{ category.description }}</p>
                      </div>
                    </div>
                    <div class="p-4 bg-white dark:bg-gray-800/50 space-y-2">
                      <div
                        v-for="node in category.nodes"
                        :key="node.name"
                        class="flex items-start gap-3 p-2"
                      >
                        <CheckCircle class="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                        <div>
                          <span class="font-medium text-gray-700 dark:text-gray-300 text-sm">{{ node.name }}</span>
                          <p class="text-xs text-gray-500 dark:text-gray-400">{{ node.desc }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 实用示例 -->
          <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark overflow-hidden shadow-sm">
            <button
              @click="toggleSection('examples')"
              class="w-full flex items-center justify-between p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <Sparkles class="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div class="text-left">
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">4. 实用示例</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">常见场景的工作流配置方案</p>
                </div>
              </div>
              <ChevronDown 
                :class="['w-6 h-6 text-gray-400 transition-transform duration-300', expandedSections.examples ? 'rotate-180' : '']" 
              />
            </button>
            
            <Transition name="expand">
              <div v-if="expandedSections.examples" class="px-6 pb-6">
                <div class="grid md:grid-cols-2 gap-4">
                  <div
                    v-for="example in examples"
                    :key="example.title"
                    :class="['border rounded-xl p-5', getColorClasses(example.color).border, getColorClasses(example.color).bg]"
                  >
                    <div class="flex items-start gap-4 mb-4">
                      <div :class="['w-12 h-12 rounded-xl flex items-center justify-center shrink-0', example.color === 'amber' ? 'bg-amber-200 dark:bg-amber-800' : example.color === 'blue' ? 'bg-blue-200 dark:bg-blue-800' : example.color === 'green' ? 'bg-green-200 dark:bg-green-800' : 'bg-red-200 dark:bg-red-800']">
                        <component :is="example.icon" :class="['w-6 h-6', getColorClasses(example.color).text]" />
                      </div>
                      <div>
                        <h4 :class="['font-bold text-lg', example.color === 'amber' ? 'text-amber-900 dark:text-amber-200' : example.color === 'blue' ? 'text-blue-900 dark:text-blue-200' : example.color === 'green' ? 'text-green-900 dark:text-green-200' : 'text-red-900 dark:text-red-200']">
                          {{ example.title }}
                        </h4>
                        <p :class="['text-sm', getColorClasses(example.color).text]">{{ example.description }}</p>
                      </div>
                    </div>
                    <div class="space-y-2 pl-4 border-l-2" :class="example.color === 'amber' ? 'border-amber-300 dark:border-amber-700' : example.color === 'blue' ? 'border-blue-300 dark:border-blue-700' : example.color === 'green' ? 'border-green-300 dark:border-green-700' : 'border-red-300 dark:border-red-700'">
                      <div
                        v-for="(step, index) in example.steps"
                        :key="index"
                        class="flex items-start gap-3"
                      >
                        <span :class="['w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0', example.color === 'amber' ? 'bg-amber-200 dark:bg-amber-800 text-amber-700 dark:text-amber-300' : example.color === 'blue' ? 'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300' : example.color === 'green' ? 'bg-green-200 dark:bg-green-800 text-green-700 dark:text-green-300' : 'bg-red-200 dark:bg-red-800 text-red-700 dark:text-red-300']">
                          {{ index + 1 }}
                        </span>
                        <span :class="['text-sm', getColorClasses(example.color).text]">{{ step }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 使用技巧 -->
          <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark overflow-hidden shadow-sm">
            <button
              @click="toggleSection('tips')"
              class="w-full flex items-center justify-between p-6 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                  <Lightbulb class="w-6 h-6 text-orange-600 dark:text-orange-400" />
                </div>
                <div class="text-left">
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">5. 使用技巧</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">让工作流更高效的小窍门</p>
                </div>
              </div>
              <ChevronDown 
                :class="['w-6 h-6 text-gray-400 transition-transform duration-300', expandedSections.tips ? 'rotate-180' : '']" 
              />
            </button>
            
            <Transition name="expand">
              <div v-if="expandedSections.tips" class="px-6 pb-6">
                <div class="grid md:grid-cols-2 gap-4">
                  <div class="flex items-start gap-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
                    <div class="w-10 h-10 rounded-full bg-green-200 dark:bg-green-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-green-800 dark:text-green-300 mb-1">先保存再发布</h5>
                      <p class="text-sm text-green-700 dark:text-green-400">在发布之前先保存工作流，确保所有配置都已保存</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
                    <div class="w-10 h-10 rounded-full bg-blue-200 dark:bg-blue-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-blue-800 dark:text-blue-300 mb-1">使用条件分支</h5>
                      <p class="text-sm text-blue-700 dark:text-blue-400">条件判断节点可以创建多个分支，实现复杂的逻辑判断</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
                    <div class="w-10 h-10 rounded-full bg-purple-200 dark:bg-purple-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-purple-800 dark:text-purple-300 mb-1">添加延迟节点</h5>
                      <p class="text-sm text-purple-700 dark:text-purple-400">在某些动作前添加延迟，避免操作过于频繁</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
                    <div class="w-10 h-10 rounded-full bg-amber-200 dark:bg-amber-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-amber-800 dark:text-amber-300 mb-1">测试后再发布</h5>
                      <p class="text-sm text-amber-700 dark:text-amber-400">使用"手动触发"类型先测试工作流逻辑是否正确</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-xl border border-cyan-200 dark:border-cyan-800">
                    <div class="w-10 h-10 rounded-full bg-cyan-200 dark:bg-cyan-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-cyan-800 dark:text-cyan-300 mb-1">合理命名节点</h5>
                      <p class="text-sm text-cyan-700 dark:text-cyan-400">给节点起一个有意义的名字，方便后期维护</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-rose-50 dark:bg-rose-900/20 rounded-xl border border-rose-200 dark:border-rose-800">
                    <div class="w-10 h-10 rounded-full bg-rose-200 dark:bg-rose-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-rose-600 dark:text-rose-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-rose-800 dark:text-rose-300 mb-1">查看执行记录</h5>
                      <p class="text-sm text-rose-700 dark:text-rose-400">在工作流列表中可以查看执行日志，便于排查问题</p>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>

        <!-- 底部行动按钮 -->
        <div class="flex flex-col md:flex-row gap-6 p-8 bg-gradient-to-r from-primary/10 via-purple-500/10 to-pink-500/10 dark:from-primary/20 dark:via-purple-500/20 dark:to-pink-500/20 rounded-2xl border border-primary/20 dark:border-primary/30">
          <div class="flex-1">
            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">🎉 准备好开始了吗？</h3>
            <p class="text-gray-600 dark:text-gray-400">创建你的第一个自动化工作流，让邮件处理更智能高效！</p>
          </div>
          <div class="flex items-center gap-4">
            <button
              @click="goToMyWorkflows"
              class="flex items-center gap-2 px-5 py-3 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-xl transition-colors"
            >
              <Workflow class="w-5 h-5" />
              查看我的工作流
            </button>
            <button
              @click="goToCreateWorkflow"
              class="flex items-center gap-2 px-6 py-3 text-white bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 rounded-xl transition-colors shadow-lg shadow-primary/25"
            >
              <Sparkles class="w-5 h-5" />
              创建工作流
              <ArrowRight class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 3000px;
}
</style>