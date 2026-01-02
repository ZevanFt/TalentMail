<script setup lang="ts">
/**
 * 模板触发配置弹窗
 * 用于配置邮件模板的触发条件
 * 保存时创建 AutomationRule 记录
 */
import { X, Zap, Clock, Hand, ChevronDown, ChevronRight, Info, Loader2 } from 'lucide-vue-next'

const { getAvailableEvents, getTemplateTriggerRules, createTemplateTriggerRule, deleteTemplateTriggerRule } = useApi()

const props = defineProps<{
  modelValue: boolean
  template: {
    code: string
    name: string
    category: string
    variables?: Array<{ key: string; label: string; type: string }> | string[] | null
  } | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', config: TriggerConfig): void
}>()

// 触发配置类型
interface TriggerConfig {
  template_code: string
  trigger_type: 'user_event' | 'scheduled' | 'manual'
  trigger_event?: string
  trigger_config?: Record<string, any>
  conditions?: Array<{ field: string; operator: string; value: any }>
  send_to_type: 'trigger_user' | 'fixed_email' | 'admin'
  send_to_email?: string
  cooldown_hours: number
  is_enabled: boolean
}

interface SystemEvent {
  value: string
  label: string
  category: string
  category_label: string
  variables: string[]
}

// 状态
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const existingRules = ref<any[]>([])
const availableEvents = ref<SystemEvent[]>([])

// 表单数据
const config = reactive<TriggerConfig>({
  template_code: '',
  trigger_type: 'user_event',
  trigger_event: '',
  trigger_config: {},
  conditions: [],
  send_to_type: 'trigger_user',
  send_to_email: '',
  cooldown_hours: 0,
  is_enabled: true
})

// 按分类分组的事件
const groupedEvents = computed(() => {
  const groups: Record<string, { label: string; events: SystemEvent[] }> = {}
  for (const event of availableEvents.value) {
    if (!groups[event.category]) {
      groups[event.category] = {
        label: event.category_label,
        events: []
      }
    }
    groups[event.category]!.events.push(event)
  }
  return groups
})

// 定时周期选项
const scheduleOptions = [
  { value: 'daily', label: '每天' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
  { value: 'interval', label: '间隔' },
]

// 条件操作符
const conditionOperators = [
  { value: 'greater_than', label: '大于' },
  { value: 'less_than', label: '小于' },
  { value: 'equals', label: '等于' },
  { value: 'not_equals', label: '不等于' },
  { value: 'contains', label: '包含' },
]

// 可用字段（用于条件）
const availableFields = [
  { value: 'storage_used_percent', label: '存储使用百分比' },
  { value: 'email_count', label: '邮件数量' },
  { value: 'days_since_login', label: '距离上次登录天数' },
]

// 高级设置展开状态
const showAdvanced = ref(false)

// 当前选中事件的可用变量
const selectedEventVariables = computed(() => {
  if (config.trigger_type !== 'user_event' || !config.trigger_event) {
    return []
  }
  
  const event = availableEvents.value.find(e => e.value === config.trigger_event)
  return event?.variables || []
})

// 加载可用事件类型
const loadAvailableEvents = async () => {
  try {
    const events = await getAvailableEvents()
    availableEvents.value = events
  } catch (e) {
    console.error('加载事件类型失败:', e)
    // 使用默认事件列表作为后备
    availableEvents.value = [
      { value: 'user.registered', label: '用户注册成功', category: 'user', category_label: '👤 用户事件', variables: ['user_name', 'user_email', 'register_time'] },
      { value: 'user.login_new_device', label: '新设备登录', category: 'user', category_label: '👤 用户事件', variables: ['user_name', 'login_time', 'login_ip'] },
      { value: 'user.password_changed', label: '密码修改成功', category: 'user', category_label: '👤 用户事件', variables: ['user_name', 'change_time'] },
    ]
  }
}

// 加载已有的触发规则
const loadExistingRules = async () => {
  if (!props.template?.code) return
  
  loading.value = true
  try {
    existingRules.value = await getTemplateTriggerRules(props.template.code)
    
    // 如果有已存在的规则，加载第一条的配置
    if (existingRules.value.length > 0) {
      const rule = existingRules.value[0]
      config.trigger_type = rule.trigger_type as any
      config.trigger_event = rule.trigger_config?.event_type || ''
      config.trigger_config = rule.trigger_config || {}
      config.conditions = rule.conditions || []
      config.is_enabled = rule.is_active
      
      // 解析动作配置
      const action = rule.actions?.find((a: any) => a.type === 'send_template_email')
      if (action?.config) {
        config.send_to_type = action.config.to_type || 'trigger_user'
        config.send_to_email = action.config.to || ''
      }
    }
  } catch (e) {
    console.error('加载触发规则失败:', e)
  } finally {
    loading.value = false
  }
}

// 关闭弹窗
const close = () => {
  emit('update:modelValue', false)
}

// 保存配置
const save = async () => {
  if (!props.template?.code) return
  
  saving.value = true
  error.value = ''
  
  try {
    // 如果已有规则，先删除
    for (const rule of existingRules.value) {
      await deleteTemplateTriggerRule(rule.id)
    }
    
    // 如果是手动模式，不创建规则
    if (config.trigger_type === 'manual') {
      emit('save', { ...config, template_code: props.template.code })
      close()
      return
    }
    
    // 创建新规则
    await createTemplateTriggerRule(props.template.code, {
      trigger_type: config.trigger_type,
      trigger_event: config.trigger_event,
      trigger_config: config.trigger_config || {},
      conditions: config.conditions || [],
      send_to_type: config.send_to_type,
      send_to_email: config.send_to_email,
      cooldown_hours: config.cooldown_hours,
      is_enabled: config.is_enabled
    })
    
    emit('save', { ...config, template_code: props.template.code })
    close()
  } catch (e: any) {
    error.value = e.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

// 添加条件
const addCondition = () => {
  config.conditions?.push({ field: '', operator: 'greater_than', value: '' })
}

// 删除条件
const removeCondition = (index: number) => {
  config.conditions?.splice(index, 1)
}

// 监听弹窗打开，加载数据
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen && props.template) {
    config.template_code = props.template.code
    // 重置表单
    config.trigger_type = 'user_event'
    config.trigger_event = ''
    config.trigger_config = {}
    config.conditions = []
    config.send_to_type = 'trigger_user'
    config.send_to_email = ''
    config.cooldown_hours = 0
    config.is_enabled = true
    error.value = ''
    
    // 加载数据
    await loadAvailableEvents()
    await loadExistingRules()
  }
}, { immediate: true })
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="modelValue" 
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      @click.self="close"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        
        <!-- 标题栏 -->
        <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <Zap class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">触发设置</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ template?.name }}</p>
            </div>
          </div>
          <button @click="close" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">
            <X class="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        <!-- 内容区 -->
        <div v-if="loading" class="flex-1 flex items-center justify-center py-12">
          <Loader2 class="w-8 h-8 animate-spin text-blue-500" />
        </div>
        <div v-else class="flex-1 overflow-y-auto p-5 space-y-6">
          
          <!-- 错误提示 -->
          <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">
            {{ error }}
          </div>
          
          <!-- 已有规则提示 -->
          <div v-if="existingRules.length > 0" class="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div class="flex items-center gap-2 text-green-700 dark:text-green-400">
              <Zap class="w-4 h-4" />
              <span class="font-medium">已配置触发规则</span>
            </div>
            <p class="text-sm text-green-600 dark:text-green-500 mt-1">
              此模板已配置自动触发，修改后将更新现有规则
            </p>
          </div>
          
          <!-- 启用状态 -->
          <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
            <div>
              <span class="font-medium text-gray-900 dark:text-white">启用自动触发</span>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">开启后，当触发条件满足时将自动发送邮件</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="config.is_enabled" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-300 peer-focus:ring-2 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <!-- 触发方式选择 -->
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-3">触发方式</h4>
            <div class="space-y-3">
              
              <!-- 系统事件触发 -->
              <label
                :class="[
                  'block p-4 rounded-xl border-2 cursor-pointer transition',
                  config.trigger_type === 'user_event'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-start gap-3">
                  <input
                    type="radio"
                    v-model="config.trigger_type"
                    value="user_event"
                    class="mt-1"
                  >
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <Zap class="w-4 h-4 text-blue-500" />
                      <span class="font-medium text-gray-900 dark:text-white">系统事件触发</span>
                    </div>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">当系统发生特定事件时自动发送邮件</p>
                    
                    <!-- 事件选择器 -->
                    <div v-if="config.trigger_type === 'user_event'" class="mt-4 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                      <label class="text-sm text-gray-500 dark:text-gray-400 mb-2 block">选择触发事件：</label>
                      <div class="space-y-1 max-h-48 overflow-y-auto">
                        <template v-for="(category, key) in groupedEvents" :key="key">
                          <div class="text-xs text-gray-400 dark:text-gray-500 font-medium mt-2 mb-1">{{ category.label }}</div>
                          <label
                            v-for="event in category.events"
                            :key="event.value"
                            class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700/50"
                          >
                            <input
                              type="radio"
                              v-model="config.trigger_event"
                              :value="event.value"
                            >
                            <span class="text-sm text-gray-700 dark:text-gray-300">{{ event.label }}</span>
                            <code class="ml-auto text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{{ event.value }}</code>
                          </label>
                        </template>
                      </div>
                    </div>
                  </div>
                </div>
              </label>
              
              <!-- 定时触发 -->
              <label 
                :class="[
                  'block p-4 rounded-xl border-2 cursor-pointer transition',
                  config.trigger_type === 'scheduled' 
                    ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20' 
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-start gap-3">
                  <input 
                    type="radio" 
                    v-model="config.trigger_type" 
                    value="scheduled" 
                    class="mt-1"
                  >
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <Clock class="w-4 h-4 text-amber-500" />
                      <span class="font-medium text-gray-900 dark:text-white">定时触发</span>
                    </div>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">按照设定的时间周期自动检查并发送</p>
                    
                    <!-- 定时配置 -->
                    <div v-if="config.trigger_type === 'scheduled'" class="mt-4 space-y-4">
                      <div class="flex gap-2">
                        <label 
                          v-for="opt in scheduleOptions" 
                          :key="opt.value"
                          :class="[
                            'flex-1 py-2 text-center rounded-lg cursor-pointer text-sm transition',
                            config.trigger_config?.schedule === opt.value 
                              ? 'bg-amber-500 text-white' 
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                          ]"
                        >
                          <input 
                            type="radio" 
                            :value="opt.value" 
                            v-model="config.trigger_config!.schedule"
                            class="sr-only"
                          >
                          {{ opt.label }}
                        </label>
                      </div>
                      <div class="flex items-center gap-3">
                        <span class="text-sm text-gray-500">执行时间：</span>
                        <input 
                          type="time" 
                          v-model="config.trigger_config!.time"
                          class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
                        >
                      </div>
                    </div>
                  </div>
                </div>
              </label>
              
              <!-- 手动使用 -->
              <label 
                :class="[
                  'block p-4 rounded-xl border-2 cursor-pointer transition',
                  config.trigger_type === 'manual' 
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20' 
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-start gap-3">
                  <input 
                    type="radio" 
                    v-model="config.trigger_type" 
                    value="manual" 
                    class="mt-1"
                  >
                  <div>
                    <div class="flex items-center gap-2">
                      <Hand class="w-4 h-4 text-green-500" />
                      <span class="font-medium text-gray-900 dark:text-white">手动使用</span>
                    </div>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">用户在撰写邮件时选择此模板发送</p>
                  </div>
                </div>
              </label>
              
            </div>
          </div>
          
          <!-- 触发条件（定时触发时显示） -->
          <div v-if="config.trigger_type === 'scheduled'" class="hidden">
            <h4 class="font-medium text-gray-900 dark:text-white mb-3">触发条件（满足条件才发送）</h4>
            <div class="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl space-y-3">
              <div 
                v-for="(condition, index) in config.conditions" 
                :key="index"
                class="flex items-center gap-2"
              >
                <select 
                  v-model="condition.field"
                  class="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
                >
                  <option value="">选择字段</option>
                  <option v-for="f in availableFields" :key="f.value" :value="f.value">{{ f.label }}</option>
                </select>
                <select 
                  v-model="condition.operator"
                  class="w-28 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
                >
                  <option v-for="op in conditionOperators" :key="op.value" :value="op.value">{{ op.label }}</option>
                </select>
                <input 
                  v-model="condition.value"
                  type="text"
                  class="w-24 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
                  placeholder="值"
                >
                <button 
                  @click="removeCondition(index)"
                  class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg"
                >
                  ✕
                </button>
              </div>
              <button 
                @click="addCondition"
                class="text-sm text-blue-500 hover:text-blue-600"
              >
                + 添加条件
              </button>
            </div>
          </div>
          
          <!-- 发送给谁 -->
          <div v-if="config.trigger_type !== 'manual'">
            <h4 class="font-medium text-gray-900 dark:text-white mb-3">发送给谁</h4>
            <div class="space-y-2">
              <label class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
                <input type="radio" v-model="config.send_to_type" value="trigger_user">
                <div>
                  <span class="font-medium text-gray-700 dark:text-gray-300">触发事件的用户本人</span>
                  <p class="text-xs text-gray-500 dark:text-gray-400">邮件将发送到触发此事件的用户邮箱</p>
                </div>
              </label>
              <label class="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
                <input type="radio" v-model="config.send_to_type" value="fixed_email" class="mt-1">
                <div class="flex-1">
                  <span class="font-medium text-gray-700 dark:text-gray-300">指定邮箱</span>
                  <input 
                    v-if="config.send_to_type === 'fixed_email'"
                    v-model="config.send_to_email"
                    type="email" 
                    placeholder="admin@example.com" 
                    class="mt-2 w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-sm"
                  >
                </div>
              </label>
              <label class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
                <input type="radio" v-model="config.send_to_type" value="admin">
                <span class="font-medium text-gray-700 dark:text-gray-300">系统管理员</span>
              </label>
            </div>
          </div>
          
          <!-- 高级设置 -->
          <div>
            <button 
              @click="showAdvanced = !showAdvanced"
              class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            >
              <component :is="showAdvanced ? ChevronDown : ChevronRight" class="w-4 h-4" />
              高级设置
            </button>
            <div v-if="showAdvanced" class="mt-3 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl space-y-4">
              <label class="flex items-start gap-3">
                <input type="checkbox" :checked="config.cooldown_hours > 0" @change="config.cooldown_hours = ($event.target as HTMLInputElement).checked ? 24 : 0" class="mt-1">
                <div>
                  <span class="text-sm text-gray-700 dark:text-gray-300">设置冷却时间（避免重复发送）</span>
                  <div v-if="config.cooldown_hours > 0" class="flex items-center gap-2 mt-2">
                    <span class="text-sm text-gray-500">冷却时间：</span>
                    <input 
                      v-model.number="config.cooldown_hours"
                      type="number" 
                      class="w-20 px-3 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded text-sm"
                    >
                    <span class="text-sm text-gray-500">小时</span>
                  </div>
                </div>
              </label>
            </div>
          </div>
          
          <!-- 可用变量预览 -->
          <div v-if="config.trigger_type === 'user_event' && selectedEventVariables.length > 0" class="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/50 rounded-xl">
            <div class="flex items-center gap-2 mb-3">
              <Info class="w-4 h-4 text-green-600 dark:text-green-400" />
              <span class="font-medium text-green-700 dark:text-green-400">此事件触发时可用的变量：</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <code 
                v-for="v in selectedEventVariables" 
                :key="v"
                class="px-2 py-1 text-sm bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded border border-gray-200 dark:border-gray-600"
              >
                &#123;&#123;{{ v }}&#125;&#125;
              </code>
            </div>
          </div>
          
        </div>
        
        <!-- 底部按钮 -->
        <div class="flex items-center justify-end gap-3 p-5 border-t border-gray-200 dark:border-gray-700">
          <button 
            @click="close"
            class="px-5 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition"
          >
            取消
          </button>
          <button
            @click="save"
            :disabled="saving"
            class="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium disabled:opacity-50"
          >
            <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
            <span>{{ saving ? '保存中...' : '保存设置' }}</span>
          </button>
        </div>
        
      </div>
    </div>
  </Teleport>
</template>