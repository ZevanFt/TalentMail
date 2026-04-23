<script setup lang="ts">
import { AlertTriangle, Info, Trash2 } from 'lucide-vue-next'

const { visible, options, handleConfirm, handleCancel } = useConfirmDialog()

const iconComponent = computed(() => {
  switch (options.value?.type) {
    case 'danger': return Trash2
    case 'warning': return AlertTriangle
    default: return Info
  }
})

const iconColors = computed(() => {
  switch (options.value?.type) {
    case 'danger': return {
      bg: 'bg-red-100 dark:bg-red-900/30',
      icon: 'text-red-500',
    }
    case 'warning': return {
      bg: 'bg-amber-100 dark:bg-amber-900/30',
      icon: 'text-amber-500',
    }
    default: return {
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      icon: 'text-blue-500',
    }
  }
})

const confirmBtnClass = computed(() => {
  switch (options.value?.type) {
    case 'danger':
      return 'bg-red-500 hover:bg-red-600 text-white'
    case 'warning':
      return 'bg-amber-500 hover:bg-amber-600 text-white'
    default:
      return 'bg-primary hover:bg-primary-hover text-white'
  }
})
</script>

<template>
  <CommonModal
    :model-value="visible"
    :title="options?.title || '确认'"
    width-class="w-full max-w-sm"
    :before-close="() => { handleCancel(); return false }"
    @update:model-value="(v: boolean) => { if (!v) handleCancel() }"
  >
    <div class="flex items-start gap-3 py-2">
      <div
        class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
        :class="iconColors.bg"
      >
        <component :is="iconComponent" class="w-5 h-5" :class="iconColors.icon" />
      </div>
      <p class="text-gray-700 dark:text-gray-300 text-sm leading-relaxed pt-2">
        {{ options?.message }}
      </p>
    </div>
    <template #footer>
      <button
        @click="handleCancel"
        class="px-5 py-2.5 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200
               hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 font-medium"
      >
        {{ options?.cancelText || '取消' }}
      </button>
      <button
        @click="handleConfirm"
        class="px-5 py-2.5 rounded-xl transition-all duration-200 font-semibold"
        :class="confirmBtnClass"
      >
        {{ options?.confirmText || '确定' }}
      </button>
    </template>
  </CommonModal>
</template>
