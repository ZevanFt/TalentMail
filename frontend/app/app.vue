<!-- <template>
  <div>
    <NuxtRouteAnnouncer />
    <NuxtWelcome />
  </div>
</template> -->

<script setup lang="ts">
const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
    
    <!-- 全局挂载弹窗 -->
    <EmailComposeModal />
  </NuxtLayout>
</template>