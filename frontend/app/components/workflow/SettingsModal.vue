<script setup lang="ts">
import { Settings, X, Plus, Trash2, Link, Save } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps<{
  modelValue: boolean
  workflow: any
  nodes: any[]
  savingSettings: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'save'): void
  (e: 'add-config-item'): void
  (e: 'remove-config-item', key: string): void
  (e: 'add-config-binding', key: string): void
  (e: 'remove-config-binding', key: string, index: number): void
  (e: 'get-node-config-fields', nodeId: string): { key: string; title: string }[]
}>()

// 获取节点配置字段 — 通过 inject 或 prop 函数
const getNodeConfigFields = inject<(nodeId: string) => { key: string; title: string }[]>('getNodeConfigFields', () => [])
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="emit('update:modelValue', false)"
      >
        <div class="bg-white dark:bg-bg-panelDark rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <!-- 头部 -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Settings class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('workflows.settingsModal.title') }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ t('workflows.settingsModal.subtitle') }}</p>
              </div>
            </div>
            <button @click="emit('update:modelValue', false)" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              <X class="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <!-- 内容 -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- 基础信息 -->
            <div class="space-y-4">
              <h4 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span class="w-1 h-4 bg-primary rounded-full"></span>
                {{ t('workflows.settingsModal.basicInfo') }}
              </h4>
              <div class="grid gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('workflows.settingsModal.nameLabel') }}</label>
                  <input v-model="workflow.name" type="text" class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('workflows.settingsModal.descLabel') }}</label>
                  <textarea v-model="workflow.description" rows="3" class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
                </div>
              </div>
            </div>

            <!-- 全局配置项 -->
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h4 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <span class="w-1 h-4 bg-primary rounded-full"></span>
                  {{ t('workflows.settingsModal.globalConfig') }}
                </h4>
                <button @click="emit('add-config-item')" class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary hover:bg-primary/10 rounded-lg whitespace-nowrap transition-colors">
                  <Plus class="w-4 h-4" />
                  {{ t('workflows.settingsModal.addConfigItem') }}
                </button>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ t('workflows.settingsModal.configHint') }}
              </p>

              <!-- 已有配置项 -->
              <div v-if="workflow.config_schema?.properties && Object.keys(workflow.config_schema.properties).length > 0" class="space-y-4">
                <div
                  v-for="(prop, key) in workflow.config_schema.properties"
                  :key="key"
                  class="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg space-y-4"
                >
                  <!-- 基本信息 -->
                  <div class="flex items-start gap-4">
                    <div class="flex-1 grid grid-cols-2 gap-4">
                      <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('workflows.settingsModal.configName') }}</label>
                        <input v-model="prop.title" type="text" :placeholder="t('workflows.settingsModal.namePlaceholder')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
                      </div>
                      <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('workflows.settingsModal.typeLabel') }}</label>
                        <select v-model="prop.type" class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
                          <option value="boolean">{{ t('workflows.settingsModal.typeBoolean') }}</option>
                          <option value="string">{{ t('workflows.settingsModal.typeString') }}</option>
                          <option value="integer">{{ t('workflows.settingsModal.typeNumber') }}</option>
                        </select>
                      </div>
                      <div class="col-span-2">
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('workflows.settingsModal.descLabel') }}</label>
                        <input v-model="prop.description" type="text" :placeholder="t('workflows.settingsModal.descPlaceholder')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
                      </div>
                      <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('workflows.settingsModal.defaultValue') }}</label>
                        <template v-if="prop.type === 'boolean'">
                          <select v-model="workflow.default_config[key]" class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
                            <option :value="true">{{ t('workflows.settingsModal.on') }}</option>
                            <option :value="false">{{ t('workflows.settingsModal.off') }}</option>
                          </select>
                        </template>
                        <template v-else-if="prop.type === 'integer'">
                          <input v-model.number="workflow.default_config[key]" type="number" class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
                        </template>
                        <template v-else>
                          <input v-model="workflow.default_config[key]" type="text" class="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white" />
                        </template>
                      </div>
                    </div>
                    <button @click="emit('remove-config-item', key as string)" class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" :title="t('workflows.settingsModal.removeItemTitle')">
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>

                  <!-- 节点绑定 -->
                  <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <div class="flex items-center justify-between mb-2">
                      <label class="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                        <Link class="w-3.5 h-3.5" />
                        {{ t('workflows.settingsModal.bindingLabel') }}
                      </label>
                      <button @click="emit('add-config-binding', key as string)" class="text-xs text-primary hover:text-primary/80 flex items-center gap-1">
                        <Plus class="w-3 h-3" />
                        {{ t('workflows.settingsModal.addBinding') }}
                      </button>
                    </div>
                    <p class="text-xs text-gray-400 dark:text-gray-500 mb-2">
                      {{ t('workflows.settingsModal.bindingHint') }}
                    </p>

                    <div v-if="prop.bindings && prop.bindings.length > 0" class="space-y-2">
                      <div
                        v-for="(binding, bIndex) in prop.bindings"
                        :key="bIndex"
                        class="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <select v-model="binding.nodeId" class="flex-1 px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                          <option value="">{{ t('workflows.settingsModal.selectNode') }}</option>
                          <option v-for="node in nodes" :key="node.id" :value="node.id">{{ node.data?.label || node.id }}</option>
                        </select>
                        <span class="text-gray-400 text-xs">&rarr;</span>
                        <select v-model="binding.field" :disabled="!binding.nodeId" class="flex-1 px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50">
                          <option value="">{{ t('workflows.settingsModal.selectField') }}</option>
                          <option v-for="field in getNodeConfigFields(binding.nodeId)" :key="field.key" :value="field.key">{{ field.title }}</option>
                        </select>
                        <button @click="emit('remove-config-binding', key as string, bIndex as number)" class="p-1 text-gray-400 hover:text-red-500 transition-colors">
                          <X class="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div v-else class="text-xs text-gray-400 dark:text-gray-500 italic">
                      {{ t('workflows.settingsModal.noBindings') }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
                <Settings class="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p class="text-sm">{{ t('workflows.settingsModal.emptyTitle') }}</p>
                <p class="text-xs mt-1">{{ t('workflows.settingsModal.emptyHint') }}</p>
              </div>
            </div>
          </div>

          <!-- 底部按钮 -->
          <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <button @click="emit('update:modelValue', false)" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              {{ t('workflows.common.cancel') }}
            </button>
            <button @click="emit('save')" :disabled="savingSettings" class="flex items-center gap-2 px-4 py-2 text-sm text-white bg-primary hover:bg-primary/90 rounded-lg whitespace-nowrap transition-colors disabled:opacity-50">
              <Save class="w-4 h-4" />
              {{ savingSettings ? t('workflows.common.saving') : t('workflows.settingsModal.saveSettings') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
