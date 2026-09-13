<script setup lang="ts">
/**
 * API 密钥管理设置页
 */
import { Key, Plus, Trash2, Copy, Clock, Shield, Eye, EyeOff, AlertTriangle } from 'lucide-vue-next'

const { getApiKeys, createApiKey, revokeApiKey, getApiKeyAuditLogs } = useApi()
const toast = useToast()
const { t } = useI18n()

interface ApiKey {
  id: number
  key_prefix: string
  scopes: string[]
  description: string | null
  rate_limit_per_minute: number
  created_at: string
  updated_at: string
  expires_at: string | null
  revoked_at: string | null
  last_used_at: string | null
}

interface AuditLog {
  id: number
  api_key_id: number
  method: string
  path: string
  ip_address: string
  status_code: number
  decision: string
  created_at: string
}

const scopeGroupNames = computed(() => ({
  tempMailbox: t('adminTools.apiKeys.scopeGroups.tempMailbox'),
  mail: t('adminTools.apiKeys.scopeGroups.mail'),
  system: t('adminTools.apiKeys.scopeGroups.system'),
}))

const AVAILABLE_SCOPES = computed(() => [
  { value: 'temp_mailbox:create', label: t('adminTools.apiKeys.scopes.createTempMailbox'), group: scopeGroupNames.value.tempMailbox },
  { value: 'temp_mailbox:read', label: t('adminTools.apiKeys.scopes.readTempMailboxes'), group: scopeGroupNames.value.tempMailbox },
  { value: 'temp_mailbox:extend', label: t('adminTools.apiKeys.scopes.extendMailbox'), group: scopeGroupNames.value.tempMailbox },
  { value: 'temp_mailbox:restore', label: t('adminTools.apiKeys.scopes.restoreMailbox'), group: scopeGroupNames.value.tempMailbox },
  { value: 'temp_email:read', label: t('adminTools.apiKeys.scopes.readMail'), group: scopeGroupNames.value.mail },
  { value: 'temp_code:read', label: t('adminTools.apiKeys.scopes.readCodes'), group: scopeGroupNames.value.mail },
  { value: 'system_email:send', label: t('adminTools.apiKeys.scopes.sendSystemEmail'), group: scopeGroupNames.value.system },
])

const loading = ref(true)
const apiKeys = ref<ApiKey[]>([])
const total = ref(0)

// 创建弹窗
const showCreateModal = ref(false)
const createForm = reactive({
  description: '',
  scopes: [] as string[],
  expires_in_days: 90,
  rate_limit_per_minute: 60,
})
const creating = ref(false)

// 一次性显示密钥
const showKeyResult = ref(false)
const createdKeyValue = ref('')
const keyCopied = ref(false)

// 审计日志
const showAuditModal = ref(false)
const auditKeyId = ref<number | null>(null)
const auditLogs = ref<AuditLog[]>([])
const auditLoading = ref(false)

const loadApiKeys = async () => {
  loading.value = true
  try {
    const res = await getApiKeys()
    apiKeys.value = res.items || []
    total.value = res.total ?? apiKeys.value.length
  } catch (e: any) {
    toast.error(e.data?.detail || t('adminTools.apiKeys.loadKeysFailed'))
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  createForm.description = ''
  createForm.scopes = []
  createForm.expires_in_days = 90
  createForm.rate_limit_per_minute = 60
  showCreateModal.value = true
}

const handleCreate = async () => {
  if (createForm.scopes.length === 0) {
    toast.error(t('adminTools.apiKeys.selectScopeRequired'))
    return
  }
  creating.value = true
  try {
    const res = await createApiKey({
      description: createForm.description || undefined,
      scopes: createForm.scopes,
      expires_in_days: createForm.expires_in_days,
      rate_limit_per_minute: createForm.rate_limit_per_minute,
    })
    createdKeyValue.value = res.api_key
    keyCopied.value = false
    showCreateModal.value = false
    showKeyResult.value = true
    await loadApiKeys()
  } catch (e: any) {
    toast.error(e.data?.detail || t('adminTools.apiKeys.createFailed'))
  } finally {
    creating.value = false
  }
}

const copyKey = async () => {
  try {
    await navigator.clipboard.writeText(createdKeyValue.value)
    keyCopied.value = true
    toast.success(t('adminTools.apiKeys.copiedToClipboard'))
  } catch {
    toast.error(t('adminTools.apiKeys.copyFailed'))
  }
}

const handleRevoke = async (key: ApiKey) => {
  if (!confirm(t('adminTools.apiKeys.revokeConfirm', { prefix: key.key_prefix }))) return
  try {
    await revokeApiKey(key.id)
    toast.success(t('adminTools.apiKeys.revokedToast'))
    await loadApiKeys()
  } catch (e: any) {
    toast.error(e.data?.detail || t('adminTools.apiKeys.revokeFailed'))
  }
}

const openAuditLogs = async (key: ApiKey) => {
  auditKeyId.value = key.id
  showAuditModal.value = true
  auditLoading.value = true
  try {
    auditLogs.value = await getApiKeyAuditLogs(key.id)
  } catch (e: any) {
    toast.error(e.data?.detail || t('adminTools.apiKeys.loadAuditFailed'))
    auditLogs.value = []
  } finally {
    auditLoading.value = false
  }
}

const isRevoked = (key: ApiKey) => !!key.revoked_at
const isExpired = (key: ApiKey) => key.expires_at && new Date(key.expires_at) < new Date()

const formatDate = (str: string | null) => {
  if (!str) return '-'
  return new Date(str).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const scopeLabel = (scope: string) => {
  const found = AVAILABLE_SCOPES.value.find(s => s.value === scope)
  return found ? found.label : scope
}

const statusBadge = (key: ApiKey) => {
  if (isRevoked(key)) return { text: t('adminTools.apiKeys.status.revoked'), class: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' }
  if (isExpired(key)) return { text: t('adminTools.apiKeys.status.expired'), class: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400' }
  return { text: t('adminTools.apiKeys.status.active'), class: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' }
}

onMounted(loadApiKeys)
</script>

<template>
  <div class="space-y-6">
    <!-- 标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('adminTools.apiKeys.title') }}</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ t('adminTools.apiKeys.subtitle') }}</p>
      </div>
      <button @click="openCreate" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors whitespace-nowrap">
        <Plus class="w-4 h-4" /> {{ t('adminTools.apiKeys.createKey') }}
      </button>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 2" :key="i" class="p-4 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark">
        <div class="flex items-center gap-3">
          <div class="h-5 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
          <div class="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        </div>
        <div class="mt-3 flex gap-2">
          <div v-for="j in 3" :key="j" class="h-6 w-20 bg-gray-100 dark:bg-gray-800 rounded animate-pulse"></div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="apiKeys.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
      <Key class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
      <p class="text-gray-500 dark:text-gray-400 mb-2">{{ t('adminTools.apiKeys.emptyTitle') }}</p>
      <p class="text-sm text-gray-400 dark:text-gray-500 mb-6">{{ t('adminTools.apiKeys.emptySubtitle') }}</p>
      <button @click="openCreate" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
        <Plus class="w-4 h-4" /> {{ t('adminTools.apiKeys.createFirstKey') }}
      </button>
    </div>

    <!-- 密钥列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="key in apiKeys"
        :key="key.id"
        class="p-4 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark transition-colors"
        :class="{ 'opacity-60': isRevoked(key) || isExpired(key) }"
      >
        <!-- 头部 -->
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2 flex-wrap">
            <code class="text-sm font-mono text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">{{ key.key_prefix }}...</code>
            <span :class="['px-2 py-0.5 text-xs rounded-full whitespace-nowrap', statusBadge(key).class]">
              {{ statusBadge(key).text }}
            </span>
            <span v-if="key.description" class="text-sm text-gray-500 dark:text-gray-400">{{ key.description }}</span>
          </div>
          <div class="flex items-center gap-1">
            <button
              @click="openAuditLogs(key)"
              class="p-1.5 text-gray-400 hover:text-primary rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              :title="t('adminTools.apiKeys.auditLog')"
            >
              <Eye class="w-4 h-4" />
            </button>
            <button
              v-if="!isRevoked(key)"
              @click="handleRevoke(key)"
              class="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              :title="t('adminTools.apiKeys.revoke')"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Scope 标签 -->
        <div class="flex flex-wrap gap-1.5 mb-2">
          <span
            v-for="scope in key.scopes"
            :key="scope"
            class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs rounded whitespace-nowrap"
          >{{ scopeLabel(scope) }}</span>
        </div>

        <!-- 元信息 -->
        <div class="flex flex-wrap gap-4 text-xs text-gray-400">
          <span><Clock class="w-3 h-3 inline mr-1" />{{ t('adminTools.apiKeys.createdAt') }}: {{ formatDate(key.created_at) }}</span>
          <span v-if="key.expires_at"><Shield class="w-3 h-3 inline mr-1" />{{ t('adminTools.apiKeys.expiresAt') }}: {{ formatDate(key.expires_at) }}</span>
          <span v-if="key.last_used_at">{{ t('adminTools.apiKeys.lastUsed') }}: {{ formatDate(key.last_used_at) }}</span>
          <span>{{ t('adminTools.apiKeys.rateLimit') }}: {{ key.rate_limit_per_minute }}/min</span>
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <CommonModal v-model="showCreateModal" :title="t('adminTools.apiKeys.createModalTitle')" max-width="lg">
      <div class="space-y-4">
        <!-- 描述 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('adminTools.apiKeys.descriptionOptional') }}</label>
          <input
            v-model="createForm.description"
            type="text"
            maxlength="255"
            :placeholder="t('adminTools.apiKeys.descriptionPlaceholder')"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <!-- 权限范围 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{{ t('adminTools.apiKeys.scopesLabel') }} <span class="text-red-500">*</span></label>
          <div class="space-y-3">
            <div v-for="group in scopeGroupNames" :key="group">
              <div class="text-xs font-medium text-gray-400 mb-1">{{ group }}</div>
              <div class="space-y-1.5">
                <label
                  v-for="scope in AVAILABLE_SCOPES.filter(s => s.group === group)"
                  :key="scope.value"
                  class="flex items-center gap-2 cursor-pointer"
                >
                  <input type="checkbox" v-model="createForm.scopes" :value="scope.value" class="rounded border-gray-300 text-primary focus:ring-primary" />
                  <span class="text-sm text-gray-700 dark:text-gray-300">{{ scope.label }}</span>
                  <code class="text-xs text-gray-400">{{ scope.value }}</code>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 过期天数 & 限速 -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('adminTools.apiKeys.expiresInDays') }}</label>
            <input
              v-model.number="createForm.expires_in_days"
              type="number"
              min="1"
              max="365"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('adminTools.apiKeys.rateLimitPerMinute') }}</label>
            <input
              v-model.number="createForm.rate_limit_per_minute"
              type="number"
              min="1"
              max="600"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex justify-end gap-3 pt-2">
          <button @click="showCreateModal = false" class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            {{ t('adminTools.common.cancel') }}
          </button>
          <button @click="handleCreate" :disabled="creating" class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 whitespace-nowrap">
            {{ creating ? t('adminTools.common.saving') : t('adminTools.apiKeys.createKey') }}
          </button>
        </div>
      </div>
    </CommonModal>

    <!-- 密钥展示弹窗（一次性） -->
    <CommonModal v-model="showKeyResult" :title="t('adminTools.apiKeys.keyCreatedTitle')" max-width="md" :closeable="keyCopied">
      <div class="space-y-4">
        <div class="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <AlertTriangle class="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
          <div class="text-sm text-yellow-700 dark:text-yellow-400">
            <p class="font-medium">{{ t('adminTools.apiKeys.saveKeyWarning') }}</p>
            <p class="mt-1">{{ t('adminTools.apiKeys.saveKeyWarningDetail') }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <code class="flex-1 text-sm font-mono text-gray-900 dark:text-white break-all select-all">{{ createdKeyValue }}</code>
          <button
            @click="copyKey"
            class="p-2 shrink-0 text-gray-500 hover:text-primary rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            :title="keyCopied ? t('adminTools.common.copied') : t('adminTools.common.copy')"
          >
            <Copy class="w-4 h-4" />
          </button>
        </div>

        <div class="flex justify-end">
          <button
            @click="showKeyResult = false"
            :class="['px-4 py-2 text-sm rounded-lg transition-colors whitespace-nowrap', keyCopied ? 'bg-primary text-white hover:bg-primary-hover' : 'border border-gray-200 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800']"
          >{{ keyCopied ? t('adminTools.apiKeys.done') : t('adminTools.apiKeys.iSavedKey') }}</button>
        </div>
      </div>
    </CommonModal>

    <!-- 审计日志弹窗 -->
    <CommonModal v-model="showAuditModal" :title="t('adminTools.apiKeys.auditModalTitle')" max-width="xl">
      <div v-if="auditLoading" class="py-8 text-center text-gray-400">{{ t('adminTools.common.loading') }}</div>
      <div v-else-if="auditLogs.length === 0" class="py-8 text-center text-gray-400">{{ t('adminTools.apiKeys.noCallRecords') }}</div>
      <div v-else class="max-h-[400px] overflow-y-auto">
        <table class="w-full text-sm">
          <thead class="sticky top-0 bg-white dark:bg-bg-panelDark">
            <tr class="text-left text-xs text-gray-400 border-b border-gray-100 dark:border-gray-800">
              <th class="py-2 px-2">{{ t('adminTools.apiKeys.colTime') }}</th>
              <th class="py-2 px-2">{{ t('adminTools.apiKeys.colMethod') }}</th>
              <th class="py-2 px-2">{{ t('adminTools.apiKeys.colPath') }}</th>
              <th class="py-2 px-2">IP</th>
              <th class="py-2 px-2">{{ t('adminTools.apiKeys.colStatus') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in auditLogs" :key="log.id" class="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30">
              <td class="py-1.5 px-2 text-xs text-gray-500 whitespace-nowrap">{{ formatDate(log.created_at) }}</td>
              <td class="py-1.5 px-2">
                <code class="text-xs px-1.5 py-0.5 rounded whitespace-nowrap" :class="log.method === 'GET' ? 'bg-green-100 dark:bg-green-900/30 text-green-600' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600'">{{ log.method }}</code>
              </td>
              <td class="py-1.5 px-2 text-xs text-gray-700 dark:text-gray-300 font-mono truncate max-w-[200px]">{{ log.path }}</td>
              <td class="py-1.5 px-2 text-xs text-gray-400 whitespace-nowrap">{{ log.ip_address }}</td>
              <td class="py-1.5 px-2">
                <span class="text-xs whitespace-nowrap" :class="log.status_code < 400 ? 'text-green-500' : 'text-red-500'">{{ log.status_code }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </CommonModal>
  </div>
</template>
