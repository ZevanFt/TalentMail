<script setup lang="ts">
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: Date | null
}>()

const emit = defineEmits(['update:modelValue'])

// 当前显示的月份
const currentMonth = ref(new Date())
const selectedHour = ref(9)

// 星期标题
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

// 时间选项
const hours = [8, 9, 10, 12, 14, 16, 18, 20]

// 获取当月的日期网格
const calendarDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  
  // 当月第一天
  const firstDay = new Date(year, month, 1)
  // 当月最后一天
  const lastDay = new Date(year, month + 1, 0)
  
  const days: { date: Date; isCurrentMonth: boolean; isToday: boolean; isPast: boolean }[] = []
  
  // 填充上月的日期
  const startPadding = firstDay.getDay()
  for (let i = startPadding - 1; i >= 0; i--) {
    const date = new Date(year, month, -i)
    days.push({ date, isCurrentMonth: false, isToday: false, isPast: true })
  }
  
  // 当月日期
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const date = new Date(year, month, d)
    days.push({
      date,
      isCurrentMonth: true,
      isToday: date.getTime() === today.getTime(),
      isPast: date < today
    })
  }
  
  // 填充下月的日期（补齐6行）
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const date = new Date(year, month + 1, i)
    days.push({ date, isCurrentMonth: false, isToday: false, isPast: false })
  }
  
  return days
})

// 月份标题
const monthTitle = computed(() => {
  return `${currentMonth.value.getFullYear()}年${currentMonth.value.getMonth() + 1}月`
})

// 上一月
const prevMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
}

// 下一月
const nextMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
}

// 选中的日期
const selectedDate = ref<Date | null>(props.modelValue)

// 选择日期
const selectDate = (day: { date: Date; isPast: boolean }) => {
  if (day.isPast) return
  selectedDate.value = day.date
  emitValue()
}

// 发送值
const emitValue = () => {
  if (selectedDate.value) {
    const result = new Date(selectedDate.value)
    result.setHours(selectedHour.value, 0, 0, 0)
    emit('update:modelValue', result)
  }
}

// 判断是否选中
const isSelected = (date: Date) => {
  if (!selectedDate.value) return false
  return date.toDateString() === selectedDate.value.toDateString()
}

// 监听时间变化
watch(selectedHour, emitValue)
</script>

<template>
  <div class="select-none">
    <!-- 月份导航 -->
    <div class="flex items-center justify-between mb-3">
      <button @click="prevMonth" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
        <ChevronLeft class="w-5 h-5" />
      </button>
      <span class="font-medium">{{ monthTitle }}</span>
      <button @click="nextMonth" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
        <ChevronRight class="w-5 h-5" />
      </button>
    </div>

    <!-- 星期标题 -->
    <div class="grid grid-cols-7 gap-1 mb-1">
      <div v-for="day in weekDays" :key="day" class="text-center text-xs text-gray-500 py-1">
        {{ day }}
      </div>
    </div>

    <!-- 日期网格 -->
    <div class="grid grid-cols-7 gap-1">
      <button
        v-for="(day, index) in calendarDays"
        :key="index"
        @click="selectDate(day)"
        :disabled="day.isPast"
        class="aspect-square flex items-center justify-center text-sm rounded-lg transition-colors"
        :class="{
          'text-gray-300 dark:text-gray-600 cursor-not-allowed': day.isPast,
          'text-gray-400 dark:text-gray-500': !day.isCurrentMonth && !day.isPast,
          'hover:bg-gray-100 dark:hover:bg-gray-700': !day.isPast && !isSelected(day.date),
          'bg-primary text-white': isSelected(day.date),
          'ring-2 ring-primary ring-inset': day.isToday && !isSelected(day.date)
        }"
      >
        {{ day.date.getDate() }}
      </button>
    </div>

    <!-- 时间选择 -->
    <div class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
      <div class="text-xs text-gray-500 mb-2">选择时间</div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="hour in hours"
          :key="hour"
          @click="selectedHour = hour"
          class="px-3 py-1.5 text-sm rounded-lg transition-colors"
          :class="selectedHour === hour 
            ? 'bg-primary text-white' 
            : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'"
        >
          {{ hour }}:00
        </button>
      </div>
    </div>
  </div>
</template>