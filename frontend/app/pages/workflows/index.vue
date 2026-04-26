<script setup lang="ts">
definePageMeta({ layout: 'default' })
const config = useConfig()
useHead({ title: `工作流 - ${config.appName}` })

// 工作流列表已整合到设置页面，直接重定向
navigateTo('/settings?tab=my-workflows', { replace: true })
</script>
