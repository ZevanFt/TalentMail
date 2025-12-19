<script setup lang="ts">
import { X } from 'lucide-vue-next'

const props = defineProps<{
  title?: string
  modelValue: boolean
  widthClass?: string // 允许自定义宽度，比如写信是大窗，生成是小窗
  beforeClose?: () => boolean | void // 返回 false 阻止关闭
}>()

const emit = defineEmits(['update:modelValue'])

// 处理关闭逻辑
const handleClose = () => {
  console.log('Modal handleClose called')
  console.log('beforeClose prop:', props.beforeClose)
  console.log('beforeClose type:', typeof props.beforeClose)
  
  if (props.beforeClose) {
    console.log('Calling beforeClose...')
    const result = props.beforeClose()
    console.log('beforeClose returned:', result)
    if (result === false) {
      console.log('Close prevented by beforeClose')
      return
    }
  }
  console.log('Emitting update:modelValue false')
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <!-- 遮罩层 -->
      <div v-if="modelValue" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="handleClose">
        
        <!-- 弹窗主体 -->
        <div 
          class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl flex flex-col max-h-[90vh] transition-all transform scale-100"
          :class="widthClass || 'w-full max-w-lg'"
        >
          <!-- 头部 -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ title }}</h3>
            <button @click="handleClose" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- 内容 -->
          <div class="p-6 overflow-y-auto custom-scrollbar">
            <slot />
          </div>

          <!-- 底部 (可选) -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-b-xl flex justify-end gap-3">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>