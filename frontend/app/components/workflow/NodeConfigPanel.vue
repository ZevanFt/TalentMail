<script setup lang="ts">
import { X, Trash2, Package } from 'lucide-vue-next'
import type { Component } from 'vue'

const props = defineProps<{
  selectedNode: any
  configSchema: any
  emailTemplates: any[]
  iconComponents: Record<string, Component>
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'delete'): void
}>()

const getIconComponent = (iconName: string): Component => {
  return props.iconComponents[iconName] ?? Package
}
</script>

<template>
  <div class="w-80 bg-white dark:bg-bg-panelDark border-l border-gray-200 dark:border-border-dark flex flex-col shrink-0">
    <!-- 标题 -->
    <div class="h-14 flex items-center justify-between px-4 border-b border-gray-100 dark:border-gray-800">
      <div class="flex items-center gap-2">
        <component :is="getIconComponent(selectedNode.data.icon)" class="w-5 h-5" :style="{ color: selectedNode.data.color }" />
        <span class="font-bold text-gray-900 dark:text-white text-sm">{{ selectedNode.data.label }}</span>
      </div>
      <button @click="emit('close')" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
        <X class="w-5 h-5 text-gray-500" />
      </button>
    </div>

    <!-- 配置表单 -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- 节点名称 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">节点名称</label>
        <input
          v-model="selectedNode.data.label"
          class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
        />
      </div>

      <!-- 节点类型信息 -->
      <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <p class="text-xs text-gray-500 dark:text-gray-400">节点类型</p>
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ selectedNode.data.nodeSubtype }}</p>
      </div>

      <!-- 动态配置项 -->
      <template v-if="configSchema?.properties">
        <div v-for="(prop, key) in configSchema.properties" :key="key" class="space-y-1">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {{ prop.title || key }}
            <span v-if="configSchema.required?.includes(key)" class="text-red-500">*</span>
          </label>
          <p v-if="prop.description" class="text-xs text-gray-500 dark:text-gray-400">{{ prop.description }}</p>

          <!-- 邮件模板选择 -->
          <select
            v-if="key === 'template_code'"
            v-model="selectedNode.data.config[key]"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          >
            <option value="">请选择邮件模板</option>
            <option v-for="template in emailTemplates" :key="template.code" :value="template.code">
              {{ template.name }} ({{ template.code }})
            </option>
          </select>

          <!-- 布尔类型 -->
          <CommonToggle v-else-if="prop.type === 'boolean'" v-model="selectedNode.data.config[key]" />

          <!-- 数字类型 -->
          <input
            v-else-if="prop.type === 'integer' || prop.type === 'number'"
            v-model.number="selectedNode.data.config[key]"
            type="number"
            :min="prop.minimum"
            :max="prop.maximum"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          />

          <!-- 枚举类型 -->
          <select
            v-else-if="prop.enum"
            v-model="selectedNode.data.config[key]"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          >
            <option v-for="(opt, idx) in prop.enum" :key="opt" :value="opt">
              {{ prop.enumNames?.[idx] || opt }}
            </option>
          </select>

          <!-- 多行文本 -->
          <textarea
            v-else-if="prop.format === 'html' || prop.format === 'textarea'"
            v-model="selectedNode.data.config[key]"
            rows="4"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          />

          <!-- 普通文本 -->
          <input
            v-else
            v-model="selectedNode.data.config[key]"
            type="text"
            class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
          />
        </div>
      </template>

      <!-- 无配置项 -->
      <div v-else class="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
        此节点无需配置
      </div>
    </div>

    <!-- 删除按钮 -->
    <div class="p-4 border-t border-gray-100 dark:border-gray-800">
      <button
        @click="emit('delete')"
        class="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-600 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
      >
        <Trash2 class="w-4 h-4" />
        删除节点
      </button>
    </div>
  </div>
</template>
