<script setup lang="ts">
import { X, Keyboard } from 'lucide-vue-next'
import { getShortcutsByCategory } from '~/composables/useKeyboardShortcuts'

const { showShortcutsHelp } = useKeyboardShortcuts()

const shortcutsByCategory = getShortcutsByCategory()
const categories = Object.keys(shortcutsByCategory)
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="showShortcutsHelp" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showShortcutsHelp = false"></div>
        
        <!-- 弹窗内容 -->
        <div class="modal-solid-bg relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
          <!-- 头部 -->
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Keyboard class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">键盘快捷键</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">使用快捷键提高效率</p>
              </div>
            </div>
            <button @click="showShortcutsHelp = false" 
              class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <!-- 快捷键列表 -->
          <div class="p-6 overflow-y-auto max-h-[calc(80vh-80px)] custom-scrollbar">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div v-for="category in categories" :key="category">
                <h4 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                  {{ category }}
                </h4>
                <div class="space-y-2">
                  <div v-for="shortcut in shortcutsByCategory[category]" :key="shortcut.key"
                    class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ shortcut.description }}</span>
                    <kbd class="inline-flex items-center justify-center min-w-[28px] h-7 px-2 bg-gray-100 dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-md text-xs font-mono font-medium text-gray-700 dark:text-white shadow-sm">
                      {{ shortcut.label }}
                    </kbd>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 底部提示 -->
          <div class="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
            <p class="text-xs text-gray-500 dark:text-gray-400 text-center">
              按 <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded text-[10px] font-mono mx-1 text-gray-700 dark:text-white">?</kbd> 显示或隐藏此帮助
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>