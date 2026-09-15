<script setup lang="ts">
const props = defineProps<{ password: string }>()
const { t } = useI18n()

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
    1: { labelKey: 'common.password.weak', color: 'bg-red-500', width: '25%' },
    2: { labelKey: 'common.password.fair', color: 'bg-orange-400', width: '50%' },
    3: { labelKey: 'common.password.strong', color: 'bg-blue-500', width: '75%' },
    4: { labelKey: 'common.password.veryStrong', color: 'bg-green-500', width: '100%' },
  } as Record<number, { labelKey: string; color: string; width: string }>

  return { score: level, label: t(map[level].labelKey), color: map[level].color, width: map[level].width }
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
      {{ t('common.password.hint') }}
    </p>
  </div>
</template>
