<script setup lang="ts">
import { Plus, Trash2, ChevronDown, ChevronUp, GripVertical } from 'lucide-vue-next'

const props = defineProps<{
  rule: any
  metadata: any
}>()

const emit = defineEmits(['save', 'cancel'])

// 本地编辑状态
const localRule = ref<any>({ ...props.rule })
const conditions = ref<any[]>(props.rule.conditions || [])
const actions = ref<any[]>(props.rule.actions || [])

// 展开状态
const expandedConditions = ref<Set<number>>(new Set())
const expandedActions = ref<Set<number>>(new Set())

// 添加条件
const addCondition = () => {
  conditions.value.push({
    field: 'subject',
    operator: 'contains',
    value: ''
  })
  expandedConditions.value.add(conditions.value.length - 1)
}

// 删除条件
const removeCondition = (index: number) => {
  conditions.value.splice(index, 1)
  expandedConditions.value.delete(index)
}

// 添加动作
const addAction = () => {
  actions.value.push({
    type: 'add_tag',
    config: {}
  })
  expandedActions.value.add(actions.value.length - 1)
}

// 删除动作
const removeAction = (index: number) => {
  actions.value.splice(index, 1)
  expandedActions.value.delete(index)
}

// 切换展开
const toggleCondition = (index: number) => {
  if (expandedConditions.value.has(index)) {
    expandedConditions.value.delete(index)
  } else {
    expandedConditions.value.add(index)
  }
}

const toggleAction = (index: number) => {
  if (expandedActions.value.has(index)) {
    expandedActions.value.delete(index)
  } else {
    expandedActions.value.add(index)
  }
}

// 获取操作符名称
const getOperatorName = (operator: string) => {
  const found = props.metadata.condition_operators?.find((o: any) => o.operator === operator)
  return found?.name || operator
}

// 获取动作类型名称
const getActionTypeName = (type: string) => {
  const found = props.metadata.action_types?.find((a: any) => a.type === type)
  return found?.name || type
}

// 获取字段名称
const getFieldName = (field: string) => {
  const found = props.metadata.available_fields?.find((f: any) => f.field === field)
  return found?.name || field
}

// 检查操作符是否需要值
const operatorRequiresValue = (operator: string) => {
  const found = props.metadata.condition_operators?.find((o: any) => o.operator === operator)
  return found?.requires_value !== false
}

// 获取动作配置 schema
const getActionConfigSchema = (type: string) => {
  const found = props.metadata.action_types?.find((a: any) => a.type === type)
  return found?.config_schema?.properties || {}
}

// 保存
const handleSave = () => {
  const ruleData = {
    ...localRule.value,
    conditions: conditions.value.length > 0 ? conditions.value : null,
    actions: actions.value
  }
  emit('save', ruleData)
}

// 验证
const isValid = computed(() => {
  return localRule.value.name && 
         localRule.value.trigger_type && 
         actions.value.length > 0
})
</script>

<template>
  <div class="space-y-6">
    <!-- 基本信息 -->
    <div class="space-y-4">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white">基本信息</h3>
      
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">规则名称 *</label>
          <input v-model="localRule.name" type="text" 
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
            placeholder="输入规则名称">
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">优先级</label>
          <input v-model.number="localRule.priority" type="number" 
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
            placeholder="0">
        </div>
      </div>
      
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
        <textarea v-model="localRule.description" rows="2"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="规则描述（可选）"></textarea>
      </div>
      
      <div class="flex items-center gap-2">
        <input v-model="localRule.is_active" type="checkbox" id="is_active"
          class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary">
        <label for="is_active" class="text-sm text-gray-700 dark:text-gray-300">启用规则</label>
      </div>
    </div>

    <!-- 触发器 -->
    <div class="space-y-4">
      <h3 class="text-lg font-medium text-gray-900 dark:text-white">触发器 *</h3>
      
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">触发类型</label>
        <select v-model="localRule.trigger_type"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent">
          <option v-for="trigger in metadata.trigger_types" :key="trigger.type" :value="trigger.type">
            {{ trigger.name }} - {{ trigger.description }}
          </option>
        </select>
      </div>
    </div>

    <!-- 条件 -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">条件（可选）</h3>
        <button @click="addCondition" 
          class="px-3 py-1 text-sm text-primary hover:bg-primary/10 rounded-lg flex items-center gap-1">
          <Plus class="w-4 h-4" /> 添加条件
        </button>
      </div>
      
      <p class="text-sm text-gray-500 dark:text-gray-400">所有条件必须同时满足（AND 关系）</p>
      
      <div v-if="conditions.length === 0" class="text-center py-4 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-lg">
        无条件限制，触发时总是执行
      </div>
      
      <div v-else class="space-y-2">
        <div v-for="(condition, index) in conditions" :key="index"
          class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-900 cursor-pointer"
            @click="toggleCondition(index)">
            <div class="flex items-center gap-2">
              <GripVertical class="w-4 h-4 text-gray-400" />
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ getFieldName(condition.field) }} {{ getOperatorName(condition.operator) }} 
                <span v-if="operatorRequiresValue(condition.operator)" class="text-gray-500">"{{ condition.value }}"</span>
              </span>
            </div>
            <div class="flex items-center gap-2">
              <button @click.stop="removeCondition(index)" class="p-1 text-gray-400 hover:text-red-500">
                <Trash2 class="w-4 h-4" />
              </button>
              <component :is="expandedConditions.has(index) ? ChevronUp : ChevronDown" class="w-4 h-4 text-gray-400" />
            </div>
          </div>
          
          <div v-if="expandedConditions.has(index)" class="p-4 space-y-3 bg-white dark:bg-gray-800">
            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">字段</label>
                <select v-model="condition.field"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800">
                  <option v-for="field in metadata.available_fields" :key="field.field" :value="field.field">
                    {{ field.name }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">操作符</label>
                <select v-model="condition.operator"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800">
                  <option v-for="op in metadata.condition_operators" :key="op.operator" :value="op.operator">
                    {{ op.name }}
                  </option>
                </select>
              </div>
              <div v-if="operatorRequiresValue(condition.operator)">
                <label class="block text-xs font-medium text-gray-500 mb-1">值</label>
                <input v-model="condition.value" type="text"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800"
                  placeholder="输入值">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 动作 -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white">动作 *</h3>
        <button @click="addAction" 
          class="px-3 py-1 text-sm text-primary hover:bg-primary/10 rounded-lg flex items-center gap-1">
          <Plus class="w-4 h-4" /> 添加动作
        </button>
      </div>
      
      <p class="text-sm text-gray-500 dark:text-gray-400">按顺序执行所有动作</p>
      
      <div v-if="actions.length === 0" class="text-center py-4 text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg">
        请至少添加一个动作
      </div>
      
      <div v-else class="space-y-2">
        <div v-for="(action, index) in actions" :key="index"
          class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-900 cursor-pointer"
            @click="toggleAction(index)">
            <div class="flex items-center gap-2">
              <span class="w-5 h-5 flex items-center justify-center text-xs font-bold text-white bg-primary rounded-full">
                {{ index + 1 }}
              </span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                {{ getActionTypeName(action.type) }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <button @click.stop="removeAction(index)" class="p-1 text-gray-400 hover:text-red-500">
                <Trash2 class="w-4 h-4" />
              </button>
              <component :is="expandedActions.has(index) ? ChevronUp : ChevronDown" class="w-4 h-4 text-gray-400" />
            </div>
          </div>
          
          <div v-if="expandedActions.has(index)" class="p-4 space-y-3 bg-white dark:bg-gray-800">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">动作类型</label>
              <select v-model="action.type" @change="action.config = {}"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800">
                <option v-for="at in metadata.action_types" :key="at.type" :value="at.type">
                  {{ at.name }} - {{ at.description }}
                </option>
              </select>
            </div>
            
            <!-- 动态配置字段 -->
            <div v-for="(schema, key) in getActionConfigSchema(action.type)" :key="key">
              <label class="block text-xs font-medium text-gray-500 mb-1">
                {{ schema.description || key }}
                <span v-if="metadata.action_types?.find((a: any) => a.type === action.type)?.config_schema?.required?.includes(key)" class="text-red-500">*</span>
              </label>
              <input v-if="schema.type === 'string'" v-model="action.config[key]" type="text"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800"
                :placeholder="schema.description">
              <select v-else-if="schema.enum" v-model="action.config[key]"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800">
                <option v-for="opt in schema.enum" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
      <button @click="emit('cancel')"
        class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
        取消
      </button>
      <button @click="handleSave" :disabled="!isValid"
        class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed">
        保存规则
      </button>
    </div>
  </div>
</template>