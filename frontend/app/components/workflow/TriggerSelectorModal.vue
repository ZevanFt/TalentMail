<script setup lang="ts">
import { Zap, X, Check, Package } from 'lucide-vue-next'
import type { Component } from 'vue'

const props = defineProps<{
  modelValue: boolean
  triggerTypes: any[]
  iconComponents: Record<string, Component>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'select', trigger: any): void
  (e: 'cancel'): void
}>()

const selectedTriggerType = ref<any>(null)

const getIconComponent = (iconName: string): Component => {
  return props.iconComponents[iconName] ?? Package
}

const handleConfirm = () => {
  if (selectedTriggerType.value) {
    emit('select', selectedTriggerType.value)
  }
}

// Reset selection when modal opens
watch(() => props.modelValue, (val) => {
  if (val) selectedTriggerType.value = null
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
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
            <button @click="emit('cancel')" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="取消并返回">
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
                <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" :style="{ backgroundColor: (trigger.color || '#10b981') + '20' }">
                  <component :is="getIconComponent(trigger.icon)" class="w-5 h-5" :style="{ color: trigger.color || '#10b981' }" />
                </div>
                <div class="flex-1 min-w-0">
                  <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ trigger.name }}</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{{ trigger.description || '暂无描述' }}</p>
                </div>
                <div v-if="selectedTriggerType?.code === trigger.code" class="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
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
            <button @click="emit('cancel')" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              取消
            </button>
            <button
              @click="handleConfirm"
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
</template>
