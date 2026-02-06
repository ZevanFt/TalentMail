<!-- <template>
  <div>
    <NuxtRouteAnnouncer />
    <NuxtWelcome />
  </div>
</template> -->

<script setup lang="ts">
const { initTheme } = useTheme()
const token = useCookie('token')

onMounted(() => {
  initTheme()
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />

    <!-- 全局挂载弹窗 - 仅登录后显示 -->
    <EmailComposeModal v-if="token" />
  </NuxtLayout>
</template>