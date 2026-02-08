<template>
  <!-- 最外层：垂直排列 (Header 在上，内容在下) -->
  <div
    class="layout-default flex flex-col h-screen w-full bg-bg-light dark:bg-bg-dark text-gray-900 dark:text-gray-100 overflow-hidden font-sans">

    <!-- 1. 顶部通栏 Header (固定高度) -->
    <LayoutHeader />

    <!-- 2. 下方主体区域：水平排列 (侧边栏 + 页面内容) -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 侧边栏 (固定宽度) -->
      <LayoutSidebar />

      <!-- 页面内容 (Slot 对应 pages/index.vue，里面包含 列表+详情) -->
      <div class="flex-1 min-w-0">
        <slot />
      </div>
    </div>

  </div>
</template>