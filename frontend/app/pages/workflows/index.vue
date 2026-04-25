<script setup lang="ts">
definePageMeta({ layout: 'default' })

// 工作流列表已整合到设置页面，直接重定向
navigateTo('/settings?tab=my-workflows', { replace: true })
</script>
