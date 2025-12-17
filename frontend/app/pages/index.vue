<!-- <template> -->
  <!-- 
    核心修复：
    1. 使用 flex w-full h-full 确保撑满父容器
    2. EmailEmailList 和 EmailEmailDetail 是 Nuxt 根据 components/email/ 目录自动生成的组件名
  -->
  <!-- <div class="flex w-full h-full bg-white dark:bg-bg-dark overflow-hidden"> -->
    <!-- 第二栏：邮件列表 (固定宽度 320px) -->
    <!-- <EmailEmailList /> -->
    
    <!-- 第三栏：邮件详情 (自适应剩余空间) -->
    <!-- <EmailEmailDetail /> -->
  <!-- </div> -->
<!-- </template> -->

<template>
  <div class="flex w-full h-full bg-white dark:bg-bg-dark overflow-hidden">
    <!-- 
      修复：组件名变了！
      Email (文件夹名) + List (文件名) = EmailList
    -->
    <EmailList />
    
    <EmailDetail />
  </div>
</template>