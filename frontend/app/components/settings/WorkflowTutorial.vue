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
  Zap
} from 'lucide-vue-next'

const router = useRouter()

// 展开/折叠状态
const expandedSections = ref<Record<string, boolean>>({
  basics: true,
  create: false,
  nodes: false,
  examples: false,
  tips: false
})

const toggleSection = (key: string) => {
  expandedSections.value[key] = !expandedSections.value[key]
}

// 跳转到创建工作流
const goToCreateWorkflow = () => {
  router.push('/workflows/new')
}

// 跳转到我的工作流
const goToMyWorkflows = () => {
  router.push('/settings?tab=my-workflows')
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
</script>

<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <BookOpen class="w-7 h-7 text-primary" />
          工作流使用教程
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          学习如何创建和使用自动化工作流，让邮件处理更智能高效
        </p>
      </div>
      <button
        @click="goToCreateWorkflow"
        class="flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
      >
        <Sparkles class="w-4 h-4" />
        立即创建工作流
      </button>
    </div>

    <!-- 快速入门卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-5 border border-green-200 dark:border-green-800">
        <div class="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center mb-3">
          <MousePointer class="w-6 h-6 text-white" />
        </div>
        <h3 class="font-bold text-green-900 dark:text-green-200 mb-1">拖拽式操作</h3>
        <p class="text-sm text-green-700 dark:text-green-400">从左侧面板拖拽节点到画布，无需编写代码</p>
      </div>
      
      <div class="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-5 border border-blue-200 dark:border-blue-800">
        <div class="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center mb-3">
          <Link class="w-6 h-6 text-white" />
        </div>
        <h3 class="font-bold text-blue-900 dark:text-blue-200 mb-1">连接节点</h3>
        <p class="text-sm text-blue-700 dark:text-blue-400">用线条连接节点，定义执行顺序和逻辑</p>
      </div>
      
      <div class="bg-gradient-to-br from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/20 rounded-xl p-5 border border-purple-200 dark:border-purple-800">
        <div class="w-12 h-12 rounded-xl bg-purple-500 flex items-center justify-center mb-3">
          <Play class="w-6 h-6 text-white" />
        </div>
        <h3 class="font-bold text-purple-900 dark:text-purple-200 mb-1">自动执行</h3>
        <p class="text-sm text-purple-700 dark:text-purple-400">发布后工作流会在满足条件时自动运行</p>
      </div>
    </div>

    <!-- 可折叠教程部分 -->
    <div class="space-y-4">
      
      <!-- 基础概念 -->
      <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
        <button
          @click="toggleSection('basics')"
          class="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
              <Lightbulb class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div class="text-left">
              <h3 class="font-bold text-gray-900 dark:text-white">1. 什么是工作流？</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">了解工作流的基本概念</p>
            </div>
          </div>
          <ChevronDown 
            :class="['w-5 h-5 text-gray-400 transition-transform', expandedSections.basics ? 'rotate-180' : '']" 
          />
        </button>
        
        <Transition name="expand">
          <div v-if="expandedSections.basics" class="px-5 pb-5 space-y-4">
            <div class="prose dark:prose-invert max-w-none">
              <p class="text-gray-600 dark:text-gray-400">
                <strong>工作流</strong>是一种自动化规则，它定义了"当某个事件发生时，系统应该自动执行什么操作"。
              </p>
              
              <div class="mt-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <h4 class="font-bold text-gray-900 dark:text-white mb-2">🔄 工作流的组成</h4>
                <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li class="flex items-start gap-2">
                    <span class="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="text-xs font-bold text-green-600">1</span>
                    </span>
                    <span><strong>触发器</strong>：定义工作流何时启动（如：收到新邮件）</span>
                  </li>
                  <li class="flex items-start gap-2">
                    <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="text-xs font-bold text-blue-600">2</span>
                    </span>
                    <span><strong>条件</strong>：判断是否满足执行条件（如：发件人是老板）</span>
                  </li>
                  <li class="flex items-start gap-2">
                    <span class="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="text-xs font-bold text-purple-600">3</span>
                    </span>
                    <span><strong>动作</strong>：满足条件后执行的操作（如：添加标签、转发邮件）</span>
                  </li>
                </ul>
              </div>
              
              <div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <p class="text-sm text-blue-700 dark:text-blue-400">
                  💡 <strong>举个例子：</strong>当收到来自 boss@company.com 的邮件时，自动添加"重要"标签并标记星标。
                </p>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 创建工作流步骤 -->
      <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
        <button
          @click="toggleSection('create')"
          class="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <Workflow class="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div class="text-left">
              <h3 class="font-bold text-gray-900 dark:text-white">2. 如何创建工作流？</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">分步骤图文教程</p>
            </div>
          </div>
          <ChevronDown 
            :class="['w-5 h-5 text-gray-400 transition-transform', expandedSections.create ? 'rotate-180' : '']" 
          />
        </button>
        
        <Transition name="expand">
          <div v-if="expandedSections.create" class="px-5 pb-5">
            <div class="space-y-6">
              <!-- 步骤 1 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">1</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">进入工作流编辑器</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    点击「设置」→「我的工作流」→「新建工作流」按钮进入编辑器界面
                  </p>
                  <div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400">
                    编辑器分为三个区域：<br>
                    • <strong>左侧</strong>：节点面板，包含所有可用节点类型<br>
                    • <strong>中间</strong>：画布区域，用于设计工作流<br>
                    • <strong>右侧</strong>：配置面板，用于设置节点参数
                  </div>
                </div>
              </div>

              <!-- 步骤 2 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">2</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">添加触发器节点</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    从左侧面板「触发器」分类中，<strong>拖拽</strong>一个触发器节点到画布上。每个工作流必须有一个触发器作为起点。
                  </p>
                  <div class="flex flex-wrap gap-2">
                    <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                      📨 邮件接收触发
                    </span>
                    <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                      ⏰ 定时触发
                    </span>
                    <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                      👆 手动触发
                    </span>
                  </div>
                </div>
              </div>

              <!-- 步骤 3 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">3</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">添加条件和动作节点</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    继续拖拽需要的节点到画布上。通常的流程是：触发器 → 条件判断 → 动作执行
                  </p>
                  <div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center">
                      <span class="block text-lg mb-1">🔀</span>
                      <span class="text-purple-700 dark:text-purple-400">条件判断</span>
                    </div>
                    <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
                      <span class="block text-lg mb-1">🏷️</span>
                      <span class="text-blue-700 dark:text-blue-400">添加标签</span>
                    </div>
                    <div class="p-2 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg text-center">
                      <span class="block text-lg mb-1">📁</span>
                      <span class="text-cyan-700 dark:text-cyan-400">移动文件夹</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 步骤 4 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">4</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">连接节点</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    将鼠标移动到节点的边缘，会出现连接点。<strong>从一个节点的输出点拖动到另一个节点的输入点</strong>即可创建连接。
                  </p>
                  <div class="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800 text-sm text-amber-700 dark:text-amber-400">
                    ⚠️ 注意：连接的箭头方向代表执行顺序，从触发器开始依次执行
                  </div>
                </div>
              </div>

              <!-- 步骤 5 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">5</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">配置节点参数</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    点击节点，右侧会显示配置面板。根据节点类型设置相应的参数，如条件规则、邮件内容等。
                  </p>
                  <div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400">
                    <strong>例如「条件判断」节点：</strong><br>
                    • 字段：发件人地址<br>
                    • 操作符：包含<br>
                    • 值：boss@company.com
                  </div>
                </div>
              </div>

              <!-- 步骤 6 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">6</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">保存并发布</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    完成设计后，点击「保存」按钮保存工作流。确认无误后，点击「发布」使工作流生效。
                  </p>
                  <div class="flex gap-3">
                    <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg">
                      <Save class="w-4 h-4" />
                      保存草稿
                    </span>
                    <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-primary text-white text-sm rounded-lg">
                      <Send class="w-4 h-4" />
                      发布上线
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 节点类型介绍 -->
      <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
        <button
          @click="toggleSection('nodes')"
          class="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <Zap class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div class="text-left">
              <h3 class="font-bold text-gray-900 dark:text-white">3. 节点类型详解</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">了解每种节点的功能</p>
            </div>
          </div>
          <ChevronDown 
            :class="['w-5 h-5 text-gray-400 transition-transform', expandedSections.nodes ? 'rotate-180' : '']" 
          />
        </button>
        
        <Transition name="expand">
          <div v-if="expandedSections.nodes" class="px-5 pb-5">
            <div class="grid gap-4">
              <div
                v-for="category in nodeCategories"
                :key="category.name"
                class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
              >
                <div 
                  class="flex items-center gap-3 px-4 py-3"
                  :style="{ backgroundColor: category.color + '15' }"
                >
                  <span class="text-2xl">{{ category.icon }}</span>
                  <div>
                    <h4 class="font-bold text-gray-900 dark:text-white">{{ category.name }}</h4>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ category.description }}</p>
                  </div>
                </div>
                <div class="p-3 bg-white dark:bg-gray-800/50">
                  <div class="grid grid-cols-2 gap-2">
                    <div
                      v-for="node in category.nodes"
                      :key="node.name"
                      class="flex items-start gap-2 p-2 text-sm"
                    >
                      <CheckCircle class="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                      <div>
                        <span class="font-medium text-gray-700 dark:text-gray-300">{{ node.name }}</span>
                        <p class="text-xs text-gray-500 dark:text-gray-400">{{ node.desc }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 实用示例 -->
      <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
        <button
          @click="toggleSection('examples')"
          class="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
              <Sparkles class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div class="text-left">
              <h3 class="font-bold text-gray-900 dark:text-white">4. 实用示例</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">常见场景的工作流配置</p>
            </div>
          </div>
          <ChevronDown 
            :class="['w-5 h-5 text-gray-400 transition-transform', expandedSections.examples ? 'rotate-180' : '']" 
          />
        </button>
        
        <Transition name="expand">
          <div v-if="expandedSections.examples" class="px-5 pb-5">
            <div class="grid gap-4">
              <div
                v-for="example in examples"
                :key="example.title"
                class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              >
                <div class="flex items-start gap-3 mb-3">
                  <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
                    <component :is="example.icon" class="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <h4 class="font-bold text-gray-900 dark:text-white">{{ example.title }}</h4>
                    <p class="text-sm text-gray-500 dark:text-gray-400">{{ example.description }}</p>
                  </div>
                </div>
                <div class="ml-13 space-y-2">
                  <div
                    v-for="(step, index) in example.steps"
                    :key="index"
                    class="flex items-center gap-2 text-sm"
                  >
                    <span class="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                      {{ index + 1 }}
                    </span>
                    <span class="text-gray-600 dark:text-gray-400">{{ step }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 使用技巧 -->
      <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
        <button
          @click="toggleSection('tips')"
          class="w-full flex items-center justify-between p-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
              <Lightbulb class="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div class="text-left">
              <h3 class="font-bold text-gray-900 dark:text-white">5. 使用技巧</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">让工作流更高效的小窍门</p>
            </div>
          </div>
          <ChevronDown 
            :class="['w-5 h-5 text-gray-400 transition-transform', expandedSections.tips ? 'rotate-180' : '']" 
          />
        </button>
        
        <Transition name="expand">
          <div v-if="expandedSections.tips" class="px-5 pb-5">
            <div class="space-y-4">
              <div class="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-green-800 dark:text-green-300">先保存再发布</h5>
                  <p class="text-sm text-green-700 dark:text-green-400">在发布之前先保存工作流，确保所有配置都已保存</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-blue-800 dark:text-blue-300">使用条件分支</h5>
                  <p class="text-sm text-blue-700 dark:text-blue-400">条件判断节点可以创建多个分支，实现复杂的逻辑判断</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-purple-800 dark:text-purple-300">添加延迟节点</h5>
                  <p class="text-sm text-purple-700 dark:text-purple-400">在某些动作前添加延迟，避免操作过于频繁或立即触发</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-amber-800 dark:text-amber-300">测试后再发布</h5>
                  <p class="text-sm text-amber-700 dark:text-amber-400">使用"手动触发"类型先测试工作流逻辑是否正确</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-cyan-800 dark:text-cyan-300">合理命名节点</h5>
                  <p class="text-sm text-cyan-700 dark:text-cyan-400">给节点起一个有意义的名字，方便后期维护和调试</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-rose-50 dark:bg-rose-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-rose-800 dark:text-rose-300">查看执行记录</h5>
                  <p class="text-sm text-rose-700 dark:text-rose-400">在工作流列表中可以查看每次执行的详细日志，便于排查问题</p>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- 底部行动按钮 -->
    <div class="flex flex-col sm:flex-row gap-4 p-6 bg-gradient-to-r from-primary/5 to-purple-500/5 dark:from-primary/10 dark:to-purple-500/10 rounded-xl border border-primary/20 dark:border-primary/30">
      <div class="flex-1">
        <h3 class="font-bold text-gray-900 dark:text-white mb-1">准备好开始了吗？</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">创建你的第一个自动化工作流，让邮件处理更智能！</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="goToMyWorkflows"
          class="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Workflow class="w-4 h-4" />
          查看我的工作流
        </button>
        <button
          @click="goToCreateWorkflow"
          class="flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors"
        >
          <Sparkles class="w-4 h-4" />
          创建工作流
          <ArrowRight class="w-4 h-4" />
        </button>
      </div>
    </div>
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
  max-height: 2000px;
}
</style>