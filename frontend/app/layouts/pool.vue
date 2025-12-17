<template>
  <div class="flex flex-col h-screen w-full bg-bg-light dark:bg-bg-dark text-gray-900 dark:text-gray-100 overflow-hidden font-sans">
    
    <!-- 1. 保留全局 Header -->
    <LayoutHeader />
    
    <!-- 2. 下方内容区：占满宽度 (没有侧边栏了！) -->
    <div class="flex-1 flex overflow-hidden relative">
      <slot />
    </div>
    
  </div>
</template>