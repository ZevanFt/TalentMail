<script setup lang="ts">
const { isMobile, isDesktop, isSidebarOpen, closeSidebar, initResponsive } = useResponsive()

provide('hasSidebar', true)

onMounted(() => {
  initResponsive()
})
</script>

<template>
  <!-- 最外层：垂直排列 (Header 在上，内容在下) -->
  <div
    class="layout-default flex flex-col h-screen w-full bg-bg-light dark:bg-bg-dark text-gray-900 dark:text-gray-100 overflow-hidden font-sans">

    <!-- 1. 顶部通栏 Header (固定高度) -->
    <LayoutHeader />

    <!-- 2. 下方主体区域：水平排列 (侧边栏 + 页面内容) -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 桌面端侧边栏 (内联) -->
      <LayoutSidebar v-if="!isMobile" />

      <!-- 移动端侧边栏 (抽屉 overlay) -->
      <Teleport to="body">
        <Transition name="drawer">
          <div v-if="isMobile && isSidebarOpen" class="fixed inset-0 z-40 flex">
            <!-- 半透明背景 -->
            <div class="absolute inset-0 bg-black/50" @click="closeSidebar"></div>
            <!-- 侧边栏抽屉 -->
            <div class="relative z-10 w-72 max-w-[85vw] h-full">
              <LayoutSidebar />
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- 页面内容 (Slot 对应 pages/index.vue，里面包含 列表+详情) -->
      <div class="flex-1 min-w-0">
        <slot />
      </div>
    </div>

  </div>
</template>

<style scoped>
/* 抽屉动画 */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-enter-active > div:last-child,
.drawer-leave-active > div:last-child {
  transition: transform 0.25s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > div:last-child,
.drawer-leave-to > div:last-child {
  transform: translateX(-100%);
}
</style>
