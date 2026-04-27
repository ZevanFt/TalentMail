<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  event?: {
    id: number
    title: string
    description: string | null
    location: string | null
    start_time: string
    end_time: string
    all_day: boolean
    color: string
    reminder_minutes: number | null
  } | null
}>()

const emit = defineEmits(['update:modelValue', 'saved', 'deleted'])

const { createCalendarEvent, updateCalendarEvent, deleteCalendarEvent } = useApi()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()

const PRESET_COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B',
  '#8B5CF6', '#EC4899', '#06B6D4', '#6B7280',
]

const saving = ref(false)
const deleting = ref(false)

const form = reactive({
  title: '',
  description: '',
  location: '',
  start_time: '',
  end_time: '',
  all_day: false,
  color: '#3B82F6',
  reminder_minutes: null as number | null,
})

const isEditing = computed(() => !!props.event?.id)

// 初始化表单
watch(() => props.modelValue, (open) => {
  if (!open) return
  if (props.event) {
    form.title = props.event.title
    form.description = props.event.description || ''
    form.location = props.event.location || ''
    form.all_day = props.event.all_day
    form.color = props.event.color || '#3B82F6'
    form.reminder_minutes = props.event.reminder_minutes
    // 转换为 datetime-local 格式
    form.start_time = toLocalInput(props.event.start_time)
    form.end_time = toLocalInput(props.event.end_time)
  } else {
    form.title = ''
    form.description = ''
    form.location = ''
    form.all_day = false
    form.color = '#3B82F6'
    form.reminder_minutes = null
    // 默认当前时间向后 1 小时
    const now = new Date()
    now.setMinutes(0, 0, 0)
    form.start_time = toLocalInput(now.toISOString())
    const end = new Date(now.getTime() + 3600000)
    form.end_time = toLocalInput(end.toISOString())
  }
})

const toLocalInput = (isoStr: string): string => {
  const d = new Date(isoStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const handleSave = async () => {
  if (!form.title.trim()) {
    toast.error('请输入事件标题')
    return
  }
  if (!form.start_time || !form.end_time) {
    toast.error('请选择开始和结束时间')
    return
  }

  saving.value = true
  try {
    const payload = {
      title: form.title.trim(),
      description: form.description || null,
      location: form.location || null,
      start_time: new Date(form.start_time).toISOString(),
      end_time: new Date(form.end_time).toISOString(),
      all_day: form.all_day,
      color: form.color,
      reminder_minutes: form.reminder_minutes,
    }

    if (isEditing.value && props.event) {
      await updateCalendarEvent(props.event.id, payload)
      toast.success('事件已更新')
    } else {
      await createCalendarEvent(payload)
      toast.success('事件已创建')
    }
    emit('saved')
    emit('update:modelValue', false)
  } catch (e: any) {
    toast.error(e.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!props.event?.id) return
  const ok = await confirmDialog({ message: '确定删除此事件？', type: 'danger' })
  if (!ok) return
  deleting.value = true
  try {
    await deleteCalendarEvent(props.event.id)
    toast.success('事件已删除')
    emit('deleted')
    emit('update:modelValue', false)
  } catch (e: any) {
    toast.error(e.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <CommonModal :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)"
    :title="isEditing ? '编辑事件' : '新建事件'" width-class="w-full max-w-lg">
    <div class="space-y-4">
      <!-- 标题 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          标题 <span class="text-red-500">*</span>
        </label>
        <input v-model="form.title" placeholder="事件标题" maxlength="255"
          class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
      </div>

      <!-- 全天 -->
      <div class="flex items-center gap-2">
        <input id="all-day" v-model="form.all_day" type="checkbox" class="rounded" />
        <label for="all-day" class="text-sm text-gray-700 dark:text-gray-300">全天事件</label>
      </div>

      <!-- 时间 -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">开始时间</label>
          <input v-model="form.start_time" :type="form.all_day ? 'date' : 'datetime-local'"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">结束时间</label>
          <input v-model="form.end_time" :type="form.all_day ? 'date' : 'datetime-local'"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
        </div>
      </div>

      <!-- 地点 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">地点</label>
        <input v-model="form.location" placeholder="（可选）" maxlength="500"
          class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
      </div>

      <!-- 描述 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
        <textarea v-model="form.description" placeholder="（可选）" rows="3"
          class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-y"></textarea>
      </div>

      <!-- 颜色 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">颜色</label>
        <div class="flex items-center gap-2">
          <button v-for="c in PRESET_COLORS" :key="c" @click="form.color = c"
            class="w-7 h-7 rounded-full border-2 transition-all"
            :class="form.color === c ? 'border-gray-900 dark:border-white scale-110' : 'border-transparent'"
            :style="{ backgroundColor: c }" />
        </div>
      </div>
    </div>

    <template #footer>
      <button v-if="isEditing" @click="handleDelete" :disabled="deleting"
        class="mr-auto px-4 py-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-sm disabled:opacity-50">
        {{ deleting ? '删除中...' : '删除' }}
      </button>
      <button @click="emit('update:modelValue', false)"
        class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">取消</button>
      <button @click="handleSave" :disabled="saving"
        class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
        <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </template>
  </CommonModal>
</template>
