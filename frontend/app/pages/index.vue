<script setup lang="ts">
const { isMobile, isDesktop, mobileShowDetail, showEmailList } = useResponsive()
const { selectedEmailId } = useEmails()

// 清空选中邮件时自动回到列表视图
watch(() => selectedEmailId.value, (id) => {
  if (!id) showEmailList()
})
</script>

<template>
  <div class="flex w-full h-full main-container overflow-hidden">
    <!-- 桌面端：双栏并排 / 移动端：v-show 切换 -->
    <EmailList v-show="isDesktop || !mobileShowDetail" :class="isDesktop ? 'w-80 shrink-0' : 'w-full'" />
    <EmailDetail v-show="isDesktop || mobileShowDetail" :class="isDesktop ? '' : 'w-full'" />
  </div>
</template>