<script setup lang="ts">
import { Loader2, RefreshCw, ShieldCheck } from 'lucide-vue-next'

const { t } = useI18n()
const { listOperationAudits } = useApi()
const toast = useToast()

interface AuditItem {
  id: number
  user_id: number | null
  actor_type: string
  action: string
  resource_type: string | null
  resource_id: string | null
  detail: string | null
  ip_address: string | null
  status: string
  created_at: string
}

const items = ref<AuditItem[]>([])
const total = ref(0)
const page = ref(1)
const limit = 20
const loading = ref(true)
const error = ref('')

const filterAction = ref('')
const filterStatus = ref('')
const filterUserId = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await listOperationAudits({
      page: page.value,
      limit,
      action: filterAction.value || undefined,
      status: filterStatus.value || undefined,
      user_id: filterUserId.value ? Number(filterUserId.value) : undefined,
    })
    items.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e?.data?.detail || t('common.error')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  page.value = 1
  load()
}

const formatTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

const statusClass = (s: string) =>
  s === 'success'
    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'

onMounted(load)
</script>

<template>
  <div class="card bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="section-title mb-0 flex items-center gap-2">
          <ShieldCheck class="w-4 h-4" /> {{ t('admin.auditTitle') }}
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ t('admin.auditSummary', { n: total }) }}
        </p>
      </div>
      <button @click="load" :disabled="loading"
        class="p-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
        :title="t('common.retry')">
        <RefreshCw class="w-4 h-4" :class="loading && 'animate-spin'" />
      </button>
    </div>

    <!-- 过滤 -->
    <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 mb-4">
      <input v-model="filterAction" :placeholder="`${t('admin.action')} (email.send)`"
        class="px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-sm text-gray-900 dark:text-white" />
      <select v-model="filterStatus"
        class="px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-sm text-gray-900 dark:text-white">
        <option value="">{{ t('admin.status') }}: all</option>
        <option value="success">success</option>
        <option value="failure">failure</option>
      </select>
      <input v-model="filterUserId" type="number" min="1" :placeholder="`${t('admin.user')} ID`"
        class="px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-sm text-gray-900 dark:text-white" />
      <button @click="applyFilters"
        class="px-3 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
        {{ t('common.search') }}
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-10 text-gray-400">
      <Loader2 class="w-5 h-5 animate-spin mr-2" /> {{ t('common.loading') }}
    </div>
    <div v-else-if="error" class="text-center py-8 text-red-500 text-sm">{{ error }}</div>
    <div v-else-if="items.length === 0" class="text-center py-8 text-gray-400 text-sm">
      {{ t('admin.auditEmpty') }}
    </div>
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-gray-500 border-b border-gray-100 dark:border-gray-800">
            <th class="py-2 pr-3">{{ t('admin.time') }}</th>
            <th class="py-2 pr-3">{{ t('admin.action') }}</th>
            <th class="py-2 pr-3">{{ t('admin.user') }}</th>
            <th class="py-2 pr-3">{{ t('admin.resource') }}</th>
            <th class="py-2 pr-3">{{ t('admin.ip') }}</th>
            <th class="py-2">{{ t('admin.status') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="row.id"
            class="border-b border-gray-50 dark:border-gray-800/60 hover:bg-gray-50 dark:hover:bg-gray-800/40">
            <td class="py-2 pr-3 text-gray-500 whitespace-nowrap">{{ formatTime(row.created_at) }}</td>
            <td class="py-2 pr-3 font-mono text-xs">{{ row.action }}</td>
            <td class="py-2 pr-3">#{{ row.user_id ?? '-' }} <span class="text-xs text-gray-400">{{ row.actor_type }}</span></td>
            <td class="py-2 pr-3 text-xs text-gray-500">
              {{ row.resource_type }}<template v-if="row.resource_id">:{{ row.resource_id }}</template>
            </td>
            <td class="py-2 pr-3 text-xs text-gray-500">{{ row.ip_address || '-' }}</td>
            <td class="py-2">
              <span class="px-1.5 py-0.5 rounded text-xs" :class="statusClass(row.status)">{{ row.status }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 text-sm">
      <button @click="page = Math.max(1, page - 1); load()" :disabled="page <= 1"
        class="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-40">
        ←
      </button>
      <span class="text-gray-500">{{ page }} / {{ totalPages }}</span>
      <button @click="page = Math.min(totalPages, page + 1); load()" :disabled="page >= totalPages"
        class="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg disabled:opacity-40">
        →
      </button>
    </div>
  </div>
</template>
