<script setup lang="ts">
const props = defineProps<{ password: string }>()

const strength = computed(() => {
  const pwd = props.password || ''
  if (!pwd) return { score: 0, label: '', color: '', width: '0%' }

  let score = 0
  // 长度
  if (pwd.length >= 6) score++
  if (pwd.length >= 10) score++
  if (pwd.length >= 14) score++
  // 字符种类
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd)) score++

  // 映射到 4 级
  let level: number
  if (score <= 2) level = 1
  else if (score <= 4) level = 2
  else if (score <= 5) level = 3
  else level = 4

  const map = {
    1: { label: '弱', color: 'bg-red-500', width: '25%' },
    2: { label: '一般', color: 'bg-orange-400', width: '50%' },
    3: { label: '强', color: 'bg-blue-500', width: '75%' },
    4: { label: '很强', color: 'bg-green-500', width: '100%' },
  } as Record<number, { label: string; color: string; width: string }>

  return { score: level, ...map[level] }
})
</script>

<template>
  <div v-if="password" class="space-y-1">
    <div class="flex items-center gap-2">
      <div class="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-300"
          :class="strength.color"
          :style="{ width: strength.width }"
        />
      </div>
      <span class="text-xs font-medium shrink-0" :class="{
        'text-red-500': strength.score === 1,
        'text-orange-400': strength.score === 2,
        'text-blue-500': strength.score === 3,
        'text-green-500': strength.score === 4,
      }">{{ strength.label }}</span>
    </div>
    <p v-if="strength.score <= 2" class="text-xs text-gray-400">
      建议使用大小写字母、数字和特殊字符的组合，至少 10 位
    </p>
  </div>
</template>
