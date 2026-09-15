<script setup lang="ts">
import { Loader2, AlertCircle, Mail } from 'lucide-vue-next'

const { ssoCallback, ssoBind } = useApi()
const { appName } = useConfig()
const { t } = useI18n()

definePageMeta({ layout: false })
useHead({ title: computed(() => `${t('auth.ssoCallback.loggingIn')} - ${appName}`) })

const error = ref('')
const loading = ref(true)
const bindMode = ref(false)

onMounted(async () => {
  const route = useRoute()
  const code = route.query.code as string | undefined
  const state = route.query.state as string | undefined

  if (!code) {
    error.value = t('auth.ssoCallback.missingCode')
    loading.value = false
    return
  }

  bindMode.value = !!state && state.startsWith('bind_')

  try {
    if (bindMode.value) {
      await ssoBind(code, state)
      const back = sessionStorage.getItem('sso_bind_return') || '/settings'
      sessionStorage.removeItem('sso_bind_return')
      await navigateTo(back, { replace: true })
      return
    }
    await ssoCallback(code, state)
    await navigateTo('/', { replace: true })
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message || ''
    error.value = detail || t('auth.ssoCallback.loginFailed')
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-bg-dark transition-colors duration-300 p-4">
    <div class="w-full max-w-[400px] bg-white dark:bg-bg-panelDark rounded-2xl shadow-xl p-8 md:p-10 transition-colors duration-300">

      <!-- Logo -->
      <div class="flex flex-col items-center mb-8">
        <div class="w-12 h-12 bg-gradient-to-tr from-primary to-purple-400 rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/30 mb-4">
          <Mail class="w-6 h-6" />
        </div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ appName }}</h1>
      </div>

      <!-- Loading 状态 -->
      <div v-if="loading" class="flex flex-col items-center gap-4 py-8">
        <Loader2 class="w-10 h-10 text-primary animate-spin" />
        <p class="text-gray-500 dark:text-gray-400 text-sm">{{ t('auth.ssoCallback.completing') }}</p>
      </div>

      <!-- 错误状态 -->
      <div v-else class="flex flex-col items-center gap-4 py-6">
        <div class="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
          <AlertCircle class="w-8 h-8 text-red-500 dark:text-red-400" />
        </div>
        <div class="text-center space-y-2">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('auth.ssoCallback.failedTitle') }}</h2>
          <p class="text-sm text-red-500 dark:text-red-400">{{ error }}</p>
        </div>
        <NuxtLink to="/login"
          class="mt-4 px-6 py-2.5 bg-primary hover:bg-primary-hover text-white font-medium rounded-xl transition-all text-sm">
          {{ t('auth.backToLogin') }}
        </NuxtLink>
      </div>

    </div>
  </div>
</template>
