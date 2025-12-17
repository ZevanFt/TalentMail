<!-- <template>
  <div>
    <NuxtRouteAnnouncer />
    <NuxtWelcome />
  </div>
</template> -->

<template>
  <NuxtLayout>
    <NuxtPage />
    
    <!-- 全局挂载弹窗 -->
    <EmailComposeModal />
  </NuxtLayout>
</template>