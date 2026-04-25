<script setup lang="ts">
import { GripVertical, Package } from 'lucide-vue-next'
import type { Component } from 'vue'

const props = defineProps<{
  sortedCategories: string[]
  nodeTypesByCategory: Record<string, any[]>
  categoryLabels: Record<string, { label: string; icon: string }>
  iconComponents: Record<string, Component>
  nodeTypes: any[]
}>()

const emit = defineEmits<{
  (e: 'drag-start', event: DragEvent, nodeType: any): void
}>()

const getIconComponent = (iconName: string): Component => {
  return props.iconComponents[iconName] ?? Package
}
</script>

<template>
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
          @dragstart="(e) => emit('drag-start', e, nodeType)"
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
</template>
