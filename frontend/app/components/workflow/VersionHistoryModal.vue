<script setup lang="ts">
import { History, X, Eye, RotateCcw } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps<{
  modelValue: boolean
  versions: any[]
  currentVersion: number
  previewingVersion: any
  loadingVersions: boolean
  restoringVersion: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'preview', version: any): void
  (e: 'exit-preview'): void
  (e: 'restore', version: any): void
}>()

const formatTime = (dateStr: string | null) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const handleClose = () => {
  if (props.previewingVersion) emit('exit-preview')
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="emit('update:modelValue', false)"
      >
        <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
          <!-- 头部 -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <History class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('workflows.common.versionHistory') }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ previewingVersion ? t('workflows.versionHistory.previewing', { v: previewingVersion.version }) : t('workflows.versionHistory.subtitle') }}
                </p>
              </div>
            </div>
            <button @click="handleClose" :aria-label="t('workflows.common.close')" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              <X class="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <!-- 预览模式提示 -->
          <div v-if="previewingVersion" class="px-6 py-3 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                <Eye class="w-4 h-4" />
                <span class="text-sm font-medium">{{ t('workflows.versionHistory.previewMode') }}</span>
                <span class="text-xs text-amber-600 dark:text-amber-500">{{ t('workflows.versionHistory.previewCanvas', { v: previewingVersion.version }) }}</span>
              </div>
              <button @click="emit('exit-preview')" class="text-xs px-2 py-1 text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded transition-colors">
                {{ t('workflows.versionHistory.exitPreview') }}
              </button>
            </div>
          </div>

          <!-- 版本列表 -->
          <div class="flex-1 overflow-y-auto p-4">
            <div v-if="loadingVersions" class="flex items-center justify-center py-12">
              <div class="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full"></div>
            </div>

            <div v-else-if="versions.length > 0" class="space-y-2">
              <div
                v-for="version in versions"
                :key="version.version"
                :class="[
                  'p-4 rounded-lg border-2 transition-all',
                  previewingVersion?.version === version.version
                    ? 'border-amber-400 bg-amber-50 dark:bg-amber-900/10'
                    : version.version === currentVersion
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <span class="font-semibold text-gray-900 dark:text-white">v{{ version.version }}</span>
                      <span v-if="version.version === currentVersion" class="px-2 py-0.5 text-xs bg-primary/20 text-primary rounded-full">{{ t('workflows.versionHistory.currentVersion') }}</span>
                      <span v-if="previewingVersion?.version === version.version" class="px-2 py-0.5 text-xs bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 rounded-full">{{ t('workflows.versionHistory.previewingBadge') }}</span>
                    </div>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ formatTime(version.created_at) }}</p>
                    <p v-if="version.change_summary" class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ version.change_summary }}</p>
                    <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span>{{ t('workflows.common.nodesCount', { n: version.nodes_count || 0 }) }}</span>
                      <span>{{ t('workflows.common.connectionsCount', { n: version.edges_count || 0 }) }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      v-if="version.version !== currentVersion"
                      @click="emit('preview', version)"
                      class="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                      :title="t('workflows.versionHistory.previewTooltip')"
                    >
                      <Eye class="w-4 h-4" />
                    </button>
                    <button
                      v-if="version.version !== currentVersion"
                      @click="emit('restore', version)"
                      :disabled="restoringVersion"
                      class="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors disabled:opacity-50"
                      :title="t('workflows.versionHistory.restoreTooltip')"
                    >
                      <RotateCcw class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-12 text-gray-500 dark:text-gray-400">
              <History class="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p class="text-sm">{{ t('workflows.versionHistory.emptyTitle') }}</p>
              <p class="text-xs mt-1">{{ t('workflows.versionHistory.emptyDesc') }}</p>
            </div>
          </div>

          <!-- 底部 -->
          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <button v-if="previewingVersion" @click="emit('exit-preview')" class="px-4 py-2 text-sm text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors">
              {{ t('workflows.versionHistory.exitPreview') }}
            </button>
            <button @click="handleClose" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              {{ t('workflows.common.close') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
