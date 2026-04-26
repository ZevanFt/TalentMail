<script setup lang="ts">
import { X, User, Clock } from 'lucide-vue-next'

interface Suggestion {
  name: string | null
  email: string
  source: string // "contact" | "history"
}

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { getContactSuggestions } = useApi()

// ===== 内部状态 =====
const inputValue = ref('')
const chips = ref<string[]>([])
const suggestions = ref<Suggestion[]>([])
const showSuggestions = ref(false)
const highlightIndex = ref(-1)
const inputRef = ref<HTMLInputElement>()
const containerRef = ref<HTMLDivElement>()
const suggestionsRef = ref<HTMLDivElement>()

let debounceTimer: ReturnType<typeof setTimeout> | null = null

// ===== 从外部 v-model (逗号分隔字符串) 同步到 chips =====
const syncFromModelValue = (val: string) => {
  if (!val) {
    chips.value = []
    return
  }
  chips.value = val.split(',').map(s => s.trim()).filter(Boolean)
}

// 初始化
syncFromModelValue(props.modelValue)

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  const newChips = newVal ? newVal.split(',').map(s => s.trim()).filter(Boolean) : []
  // 仅在实质不同时更新（避免死循环）
  if (JSON.stringify(newChips) !== JSON.stringify(chips.value)) {
    chips.value = newChips
  }
})

// 同步 chips 到外部 v-model
const emitUpdate = () => {
  emit('update:modelValue', chips.value.join(', '))
}

// ===== 输入处理 =====
const handleInput = (e: Event) => {
  const val = (e.target as HTMLInputElement).value
  inputValue.value = val

  // 检查是否输入了逗号/分号 → 自动确认
  if (val.includes(',') || val.includes(';') || val.includes('；') || val.includes('，')) {
    const parts = val.split(/[,;，；]/).map(s => s.trim()).filter(Boolean)
    for (const part of parts) {
      addChip(part)
    }
    inputValue.value = ''
    closeSuggestions()
    return
  }

  // 防抖搜索建议
  if (debounceTimer) clearTimeout(debounceTimer)
  if (val.trim().length >= 1) {
    debounceTimer = setTimeout(() => fetchSuggestions(val.trim()), 300)
  } else {
    closeSuggestions()
  }
}

const fetchSuggestions = async (query: string) => {
  try {
    const res = await getContactSuggestions(query)
    // 过滤掉已经在 chips 里的
    const existing = new Set(chips.value.map(c => c.toLowerCase()))
    suggestions.value = (res.data || []).filter(s => !existing.has(s.email.toLowerCase()))
    showSuggestions.value = suggestions.value.length > 0
    highlightIndex.value = -1
  } catch (e) {
    console.error('联系人建议获取失败:', e)
    suggestions.value = []
    showSuggestions.value = false
  }
}

const closeSuggestions = () => {
  showSuggestions.value = false
  suggestions.value = []
  highlightIndex.value = -1
}

// ===== Chip 操作 =====
const addChip = (email: string) => {
  const trimmed = email.trim()
  if (!trimmed) return
  // 去重（不区分大小写）
  if (chips.value.some(c => c.toLowerCase() === trimmed.toLowerCase())) return
  chips.value.push(trimmed)
  emitUpdate()
}

const removeChip = (index: number) => {
  chips.value.splice(index, 1)
  emitUpdate()
  nextTick(() => inputRef.value?.focus())
}

const selectSuggestion = (suggestion: Suggestion) => {
  addChip(suggestion.email)
  inputValue.value = ''
  closeSuggestions()
  nextTick(() => inputRef.value?.focus())
}

// ===== 键盘事件 =====
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === 'Tab') {
    if (showSuggestions.value && highlightIndex.value >= 0) {
      e.preventDefault()
      selectSuggestion(suggestions.value[highlightIndex.value])
      return
    }
    if (inputValue.value.trim()) {
      e.preventDefault()
      addChip(inputValue.value)
      inputValue.value = ''
      closeSuggestions()
    }
  } else if (e.key === 'Backspace' && !inputValue.value && chips.value.length > 0) {
    removeChip(chips.value.length - 1)
  } else if (e.key === 'ArrowDown' && showSuggestions.value) {
    e.preventDefault()
    highlightIndex.value = Math.min(highlightIndex.value + 1, suggestions.value.length - 1)
  } else if (e.key === 'ArrowUp' && showSuggestions.value) {
    e.preventDefault()
    highlightIndex.value = Math.max(highlightIndex.value - 1, 0)
  } else if (e.key === 'Escape') {
    closeSuggestions()
  }
}

// ===== 粘贴处理 =====
const handlePaste = (e: ClipboardEvent) => {
  const text = e.clipboardData?.getData('text')
  if (!text) return

  // 如果粘贴内容有多个邮箱（逗号/分号/换行分隔）
  const parts = text.split(/[,;，；\n\r]+/).map(s => s.trim()).filter(Boolean)
  if (parts.length > 1) {
    e.preventDefault()
    for (const part of parts) {
      addChip(part)
    }
  }
  // 单个邮箱让默认行为处理
}

// ===== 失焦处理 =====
const handleBlur = () => {
  // 延迟关闭，让点击建议有时间触发
  setTimeout(() => {
    if (inputValue.value.trim()) {
      addChip(inputValue.value)
      inputValue.value = ''
    }
    closeSuggestions()
  }, 200)
}

// 点击容器聚焦输入框
const focusInput = () => {
  inputRef.value?.focus()
}
</script>

<template>
  <div
    ref="containerRef"
    @click="focusInput"
    class="contact-autocomplete relative flex flex-wrap items-center gap-1.5 px-3 py-2 min-h-[46px]
           bg-gray-50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 rounded-xl
           focus-within:bg-white dark:focus-within:bg-gray-900 focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary
           transition-all duration-200 cursor-text"
  >
    <!-- Chips -->
    <TransitionGroup name="chip">
      <span
        v-for="(chip, idx) in chips"
        :key="chip"
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium
               bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light
               max-w-[200px] truncate group/chip"
      >
        <span class="truncate">{{ chip }}</span>
        <button
          @click.stop="removeChip(idx)"
          class="shrink-0 p-0.5 rounded-full hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors
                 opacity-60 group-hover/chip:opacity-100"
        >
          <X class="w-3 h-3" />
        </button>
      </span>
    </TransitionGroup>

    <!-- Input -->
    <input
      ref="inputRef"
      :value="inputValue"
      @input="handleInput"
      @keydown="handleKeydown"
      @paste="handlePaste"
      @blur="handleBlur"
      :placeholder="chips.length === 0 ? (placeholder || '收件人 (多个用逗号分隔)') : ''"
      class="flex-1 min-w-[120px] bg-transparent border-none outline-none text-sm
             text-gray-900 dark:text-gray-100 placeholder:text-gray-400"
    />

    <!-- Suggestions Dropdown -->
    <Transition name="dropdown">
      <div
        v-if="showSuggestions"
        ref="suggestionsRef"
        class="absolute left-0 right-0 top-full mt-1 z-50
               bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
               rounded-xl shadow-lg max-h-[240px] overflow-y-auto"
      >
        <button
          v-for="(s, idx) in suggestions"
          :key="s.email"
          @mousedown.prevent="selectSuggestion(s)"
          :class="[
            'w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors',
            highlightIndex === idx
              ? 'bg-primary/10 dark:bg-primary/20'
              : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
          ]"
        >
          <div class="shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
               :class="s.source === 'contact' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'">
            <User v-if="s.source === 'contact'" class="w-4 h-4" />
            <Clock v-else class="w-4 h-4" />
          </div>
          <div class="flex-1 min-w-0">
            <div v-if="s.name" class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ s.name }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ s.email }}</div>
          </div>
          <span class="shrink-0 text-[10px] px-1.5 py-0.5 rounded-full"
                :class="s.source === 'contact' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-500' : 'bg-gray-100 dark:bg-gray-700 text-gray-400'">
            {{ s.source === 'contact' ? '联系人' : '历史' }}
          </span>
        </button>

        <div v-if="suggestions.length === 0" class="px-4 py-3 text-sm text-gray-400 text-center">
          无匹配联系人
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* Chip 动画 */
.chip-enter-active {
  transition: all 0.2s ease;
}
.chip-leave-active {
  transition: all 0.15s ease;
}
.chip-enter-from {
  opacity: 0;
  transform: scale(0.8);
}
.chip-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 下拉动画 */
.dropdown-enter-active {
  transition: all 0.15s ease;
}
.dropdown-leave-active {
  transition: all 0.1s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
