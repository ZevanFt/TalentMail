<script setup lang="ts">
const { getPoolAdminSettings, updatePoolAdminSettings, runPoolAdminCleanup } = useApi()
const { t } = useI18n()

const loading = ref(true)
const saving = ref(false)
const running = ref(false)
const message = ref('')

const form = ref({
  cleanup_enabled: true,
  ttl_hours: 24,
  recoverable_days: 10,
  cleanup_interval_hours: 24,
  cleanup_batch_size: 500,
  delete_emails_on_purge: true,
  last_cleanup_at: null as string | null,
  last_cleanup_count: 0,
})

const load = async () => {
  loading.value = true
  message.value = ''
  try {
    const data = await getPoolAdminSettings()
    form.value = { ...form.value, ...data }
  } catch (e: any) {
    message.value = e.data?.detail || t('adminTools.tempMailboxPolicy.loadFailed')
  } finally {
    loading.value = false
  }
}

const save = async () => {
  saving.value = true
  message.value = ''
  try {
    const data = await updatePoolAdminSettings({
      cleanup_enabled: form.value.cleanup_enabled,
      ttl_hours: form.value.ttl_hours,
      recoverable_days: form.value.recoverable_days,
      cleanup_interval_hours: form.value.cleanup_interval_hours,
      cleanup_batch_size: form.value.cleanup_batch_size,
      delete_emails_on_purge: form.value.delete_emails_on_purge,
    })
    form.value = { ...form.value, ...data }
    message.value = t('adminTools.tempMailboxPolicy.saved')
  } catch (e: any) {
    message.value = e.data?.detail || t('adminTools.common.saveFailed')
  } finally {
    saving.value = false
  }
}

const runNow = async () => {
  running.value = true
  message.value = ''
  try {
    const res = await runPoolAdminCleanup()
    message.value = t('adminTools.tempMailboxPolicy.cleanupDone', { expired: res.expired_count, purged: res.purged_count })
    await load()
  } catch (e: any) {
    message.value = e.data?.detail || t('adminTools.tempMailboxPolicy.runFailed')
  } finally {
    running.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('adminTools.tempMailboxPolicy.title') }}</h2>
      <p class="text-sm text-gray-500 mt-1">{{ t('adminTools.tempMailboxPolicy.subtitle') }}</p>
    </div>

    <div v-if="loading" class="text-sm text-gray-500">{{ t('adminTools.common.loading') }}</div>

    <div v-else class="space-y-4 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark p-5">
      <div class="flex items-center justify-between">
        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('adminTools.tempMailboxPolicy.enableAutoCleanup') }}</label>
        <input v-model="form.cleanup_enabled" type="checkbox" />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <label class="text-sm text-gray-700 dark:text-gray-300">
          {{ t('adminTools.tempMailboxPolicy.ttlHours') }}
          <input v-model.number="form.ttl_hours" type="number" min="1" max="168" class="mt-1 w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900" />
        </label>
        <label class="text-sm text-gray-700 dark:text-gray-300">
          {{ t('adminTools.tempMailboxPolicy.recoverableDays') }}
          <input v-model.number="form.recoverable_days" type="number" min="1" max="30" class="mt-1 w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900" />
        </label>
        <label class="text-sm text-gray-700 dark:text-gray-300">
          {{ t('adminTools.tempMailboxPolicy.cleanupIntervalHours') }}
          <input v-model.number="form.cleanup_interval_hours" type="number" min="1" max="168" class="mt-1 w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900" />
        </label>
        <label class="text-sm text-gray-700 dark:text-gray-300">
          {{ t('adminTools.tempMailboxPolicy.batchSize') }}
          <input v-model.number="form.cleanup_batch_size" type="number" min="10" max="5000" class="mt-1 w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900" />
        </label>
      </div>

      <div class="flex items-center justify-between">
        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ t('adminTools.tempMailboxPolicy.deleteEmailsOnPurge') }}</label>
        <input v-model="form.delete_emails_on_purge" type="checkbox" />
      </div>

      <div class="text-xs text-gray-500">
        {{ t('adminTools.tempMailboxPolicy.lastCleanup', { time: form.last_cleanup_at || '-', count: form.last_cleanup_count }) }}
      </div>

      <div class="flex items-center gap-3">
        <button @click="save" :disabled="saving" class="px-4 py-2 rounded bg-primary text-white text-sm disabled:opacity-60">
          {{ saving ? t('adminTools.common.saving') : t('adminTools.tempMailboxPolicy.savePolicy') }}
        </button>
        <button @click="runNow" :disabled="running" class="px-4 py-2 rounded border border-gray-300 dark:border-gray-700 text-sm disabled:opacity-60">
          {{ running ? t('adminTools.tempMailboxPolicy.running') : t('adminTools.tempMailboxPolicy.runNow') }}
        </button>
      </div>

      <div v-if="message" class="text-sm text-gray-600 dark:text-gray-300">{{ message }}</div>
    </div>
  </div>
</template>
