<script setup lang="ts">
import { ChevronLeft, ChevronRight, Plus, Upload, Loader2 } from 'lucide-vue-next'

const config = useConfig()
useHead({ title: `日历 - ${config.appName}` })
const toast = useToast()
const { getCalendarEvents, importIcs } = useApi()

// ---- 当前月份 ----
const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth()) // 0-indexed

const monthLabel = computed(() => {
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  return `${currentYear.value}年${months[currentMonth.value]}`
})

const prevMonth = () => {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
  loadEvents()
}

const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
  loadEvents()
}

const goToday = () => {
  const now = new Date()
  currentYear.value = now.getFullYear()
  currentMonth.value = now.getMonth()
  loadEvents()
}

// ---- 日历网格 ----
interface CalendarDay {
  date: Date
  day: number
  isCurrentMonth: boolean
  isToday: boolean
  events: any[]
}

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

const calendarDays = computed((): CalendarDay[] => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  // 周一为一周起始
  let startDow = firstDay.getDay() - 1
  if (startDow < 0) startDow = 6

  const days: CalendarDay[] = []
  const todayStr = formatDateKey(new Date())

  // 上月填充
  for (let i = startDow - 1; i >= 0; i--) {
    const d = new Date(year, month, -i)
    days.push({
      date: d,
      day: d.getDate(),
      isCurrentMonth: false,
      isToday: false,
      events: eventsForDate(d),
    })
  }

  // 本月
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const date = new Date(year, month, d)
    days.push({
      date,
      day: d,
      isCurrentMonth: true,
      isToday: formatDateKey(date) === todayStr,
      events: eventsForDate(date),
    })
  }

  // 下月填充（补满 6 行 42 格）
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i)
    days.push({
      date: d,
      day: d.getDate(),
      isCurrentMonth: false,
      isToday: false,
      events: eventsForDate(d),
    })
  }

  return days
})

const formatDateKey = (d: Date): string => {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// ---- 事件数据 ----
const events = ref<any[]>([])
const loading = ref(true)
const loadError = ref(false)

const eventsForDate = (date: Date): any[] => {
  const dateStr = formatDateKey(date)
  return events.value.filter(ev => {
    const start = new Date(ev.start_time)
    const end = new Date(ev.end_time)
    const startStr = formatDateKey(start)
    const endStr = formatDateKey(new Date(end.getTime() - 1)) // 结束时间减1ms（避免隔天0点算下一天）
    return dateStr >= startStr && dateStr <= endStr
  })
}

const hasEventsThisMonth = computed(() => {
  return calendarDays.value.some(day => day.isCurrentMonth && day.events.length > 0)
})

const loadEvents = async () => {
  loading.value = true
  loadError.value = false
  try {
    const start = new Date(currentYear.value, currentMonth.value - 1, 1).toISOString()
    const end = new Date(currentYear.value, currentMonth.value + 2, 0).toISOString()
    events.value = await getCalendarEvents(start, end)
  } catch (e: any) {
    console.error('加载事件失败', e)
    loadError.value = true
    toast.error('加载日历失败')
  } finally {
    loading.value = false
  }
}

// ---- 事件弹窗 ----
const showEventModal = ref(false)
const editingEvent = ref<any>(null)

const openNewEvent = (date?: Date) => {
  if (date) {
    const d = new Date(date)
    d.setHours(9, 0, 0, 0)
    editingEvent.value = {
      title: '',
      description: null,
      location: null,
      start_time: d.toISOString(),
      end_time: new Date(d.getTime() + 3600000).toISOString(),
      all_day: false,
      color: '#3B82F6',
      reminder_minutes: null,
    }
  } else {
    editingEvent.value = null
  }
  showEventModal.value = true
}

const openEditEvent = (ev: any) => {
  editingEvent.value = ev
  showEventModal.value = true
}

// ---- 选中日期详情 ----
const selectedDate = ref<Date | null>(null)
const selectedDateEvents = computed(() => {
  if (!selectedDate.value) return []
  return eventsForDate(selectedDate.value)
})
const selectedDateLabel = computed(() => {
  if (!selectedDate.value) return ''
  return selectedDate.value.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })
})

const selectDate = (day: CalendarDay) => {
  selectedDate.value = day.date
}

// ---- .ics 导入 ----
const importingIcs = ref(false)
const handleIcsImport = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  importingIcs.value = true
  try {
    const result = await importIcs(input.files[0])
    if (result.imported > 0) {
      toast.success(`成功导入 ${result.imported} 个事件`)
      await loadEvents()
    } else {
      toast.info('没有新事件被导入')
    }
  } catch (e: any) {
    toast.error(e.data?.detail || '导入失败')
  } finally {
    importingIcs.value = false
    input.value = ''
  }
}

const formatTime = (isoStr: string, allDay: boolean): string => {
  if (allDay) return '全天'
  const d = new Date(isoStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(loadEvents)
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-bg-dark">
    <div class="max-w-6xl mx-auto p-6">
      <!-- 头部 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <button @click="prevMonth" class="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors">
            <ChevronLeft class="w-5 h-5" />
          </button>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white min-w-[140px] text-center">{{ monthLabel }}</h1>
          <button @click="nextMonth" class="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors">
            <ChevronRight class="w-5 h-5" />
          </button>
          <button @click="goToday" class="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            今天
          </button>
        </div>
        <div class="flex items-center gap-2">
          <label class="flex items-center gap-2 px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <Upload class="w-4 h-4" />
            {{ importingIcs ? '导入中...' : '导入 .ics' }}
            <input type="file" accept=".ics" class="hidden" @change="handleIcsImport" :disabled="importingIcs" />
          </label>
          <button @click="openNewEvent()" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
            <Plus class="w-4 h-4" /> 新建事件
          </button>
        </div>
      </div>

      <!-- 加载错误 -->
      <div v-if="loadError && !loading" class="flex flex-col items-center justify-center py-20 gap-4">
        <div class="text-5xl">😵</div>
        <p class="text-gray-500 dark:text-gray-400">加载日历失败</p>
        <button @click="loadEvents" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
          重新加载
        </button>
      </div>

      <div v-else class="flex gap-6">
        <!-- 月历网格 -->
        <div class="flex-1 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark overflow-hidden">
          <!-- 星期标题 -->
          <div class="grid grid-cols-7 border-b border-gray-200 dark:border-gray-700">
            <div v-for="wd in WEEKDAYS" :key="wd" class="py-2 text-center text-xs font-medium text-gray-500 uppercase">
              {{ wd }}
            </div>
          </div>

          <!-- 加载骨架屏 -->
          <div v-if="loading" class="grid grid-cols-7">
            <div v-for="i in 42" :key="i" class="min-h-[90px] border-b border-r border-gray-100 dark:border-gray-800 p-1.5">
              <div class="flex items-center justify-center mb-1">
                <div class="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse"></div>
              </div>
              <div v-if="i % 5 === 0" class="space-y-0.5">
                <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              </div>
            </div>
          </div>

          <!-- 日期格子 -->
          <div v-else class="grid grid-cols-7">
            <div
              v-for="(day, idx) in calendarDays" :key="idx"
              @click="selectDate(day)"
              class="min-h-[90px] border-b border-r border-gray-100 dark:border-gray-800 p-1.5 cursor-pointer transition-colors"
              :class="{
                'bg-gray-50/50 dark:bg-gray-900/30': !day.isCurrentMonth,
                'bg-blue-50/50 dark:bg-blue-900/20': day.isToday,
                'hover:bg-gray-50 dark:hover:bg-gray-800/50': day.isCurrentMonth && !day.isToday,
                'ring-2 ring-primary ring-inset': selectedDate && formatDateKey(selectedDate) === formatDateKey(day.date),
              }"
            >
              <!-- 日期数字 -->
              <div class="flex items-center justify-center mb-1">
                <span
                  class="w-7 h-7 flex items-center justify-center rounded-full text-sm"
                  :class="{
                    'text-gray-400': !day.isCurrentMonth,
                    'bg-primary text-white font-bold': day.isToday,
                    'text-gray-900 dark:text-white': day.isCurrentMonth && !day.isToday,
                  }"
                >{{ day.day }}</span>
              </div>

              <!-- 事件色块（最多显示 3 个） -->
              <div class="space-y-0.5">
                <div
                  v-for="ev in day.events.slice(0, 3)" :key="ev.id"
                  @click.stop="openEditEvent(ev)"
                  class="text-[10px] leading-tight px-1 py-0.5 rounded truncate text-white cursor-pointer hover:opacity-80 transition-opacity"
                  :style="{ backgroundColor: ev.color || '#3B82F6' }"
                >{{ ev.title }}</div>
                <div v-if="day.events.length > 3" class="text-[10px] text-gray-400 text-center">
                  +{{ day.events.length - 3 }} 更多
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态提示 -->
          <div v-if="!loading && !hasEventsThisMonth" class="py-4 text-center text-sm text-gray-400 border-t border-gray-100 dark:border-gray-800">
            📅 本月暂无事件，点击日期或右上角「新建事件」添加
          </div>
        </div>

        <!-- 右侧日期详情 -->
        <div class="w-72 shrink-0 hidden lg:block">
          <div class="bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-4 sticky top-6">
            <div v-if="selectedDate">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-bold text-gray-900 dark:text-white">{{ selectedDateLabel }}</h3>
                <button @click="openNewEvent(selectedDate)" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="在此日新建事件">
                  <Plus class="w-4 h-4 text-primary" />
                </button>
              </div>
              <div v-if="selectedDateEvents.length === 0" class="text-sm text-gray-400 py-4 text-center">
                暂无事件
              </div>
              <div v-else class="space-y-2">
                <div
                  v-for="ev in selectedDateEvents" :key="ev.id"
                  @click="openEditEvent(ev)"
                  class="p-2.5 rounded-lg border border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <div class="flex items-center gap-2 mb-1">
                    <div class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: ev.color || '#3B82F6' }"></div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ ev.title }}</span>
                  </div>
                  <div class="text-xs text-gray-500 ml-4.5">
                    {{ formatTime(ev.start_time, ev.all_day) }}
                    <span v-if="!ev.all_day"> - {{ formatTime(ev.end_time, false) }}</span>
                  </div>
                  <div v-if="ev.location" class="text-xs text-gray-400 ml-4.5 truncate mt-0.5">
                    📍 {{ ev.location }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-sm text-gray-400 py-8 text-center">
              点击日期查看详情
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 事件弹窗 -->
    <CalendarEventModal v-model="showEventModal" :event="editingEvent" @saved="loadEvents()" @deleted="loadEvents()" />
  </div>
</template>
