<script setup lang="ts">
import { useRouter } from '#imports'
import { onMounted } from 'vue'

const router = useRouter()

// 重定向到设置页面的工作流标签
onMounted(() => {
  router.replace('/settings?tab=my-workflows')
})

definePageMeta({
  layout: 'default'
})
</script>

<template>
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p class="text-gray-500">正在跳转...</p>
    </div>
  </div>
</template>