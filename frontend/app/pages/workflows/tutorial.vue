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
const config = useConfig()
const { t } = useI18n()
useHead({ title: computed(() => `${t('workflows.tutorial.pageTitle')} - ${config.appName}`) })

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
const nodeCategories = computed(() => [
  {
    name: t('workflows.catalog.catTrigger'),
    icon: '🎯',
    color: '#10b981',
    description: t('workflows.catalog.catTriggerDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeMailReceive'), desc: t('workflows.catalog.nodeMailReceiveDesc') },
      { name: t('workflows.catalog.nodeMailSend'), desc: t('workflows.catalog.nodeMailSendDesc') },
      { name: t('workflows.catalog.nodeSchedule'), desc: t('workflows.catalog.nodeScheduleDesc') },
      { name: t('workflows.catalog.nodeManual'), desc: t('workflows.catalog.nodeManualDesc') },
      { name: t('workflows.catalog.nodeEvent'), desc: t('workflows.catalog.nodeEventDesc') }
    ]
  },
  {
    name: t('workflows.catalog.catLogic'),
    icon: '🔀',
    color: '#8b5cf6',
    description: t('workflows.catalog.catLogicDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeCondition'), desc: t('workflows.catalog.nodeConditionDesc') },
      { name: t('workflows.catalog.nodeBranch'), desc: t('workflows.catalog.nodeBranchDesc') },
      { name: t('workflows.catalog.nodeMerge'), desc: t('workflows.catalog.nodeMergeDesc') },
      { name: t('workflows.catalog.nodeLoop'), desc: t('workflows.catalog.nodeLoopDesc') },
      { name: t('workflows.catalog.nodeDelay'), desc: t('workflows.catalog.nodeDelayDesc') }
    ]
  },
  {
    name: t('workflows.catalog.catEmailAction'),
    icon: '📧',
    color: '#3b82f6',
    description: t('workflows.catalog.catEmailActionDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeSendEmail'), desc: t('workflows.catalog.nodeSendEmailDesc') },
      { name: t('workflows.catalog.nodeReply'), desc: t('workflows.catalog.nodeReplyDesc') },
      { name: t('workflows.catalog.nodeForward'), desc: t('workflows.catalog.nodeForwardDesc') },
      { name: t('workflows.catalog.nodeAutoReply'), desc: t('workflows.catalog.nodeAutoReplyDesc') },
      { name: t('workflows.catalog.nodeCcBcc'), desc: t('workflows.catalog.nodeCcBccDesc') }
    ]
  },
  {
    name: t('workflows.catalog.catEmailOperation'),
    icon: '📋',
    color: '#06b6d4',
    description: t('workflows.catalog.catEmailOperationDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeAddTag'), desc: t('workflows.catalog.nodeAddTagDesc') },
      { name: t('workflows.catalog.nodeMoveFolder'), desc: t('workflows.catalog.nodeMoveFolderDesc') },
      { name: t('workflows.catalog.nodeMarkRead'), desc: t('workflows.catalog.nodeMarkReadDesc') },
      { name: t('workflows.catalog.nodeMarkStar'), desc: t('workflows.catalog.nodeMarkStarDesc') },
      { name: t('workflows.catalog.nodeDeleteMail'), desc: t('workflows.catalog.nodeDeleteMailDesc') }
    ]
  },
  {
    name: t('workflows.catalog.catData'),
    icon: '💾',
    color: '#f59e0b',
    description: t('workflows.catalog.catDataDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeSetVar'), desc: t('workflows.catalog.nodeSetVarDesc') },
      { name: t('workflows.catalog.nodeExtract'), desc: t('workflows.catalog.nodeExtractDesc') },
      { name: t('workflows.catalog.nodeFormat'), desc: t('workflows.catalog.nodeFormatDesc') },
      { name: t('workflows.catalog.nodeRegex'), desc: t('workflows.catalog.nodeRegexDesc') },
      { name: t('workflows.catalog.nodeRender'), desc: t('workflows.catalog.nodeRenderDesc') }
    ]
  },
  {
    name: t('workflows.catalog.catIntegration'),
    icon: '🔗',
    color: '#ec4899',
    description: t('workflows.catalog.catIntegrationDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeWebhook'), desc: t('workflows.catalog.nodeWebhookDesc') },
      { name: t('workflows.catalog.nodeNotify'), desc: t('workflows.catalog.nodeNotifyDesc') },
      { name: t('workflows.catalog.nodeDatabase'), desc: t('workflows.catalog.nodeDatabaseDesc') },
      { name: t('workflows.catalog.nodeFile'), desc: t('workflows.catalog.nodeFileDesc') }
    ]
  },
  {
    name: t('workflows.catalog.catEnd'),
    icon: '🏁',
    color: '#6b7280',
    description: t('workflows.catalog.catEndDesc'),
    nodes: [
      { name: t('workflows.catalog.nodeEnd'), desc: t('workflows.catalog.nodeEndDesc') },
      { name: t('workflows.catalog.nodeEndSuccess'), desc: t('workflows.catalog.nodeEndSuccessDesc') },
      { name: t('workflows.catalog.nodeEndFail'), desc: t('workflows.catalog.nodeEndFailDesc') }
    ]
  }
])

// 使用示例
const examples = computed(() => [
  {
    title: t('workflows.catalog.exMark.title'),
    icon: Tag,
    color: 'amber',
    description: t('workflows.catalog.exMark.desc'),
    steps: [
      t('workflows.catalog.exAddTrigger'),
      t('workflows.catalog.exMark.s2'),
      t('workflows.catalog.exMark.s3'),
      t('workflows.catalog.exMark.s4'),
      t('workflows.catalog.exConnectSave')
    ]
  },
  {
    title: t('workflows.catalog.exForward.title'),
    icon: Forward,
    color: 'blue',
    description: t('workflows.catalog.exForward.desc'),
    steps: [
      t('workflows.catalog.exAddTrigger'),
      t('workflows.catalog.exForward.s2'),
      t('workflows.catalog.exForward.s3'),
      t('workflows.catalog.exForward.s4'),
      t('workflows.catalog.exConnectPublish')
    ]
  },
  {
    title: t('workflows.catalog.exVacation.title'),
    icon: Reply,
    color: 'green',
    description: t('workflows.catalog.exVacation.desc'),
    steps: [
      t('workflows.catalog.exAddTrigger'),
      t('workflows.catalog.exVacation.s2'),
      t('workflows.catalog.exVacation.s3'),
      t('workflows.catalog.exVacation.s4'),
      t('workflows.catalog.exConnectPublishVacation')
    ]
  },
  {
    title: t('workflows.catalog.exSpam.title'),
    icon: Trash2,
    color: 'red',
    description: t('workflows.catalog.exSpam.desc'),
    steps: [
      t('workflows.catalog.exAddTrigger'),
      t('workflows.catalog.exSpam.s2'),
      t('workflows.catalog.exSpam.s3'),
      t('workflows.catalog.exSpam.s4'),
      t('workflows.catalog.exConnectPublish')
    ]
  }
])

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
            :title="t('workflows.common.back')"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <BookOpen class="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 class="font-bold text-gray-900 dark:text-white">{{ t('workflows.common.tutorialTitle') }}</h1>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.subtitle') }}</p>
            </div>
          </div>
        </div>

        <!-- 右侧 -->
        <div class="flex items-center gap-3">
          <button
            @click="expandAll"
            class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            {{ t('workflows.tutorial.expandAll') }}
          </button>
          <button
            @click="collapseAll"
            class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            {{ t('workflows.tutorial.collapseAll') }}
          </button>
          <button
            @click="goToCreateWorkflow"
            class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg whitespace-nowrap transition-colors"
          >
            <Sparkles class="w-4 h-4" />
            {{ t('workflows.common.createWorkflow') }}
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
            <h3 class="font-bold text-lg text-green-900 dark:text-green-200 mb-2">{{ t('workflows.common.dragOperation') }}</h3>
            <p class="text-sm text-green-700 dark:text-green-400">{{ t('workflows.tutorial.cardDragDesc') }}</p>
          </div>
          
          <div class="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800">
            <div class="w-14 h-14 rounded-2xl bg-blue-500 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
              <Link class="w-7 h-7 text-white" />
            </div>
            <h3 class="font-bold text-lg text-blue-900 dark:text-blue-200 mb-2">{{ t('workflows.common.connectNodes') }}</h3>
            <p class="text-sm text-blue-700 dark:text-blue-400">{{ t('workflows.tutorial.cardConnectDesc') }}</p>
          </div>
          
          <div class="bg-gradient-to-br from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/20 rounded-2xl p-6 border border-purple-200 dark:border-purple-800">
            <div class="w-14 h-14 rounded-2xl bg-purple-500 flex items-center justify-center mb-4 shadow-lg shadow-purple-500/20">
              <Play class="w-7 h-7 text-white" />
            </div>
            <h3 class="font-bold text-lg text-purple-900 dark:text-purple-200 mb-2">{{ t('workflows.common.autoExecute') }}</h3>
            <p class="text-sm text-purple-700 dark:text-purple-400">{{ t('workflows.common.cardAutoDesc') }}</p>
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
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.basicsTitle') }}</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tut.basicsSubtitle') }}</p>
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
                    <strong>{{ t('workflows.tut.introLead') }}</strong>{{ t('workflows.tut.introSentence1') }}
                    {{ t('workflows.tutorial.introSentence2') }}
                  </p>
                  
                  <div class="mt-6 p-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800/50 dark:to-gray-800/30 rounded-xl">
                    <h4 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      🔄 {{ t('workflows.tutorial.elementsTitle') }}
                    </h4>
                    <div class="grid md:grid-cols-3 gap-4">
                      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-3">
                          <span class="text-lg font-bold text-green-600">1</span>
                        </div>
                        <h5 class="font-bold text-gray-900 dark:text-white mb-1">{{ t('workflows.tut.elem1Title') }}</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.elem1Desc') }}</p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">{{ t('workflows.tutorial.elem1Example') }}</p>
                      </div>
                      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-3">
                          <span class="text-lg font-bold text-blue-600">2</span>
                        </div>
                        <h5 class="font-bold text-gray-900 dark:text-white mb-1">{{ t('workflows.tut.elem2Title') }}</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.elem2Desc') }}</p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">{{ t('workflows.tutorial.elem2Example') }}</p>
                      </div>
                      <div class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-3">
                          <span class="text-lg font-bold text-purple-600">3</span>
                        </div>
                        <h5 class="font-bold text-gray-900 dark:text-white mb-1">{{ t('workflows.tut.elem3Title') }}</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.elem3Desc') }}</p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-2">{{ t('workflows.tutorial.elem3Example') }}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
                    <p class="text-blue-700 dark:text-blue-400">
                      💡 <strong>{{ t('workflows.tut.exampleLabel') }}</strong>{{ t('workflows.tut.exampleSentence') }}
                      {{ t('workflows.tutorial.exampleFlow') }}
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
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.createTitle') }}</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.createSubtitle') }}</p>
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
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">{{ t('workflows.tut.step1Title') }}</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        {{ t('workflows.tut.step1Desc') }}
                      </p>
                      <div class="bg-gray-100 dark:bg-gray-800 rounded-xl p-5">
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">{{ t('workflows.tut.editorAreasTitle') }}</p>
                        <div class="grid md:grid-cols-3 gap-3 text-sm">
                          <div class="bg-white dark:bg-gray-700 rounded-lg p-3">
                            <span class="font-medium text-gray-900 dark:text-white">📋 {{ t('workflows.tutorial.areaLeftTitle') }}</span>
                            <p class="text-gray-500 dark:text-gray-400 text-xs mt-1">{{ t('workflows.tutorial.areaLeftDesc') }}</p>
                          </div>
                          <div class="bg-white dark:bg-gray-700 rounded-lg p-3">
                            <span class="font-medium text-gray-900 dark:text-white">🎨 {{ t('workflows.tutorial.areaCenterTitle') }}</span>
                            <p class="text-gray-500 dark:text-gray-400 text-xs mt-1">{{ t('workflows.tutorial.areaCenterDesc') }}</p>
                          </div>
                          <div class="bg-white dark:bg-gray-700 rounded-lg p-3">
                            <span class="font-medium text-gray-900 dark:text-white">⚙️ {{ t('workflows.tutorial.areaRightTitle') }}</span>
                            <p class="text-gray-500 dark:text-gray-400 text-xs mt-1">{{ t('workflows.tutorial.areaRightDesc') }}</p>
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
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">{{ t('workflows.tut.step2Title') }}</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        {{ t('workflows.tut.step2Desc1') }}<strong class="text-primary">{{ t('workflows.tut.step2Drag') }}</strong>{{ t('workflows.tut.step2Desc2') }}
                      </p>
                      <div class="flex flex-wrap gap-2">
                        <span class="inline-flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm rounded-lg whitespace-nowrap">
                          📨 {{ t('workflows.catalog.nodeMailReceive') }}
                        </span>
                        <span class="inline-flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm rounded-lg whitespace-nowrap">
                          ⏰ {{ t('workflows.catalog.nodeSchedule') }}
                        </span>
                        <span class="inline-flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm rounded-lg whitespace-nowrap">
                          👆 {{ t('workflows.catalog.nodeManual') }}
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
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">{{ t('workflows.tut.step3Title') }}</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        {{ t('workflows.tut.step3Desc1') }}<span class="font-medium text-primary">{{ t('workflows.tut.step3Flow') }}</span>
                      </p>
                      <div class="grid grid-cols-4 gap-3">
                        <div class="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">🔀</span>
                          <span class="text-sm text-purple-700 dark:text-purple-400 font-medium">{{ t('workflows.catalog.nodeCondition') }}</span>
                        </div>
                        <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">🏷️</span>
                          <span class="text-sm text-blue-700 dark:text-blue-400 font-medium">{{ t('workflows.catalog.nodeAddTag') }}</span>
                        </div>
                        <div class="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">📁</span>
                          <span class="text-sm text-cyan-700 dark:text-cyan-400 font-medium">{{ t('workflows.tutorial.chipMoveFolder') }}</span>
                        </div>
                        <div class="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl text-center">
                          <span class="block text-2xl mb-2">↗️</span>
                          <span class="text-sm text-orange-700 dark:text-orange-400 font-medium">{{ t('workflows.catalog.nodeForward') }}</span>
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
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">{{ t('workflows.tut.step4Title') }}</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        {{ t('workflows.tut.step4Desc1') }}<strong class="text-primary">{{ t('workflows.tut.step4DragText') }}</strong>{{ t('workflows.tut.step4Desc2') }}
                      </p>
                      <div class="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
                        <p class="text-amber-700 dark:text-amber-400 flex items-start gap-2">
                          <span class="text-lg">⚠️</span>
                          <span>{{ t('workflows.tutorial.step4Note') }}</span>
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
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">{{ t('workflows.tut.step5Title') }}</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        {{ t('workflows.tut.step5Desc') }}
                      </p>
                      <div class="bg-gray-100 dark:bg-gray-800 rounded-xl p-5">
                        <p class="text-sm text-gray-700 dark:text-gray-300 mb-3">
                          <strong>{{ t('workflows.tutorial.step5ExampleTitle') }}</strong>
                        </p>
                        <div class="space-y-2 text-sm">
                          <div class="flex items-center gap-3 bg-white dark:bg-gray-700 rounded-lg px-4 py-2">
                            <span class="text-gray-500 w-20">{{ t('workflows.tut.fieldLabel') }}</span>
                            <span class="font-medium text-gray-900 dark:text-white">{{ t('workflows.tut.fieldSender') }}</span>
                          </div>
                          <div class="flex items-center gap-3 bg-white dark:bg-gray-700 rounded-lg px-4 py-2">
                            <span class="text-gray-500 w-20">{{ t('workflows.tut.opLabel') }}</span>
                            <span class="font-medium text-gray-900 dark:text-white">{{ t('workflows.tut.opContains') }}</span>
                          </div>
                          <div class="flex items-center gap-3 bg-white dark:bg-gray-700 rounded-lg px-4 py-2">
                            <span class="text-gray-500 w-20">{{ t('workflows.tut.valueLabel') }}</span>
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
                      <h4 class="font-bold text-xl text-gray-900 dark:text-white mb-3">{{ t('workflows.tut.step6Title') }}</h4>
                      <p class="text-gray-600 dark:text-gray-400 mb-4">
                        {{ t('workflows.tut.step6Desc') }}
                      </p>
                      <div class="flex gap-4">
                        <div class="inline-flex items-center gap-2 px-5 py-3 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl">
                          <Save class="w-5 h-5" />
                          <span class="font-medium">{{ t('workflows.common.saveDraft') }}</span>
                        </div>
                        <div class="inline-flex items-center gap-2 px-5 py-3 bg-primary text-white rounded-xl">
                          <Send class="w-5 h-5" />
                          <span class="font-medium">{{ t('workflows.common.publishOnline') }}</span>
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
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.nodesTitle') }}</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.nodesSubtitle') }}</p>
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
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.examplesTitle') }}</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tutorial.examplesSubtitle') }}</p>
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
                  <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.tipsTitle') }}</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tut.tipsSubtitle') }}</p>
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
                      <h5 class="font-bold text-green-800 dark:text-green-300 mb-1">{{ t('workflows.tut.tipSaveFirstTitle') }}</h5>
                      <p class="text-sm text-green-700 dark:text-green-400">{{ t('workflows.tut.tipSaveFirstDesc') }}</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
                    <div class="w-10 h-10 rounded-full bg-blue-200 dark:bg-blue-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-blue-800 dark:text-blue-300 mb-1">{{ t('workflows.tut.tipBranchesTitle') }}</h5>
                      <p class="text-sm text-blue-700 dark:text-blue-400">{{ t('workflows.tut.tipBranchesDesc') }}</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
                    <div class="w-10 h-10 rounded-full bg-purple-200 dark:bg-purple-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-purple-800 dark:text-purple-300 mb-1">{{ t('workflows.tut.tipDelayTitle') }}</h5>
                      <p class="text-sm text-purple-700 dark:text-purple-400">{{ t('workflows.tutorial.tipDelayDesc') }}</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
                    <div class="w-10 h-10 rounded-full bg-amber-200 dark:bg-amber-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-amber-800 dark:text-amber-300 mb-1">{{ t('workflows.tut.tipTestTitle') }}</h5>
                      <p class="text-sm text-amber-700 dark:text-amber-400">{{ t('workflows.tut.tipTestDesc') }}</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-xl border border-cyan-200 dark:border-cyan-800">
                    <div class="w-10 h-10 rounded-full bg-cyan-200 dark:bg-cyan-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-cyan-800 dark:text-cyan-300 mb-1">{{ t('workflows.tut.tipNameTitle') }}</h5>
                      <p class="text-sm text-cyan-700 dark:text-cyan-400">{{ t('workflows.tutorial.tipNameDesc') }}</p>
                    </div>
                  </div>
                  
                  <div class="flex items-start gap-4 p-4 bg-rose-50 dark:bg-rose-900/20 rounded-xl border border-rose-200 dark:border-rose-800">
                    <div class="w-10 h-10 rounded-full bg-rose-200 dark:bg-rose-800 flex items-center justify-center shrink-0">
                      <CheckCircle class="w-5 h-5 text-rose-600 dark:text-rose-400" />
                    </div>
                    <div>
                      <h5 class="font-bold text-rose-800 dark:text-rose-300 mb-1">{{ t('workflows.tut.tipHistoryTitle') }}</h5>
                      <p class="text-sm text-rose-700 dark:text-rose-400">{{ t('workflows.tutorial.tipHistoryDesc') }}</p>
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
            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">🎉 {{ t('workflows.tut.readyTitle') }}</h3>
            <p class="text-gray-600 dark:text-gray-400">{{ t('workflows.tutorial.readyDesc') }}</p>
          </div>
          <div class="flex items-center gap-4">
            <button
              @click="goToMyWorkflows"
              class="flex items-center gap-2 px-5 py-3 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-xl transition-colors"
            >
              <Workflow class="w-5 h-5" />
              {{ t('workflows.common.viewMyWorkflows') }}
            </button>
            <button
              @click="goToCreateWorkflow"
              class="flex items-center gap-2 px-6 py-3 text-white bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 rounded-xl transition-colors shadow-lg shadow-primary/25"
            >
              <Sparkles class="w-5 h-5" />
              {{ t('workflows.common.createWorkflow') }}
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