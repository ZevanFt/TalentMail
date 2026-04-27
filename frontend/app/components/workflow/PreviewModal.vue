<script setup lang="ts">
/**
 * 工作流预览弹窗（共享组件）
 * 被 MyWorkflows / SystemWorkflows 复用
 */
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Workflow, Edit, X, RefreshCw } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  modelValue: boolean
  workflow: { name?: string; description?: string; id?: number } | null
  nodes: any[]
  edges: any[]
  loading?: boolean
  showLegend?: boolean
}>(), {
  loading: false,
  showLegend: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'edit'): void
}>()

const close = () => emit('update:modelValue', false)
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="close"
      >
        <div class="modal-solid-bg bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-[90vw] h-[85vh] max-w-6xl flex flex-col overflow-hidden">
          <!-- 头部 -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-border-dark">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Workflow class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  {{ workflow?.name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ workflow?.description || '暂无描述' }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <button
                @click="emit('edit')"
                class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg whitespace-nowrap transition-colors"
              >
                <Edit class="w-4 h-4" />
                编辑
              </button>
              <button
                @click="close"
                aria-label="关闭"
                class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X class="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          <!-- 流程图预览 -->
          <div class="flex-1 relative">
            <!-- 加载状态 -->
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
              <RefreshCw class="w-8 h-8 text-primary animate-spin" />
            </div>

            <!-- 空状态 -->
            <div v-else-if="nodes.length === 0" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
              <Workflow class="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
              <p class="text-gray-500 dark:text-gray-400 mb-4">该工作流暂无节点</p>
              <button
                @click="emit('edit')"
                class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg whitespace-nowrap transition-colors"
              >
                <Edit class="w-4 h-4" />
                开始编辑
              </button>
            </div>

            <!-- VueFlow -->
            <div v-else class="absolute inset-0">
              <ClientOnly>
                <VueFlow
                  :nodes="nodes"
                  :edges="edges"
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

            <!-- 图例（可选） -->
            <div v-if="showLegend && nodes.length > 0" class="absolute bottom-4 left-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
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
            <div v-if="nodes.length > 0" class="absolute bottom-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-4 py-2 shadow-lg">
              <p class="text-sm text-gray-600 dark:text-gray-400">
                <span class="font-medium">{{ nodes.length }}</span> 个节点，
                <span class="font-medium">{{ edges.length }}</span> 条连接
              </p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
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
