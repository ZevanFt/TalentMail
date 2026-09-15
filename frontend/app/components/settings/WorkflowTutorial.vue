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
const { t } = useI18n()

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
</script>

<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <BookOpen class="w-7 h-7 text-primary" />
          {{ t('workflows.common.tutorialTitle') }}
        </h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ t('workflows.settingsTutorial.subtitle') }}
        </p>
      </div>
      <button
        @click="goToCreateWorkflow"
        class="flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg whitespace-nowrap transition-colors"
      >
        <Sparkles class="w-4 h-4" />
        {{ t('workflows.settingsTutorial.createNow') }}
      </button>
    </div>

    <!-- 快速入门卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-5 border border-green-200 dark:border-green-800">
        <div class="w-12 h-12 rounded-xl bg-green-500 flex items-center justify-center mb-3">
          <MousePointer class="w-6 h-6 text-white" />
        </div>
        <h3 class="font-bold text-green-900 dark:text-green-200 mb-1">{{ t('workflows.common.dragOperation') }}</h3>
        <p class="text-sm text-green-700 dark:text-green-400">{{ t('workflows.settingsTutorial.cardDragDesc') }}</p>
      </div>
      
      <div class="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-5 border border-blue-200 dark:border-blue-800">
        <div class="w-12 h-12 rounded-xl bg-blue-500 flex items-center justify-center mb-3">
          <Link class="w-6 h-6 text-white" />
        </div>
        <h3 class="font-bold text-blue-900 dark:text-blue-200 mb-1">{{ t('workflows.common.connectNodes') }}</h3>
        <p class="text-sm text-blue-700 dark:text-blue-400">{{ t('workflows.settingsTutorial.cardConnectDesc') }}</p>
      </div>
      
      <div class="bg-gradient-to-br from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/20 rounded-xl p-5 border border-purple-200 dark:border-purple-800">
        <div class="w-12 h-12 rounded-xl bg-purple-500 flex items-center justify-center mb-3">
          <Play class="w-6 h-6 text-white" />
        </div>
        <h3 class="font-bold text-purple-900 dark:text-purple-200 mb-1">{{ t('workflows.common.autoExecute') }}</h3>
        <p class="text-sm text-purple-700 dark:text-purple-400">{{ t('workflows.common.cardAutoDesc') }}</p>
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
              <h3 class="font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.basicsTitle') }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tut.basicsSubtitle') }}</p>
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
                <strong>{{ t('workflows.tut.introLead') }}</strong>{{ t('workflows.tut.introSentence1') }}
              </p>
              
              <div class="mt-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <h4 class="font-bold text-gray-900 dark:text-white mb-2">🔄 {{ t('workflows.settingsTutorial.elementsTitle') }}</h4>
                <ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li class="flex items-start gap-2">
                    <span class="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="text-xs font-bold text-green-600">1</span>
                    </span>
                    <span><strong>{{ t('workflows.tut.elem1Title') }}</strong>{{ t('workflows.settingsTutorial.triggerLine') }}</span>
                  </li>
                  <li class="flex items-start gap-2">
                    <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="text-xs font-bold text-blue-600">2</span>
                    </span>
                    <span><strong>{{ t('workflows.tut.elem2Title') }}</strong>{{ t('workflows.settingsTutorial.conditionLine') }}</span>
                  </li>
                  <li class="flex items-start gap-2">
                    <span class="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center shrink-0 mt-0.5">
                      <span class="text-xs font-bold text-purple-600">3</span>
                    </span>
                    <span><strong>{{ t('workflows.tut.elem3Title') }}</strong>{{ t('workflows.settingsTutorial.actionLine') }}</span>
                  </li>
                </ul>
              </div>
              
              <div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <p class="text-sm text-blue-700 dark:text-blue-400">
                  💡 <strong>{{ t('workflows.tut.exampleLabel') }}</strong>{{ t('workflows.tut.exampleSentence') }}
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
              <h3 class="font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.createTitle') }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.settingsTutorial.createSubtitle') }}</p>
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
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">{{ t('workflows.tut.step1Title') }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {{ t('workflows.tut.step1Desc') }}
                  </p>
                  <div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400">
                    {{ t('workflows.tut.editorAreasTitle') }}<br>
                    • <strong>{{ t('workflows.tut.sideLeft') }}</strong>{{ t('workflows.settingsTutorial.leftLine') }}<br>
                    • <strong>{{ t('workflows.tut.sideCenter') }}</strong>{{ t('workflows.settingsTutorial.centerLine') }}<br>
                    • <strong>{{ t('workflows.tut.sideRight') }}</strong>{{ t('workflows.settingsTutorial.rightLine') }}
                  </div>
                </div>
              </div>

              <!-- 步骤 2 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">2</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">{{ t('workflows.tut.step2Title') }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {{ t('workflows.tut.step2Desc1') }}<strong>{{ t('workflows.tut.step2Drag') }}</strong>{{ t('workflows.tut.step2Desc2') }}
                  </p>
                  <div class="flex flex-wrap gap-2">
                    <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full whitespace-nowrap">
                      📨 {{ t('workflows.catalog.nodeMailReceive') }}
                    </span>
                    <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full whitespace-nowrap">
                      ⏰ {{ t('workflows.catalog.nodeSchedule') }}
                    </span>
                    <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full whitespace-nowrap">
                      👆 {{ t('workflows.catalog.nodeManual') }}
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
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">{{ t('workflows.tut.step3Title') }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {{ t('workflows.tut.step3Desc1') }}{{ t('workflows.tut.step3Flow') }}
                  </p>
                  <div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center">
                      <span class="block text-lg mb-1">🔀</span>
                      <span class="text-purple-700 dark:text-purple-400">{{ t('workflows.catalog.nodeCondition') }}</span>
                    </div>
                    <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
                      <span class="block text-lg mb-1">🏷️</span>
                      <span class="text-blue-700 dark:text-blue-400">{{ t('workflows.catalog.nodeAddTag') }}</span>
                    </div>
                    <div class="p-2 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg text-center">
                      <span class="block text-lg mb-1">📁</span>
                      <span class="text-cyan-700 dark:text-cyan-400">{{ t('workflows.tutorial.chipMoveFolder') }}</span>
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
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">{{ t('workflows.tut.step4Title') }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {{ t('workflows.tut.step4Desc1') }}<strong>{{ t('workflows.tut.step4DragText') }}</strong>{{ t('workflows.tut.step4Desc2') }}
                  </p>
                  <div class="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800 text-sm text-amber-700 dark:text-amber-400">
                    ⚠️ {{ t('workflows.settingsTutorial.step4Note') }}
                  </div>
                </div>
              </div>

              <!-- 步骤 5 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">5</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">{{ t('workflows.tut.step5Title') }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {{ t('workflows.tut.step5Desc') }}
                  </p>
                  <div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-500 dark:text-gray-400">
                    <strong>{{ t('workflows.settingsTutorial.step5ExampleTitle') }}</strong><br>
                    • {{ t('workflows.tut.fieldLabel') }}{{ t('workflows.tut.fieldSender') }}<br>
                    • {{ t('workflows.tut.opLabel') }}{{ t('workflows.tut.opContains') }}<br>
                    • {{ t('workflows.tut.valueLabel') }}boss@company.com
                  </div>
                </div>
              </div>

              <!-- 步骤 6 -->
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span class="font-bold text-primary">6</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-gray-900 dark:text-white mb-2">{{ t('workflows.tut.step6Title') }}</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {{ t('workflows.tut.step6Desc') }}
                  </p>
                  <div class="flex gap-3">
                    <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg whitespace-nowrap">
                      <Save class="w-4 h-4" />
                      {{ t('workflows.common.saveDraft') }}
                    </span>
                    <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-primary text-white text-sm rounded-lg whitespace-nowrap">
                      <Send class="w-4 h-4" />
                      {{ t('workflows.common.publishOnline') }}
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
              <h3 class="font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.nodesTitle') }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.settingsTutorial.nodesSubtitle') }}</p>
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
              <h3 class="font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.examplesTitle') }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.settingsTutorial.examplesSubtitle') }}</p>
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
              <h3 class="font-bold text-gray-900 dark:text-white">{{ t('workflows.tut.tipsTitle') }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.tut.tipsSubtitle') }}</p>
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
                  <h5 class="font-medium text-green-800 dark:text-green-300">{{ t('workflows.tut.tipSaveFirstTitle') }}</h5>
                  <p class="text-sm text-green-700 dark:text-green-400">{{ t('workflows.tut.tipSaveFirstDesc') }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-blue-800 dark:text-blue-300">{{ t('workflows.tut.tipBranchesTitle') }}</h5>
                  <p class="text-sm text-blue-700 dark:text-blue-400">{{ t('workflows.tut.tipBranchesDesc') }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-purple-800 dark:text-purple-300">{{ t('workflows.tut.tipDelayTitle') }}</h5>
                  <p class="text-sm text-purple-700 dark:text-purple-400">{{ t('workflows.settingsTutorial.tipDelayDesc') }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-amber-800 dark:text-amber-300">{{ t('workflows.tut.tipTestTitle') }}</h5>
                  <p class="text-sm text-amber-700 dark:text-amber-400">{{ t('workflows.tut.tipTestDesc') }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-cyan-800 dark:text-cyan-300">{{ t('workflows.tut.tipNameTitle') }}</h5>
                  <p class="text-sm text-cyan-700 dark:text-cyan-400">{{ t('workflows.settingsTutorial.tipNameDesc') }}</p>
                </div>
              </div>
              
              <div class="flex items-start gap-3 p-3 bg-rose-50 dark:bg-rose-900/20 rounded-lg">
                <CheckCircle class="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <h5 class="font-medium text-rose-800 dark:text-rose-300">{{ t('workflows.tut.tipHistoryTitle') }}</h5>
                  <p class="text-sm text-rose-700 dark:text-rose-400">{{ t('workflows.settingsTutorial.tipHistoryDesc') }}</p>
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
        <h3 class="font-bold text-gray-900 dark:text-white mb-1">{{ t('workflows.tut.readyTitle') }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.settingsTutorial.readyDesc') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="goToMyWorkflows"
          class="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg whitespace-nowrap transition-colors"
        >
          <Workflow class="w-4 h-4" />
          {{ t('workflows.common.viewMyWorkflows') }}
        </button>
        <button
          @click="goToCreateWorkflow"
          class="flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg whitespace-nowrap transition-colors"
        >
          <Sparkles class="w-4 h-4" />
          {{ t('workflows.common.createWorkflow') }}
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