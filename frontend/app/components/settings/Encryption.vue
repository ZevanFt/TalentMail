<script setup lang="ts">
import { Key, Shield, Trash2, Loader2, Copy, Check, AlertCircle, Download, Upload } from 'lucide-vue-next'

const { getMyPgpKey, uploadMyPgpKey, deleteMyPgpKey, getMe } = useApi()
const { generateKeyPair, clearLocalKeys, hasLocalPrivateKey, exportPrivateKey, importPrivateKey, getLocalFingerprint } = usePGP()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { t } = useI18n()

const loading = ref(true)
const keyInfo = ref<{ has_key: boolean; fingerprint: string | null; created_at: string | null; public_key: string | null } | null>(null)
const localFingerprint = ref<string | null>(null)

// 生成密钥
const showGenerateModal = ref(false)
const generateForm = reactive({ passphrase: '', confirmPassphrase: '' })
const generating = ref(false)

// 导入私钥
const showImportModal = ref(false)
const importForm = reactive({ privateKey: '', passphrase: '' })
const importing = ref(false)

const copied = ref(false)

const loadKeyInfo = async () => {
  loading.value = true
  try {
    keyInfo.value = await getMyPgpKey()
    localFingerprint.value = await getLocalFingerprint()
  } catch (e: any) {
    console.error('加载密钥信息失败', e)
  } finally {
    loading.value = false
  }
}

const handleGenerate = async () => {
  if (!generateForm.passphrase) {
    toast.error(t('settingsSecurity.encryption.passphraseRequired'))
    return
  }
  if (generateForm.passphrase !== generateForm.confirmPassphrase) {
    toast.error(t('settingsSecurity.encryption.passphraseMismatch'))
    return
  }
  if (generateForm.passphrase.length < 8) {
    toast.error(t('settingsSecurity.encryption.passphraseTooShort'))
    return
  }

  generating.value = true
  try {
    const me = await getMe()
    const result = await generateKeyPair(me.display_name || me.email, me.email, generateForm.passphrase)

    // 上传公钥到服务器
    await uploadMyPgpKey(result.publicKey, result.fingerprint)

    showGenerateModal.value = false
    generateForm.passphrase = ''
    generateForm.confirmPassphrase = ''
    toast.success(t('settingsSecurity.encryption.keyGenerated'))
    await loadKeyInfo()
  } catch (e: any) {
    console.error('生成密钥失败', e)
    toast.error(e.data?.detail || t('settingsSecurity.encryption.generateFailed'))
  } finally {
    generating.value = false
  }
}

const handleDeleteKey = async () => {
  const ok = await confirmDialog({ message: t('settingsSecurity.encryption.deleteKeyConfirm'), type: 'danger' })
  if (!ok) return
  try {
    await deleteMyPgpKey()
    clearLocalKeys()
    toast.success(t('settingsSecurity.encryption.keyDeleted'))
    await loadKeyInfo()
  } catch (e: any) {
    toast.error(e.data?.detail || t('settingsSecurity.encryption.deleteFailed'))
  }
}

const copyPublicKey = async () => {
  if (!keyInfo.value?.public_key) return
  try {
    await navigator.clipboard.writeText(keyInfo.value.public_key)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch {
    toast.error(t('settingsSecurity.encryption.copyFailed'))
  }
}

const downloadPrivateKey = () => {
  const key = exportPrivateKey()
  if (!key) {
    toast.error(t('settingsSecurity.encryption.noLocalKey'))
    return
  }
  const blob = new Blob([key], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'talentmail-private-key.asc'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  toast.success(t('settingsSecurity.encryption.privateKeyDownloaded'))
}

const handleImportPrivateKey = async () => {
  if (!importForm.privateKey.trim() || !importForm.passphrase) {
    toast.error(t('settingsSecurity.encryption.importRequired'))
    return
  }
  importing.value = true
  try {
    // 验证私钥格式
    const openpgp = await import('openpgp')
    const privKey = await openpgp.readPrivateKey({ armoredKey: importForm.privateKey.trim() })
    // 验证密码
    await openpgp.decryptKey({ privateKey: privKey, passphrase: importForm.passphrase })

    importPrivateKey(importForm.privateKey.trim(), importForm.passphrase)
    showImportModal.value = false
    importForm.privateKey = ''
    importForm.passphrase = ''
    toast.success(t('settingsSecurity.encryption.keyImported'))
    await loadKeyInfo()
  } catch (e: any) {
    toast.error(t('settingsSecurity.encryption.importInvalid'))
  } finally {
    importing.value = false
  }
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(loadKeyInfo)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h2 class="text-lg font-bold text-gray-900 dark:text-white">{{ t('settingsSecurity.encryption.title') }}</h2>
      <p class="text-sm text-gray-500 mt-1">{{ t('settingsSecurity.encryption.desc') }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div class="bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark animate-pulse">
        <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-3" />
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-72" />
      </div>
    </div>

    <template v-else>
      <!-- 已有公钥 -->
      <div v-if="keyInfo?.has_key" class="bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark space-y-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <Shield class="w-5 h-5 text-green-600" />
          </div>
          <div>
            <div class="font-medium text-gray-900 dark:text-white">{{ t('settingsSecurity.encryption.enabled') }}</div>
            <div class="text-xs text-gray-500">{{ t('settingsSecurity.encryption.fingerprint', { fp: keyInfo.fingerprint }) }}</div>
          </div>
        </div>

        <!-- 本地私钥状态 -->
        <div class="flex items-center gap-2 text-sm" :class="hasLocalPrivateKey ? 'text-green-600' : 'text-amber-500'">
          <Key class="w-4 h-4" />
          <span v-if="hasLocalPrivateKey">{{ t('settingsSecurity.encryption.localKeyAvailable') }}</span>
          <span v-else>{{ t('settingsSecurity.encryption.localKeyMissing') }}</span>
        </div>

        <div class="text-xs text-gray-400">
          {{ t('settingsSecurity.encryption.uploadedAt', { date: formatDate(keyInfo.created_at) }) }}
        </div>

        <!-- 操作按钮 -->
        <div class="flex flex-wrap gap-2">
          <button @click="copyPublicKey" class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <Check v-if="copied" class="w-4 h-4 text-green-500" />
            <Copy v-else class="w-4 h-4" />
            {{ t('settingsSecurity.encryption.copyPublicKey') }}
          </button>
          <button v-if="hasLocalPrivateKey" @click="downloadPrivateKey" class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <Download class="w-4 h-4" /> {{ t('settingsSecurity.encryption.exportPrivateKey') }}
          </button>
          <button v-if="!hasLocalPrivateKey" @click="showImportModal = true; importForm.privateKey = ''; importForm.passphrase = ''"
            class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap border border-primary text-primary rounded-lg hover:bg-primary/5 transition-colors">
            <Upload class="w-4 h-4" /> {{ t('settingsSecurity.encryption.importPrivateKey') }}
          </button>
          <button @click="handleDeleteKey" class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap text-red-500 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            <Trash2 class="w-4 h-4" /> {{ t('settingsSecurity.encryption.deleteKey') }}
          </button>
        </div>
      </div>

      <!-- 无公钥 -->
      <div v-else class="bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark text-center">
        <Shield class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
        <p class="text-lg font-medium text-gray-900 dark:text-white mb-1">{{ t('settingsSecurity.encryption.notSetup') }}</p>
        <p class="text-sm text-gray-500 mb-4">{{ t('settingsSecurity.encryption.notSetupDesc') }}</p>
        <button @click="showGenerateModal = true; generateForm.passphrase = ''; generateForm.confirmPassphrase = ''"
          class="px-5 py-2.5 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
          {{ t('settingsSecurity.encryption.generateKeyPair') }}
        </button>
      </div>

      <!-- 使用说明 -->
      <div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800/30">
        <div class="flex items-start gap-3">
          <AlertCircle class="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
          <div class="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <p class="font-medium">{{ t('settingsSecurity.encryption.about') }}</p>
            <ul class="list-disc list-inside space-y-0.5 text-xs">
              <li>{{ t('settingsSecurity.encryption.tip1') }}</li>
              <li>{{ t('settingsSecurity.encryption.tip2') }}</li>
              <li>{{ t('settingsSecurity.encryption.tip3') }}</li>
              <li>{{ t('settingsSecurity.encryption.tip4') }}</li>
            </ul>
          </div>
        </div>
      </div>
    </template>

    <!-- 生成密钥弹窗 -->
    <CommonModal v-model="showGenerateModal" :title="t('settingsSecurity.encryption.generateModalTitle')" width-class="w-full max-w-md">
      <div class="space-y-4">
        <p class="text-sm text-gray-500">{{ t('settingsSecurity.encryption.generateModalDesc') }}</p>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.encryption.passphrase') }}</label>
          <input v-model="generateForm.passphrase" type="password" :placeholder="t('settingsSecurity.encryption.passphrasePlaceholder')"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.encryption.confirmPassphrase') }}</label>
          <input v-model="generateForm.confirmPassphrase" type="password" :placeholder="t('settingsSecurity.encryption.confirmPlaceholder')"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm"
            @keyup.enter="handleGenerate" />
        </div>
      </div>
      <template #footer>
        <button @click="showGenerateModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">{{ t('common.cancel') }}</button>
        <button @click="handleGenerate" :disabled="generating"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="generating" class="w-4 h-4 animate-spin" />
          {{ generating ? t('settingsSecurity.encryption.generating') : t('settingsSecurity.encryption.generateKey') }}
        </button>
      </template>
    </CommonModal>

    <!-- 导入私钥弹窗 -->
    <CommonModal v-model="showImportModal" :title="t('settingsSecurity.encryption.importModalTitle')" width-class="w-full max-w-lg">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.encryption.privateKeyLabel') }}</label>
          <textarea v-model="importForm.privateKey" rows="6" placeholder="-----BEGIN PGP PRIVATE KEY BLOCK-----..."
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm font-mono resize-y"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settingsSecurity.encryption.passphrase') }}</label>
          <input v-model="importForm.passphrase" type="password" :placeholder="t('settingsSecurity.encryption.importPassphrasePlaceholder')"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm" />
        </div>
      </div>
      <template #footer>
        <button @click="showImportModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">{{ t('common.cancel') }}</button>
        <button @click="handleImportPrivateKey" :disabled="importing"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="importing" class="w-4 h-4 animate-spin" />
          {{ importing ? t('settingsSecurity.encryption.verifying') : t('settingsSecurity.encryption.import') }}
        </button>
      </template>
    </CommonModal>
  </div>
</template>
