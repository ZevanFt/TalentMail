<script setup lang="ts">
import { Key, Shield, Trash2, Loader2, Copy, Check, AlertCircle, Download, Upload } from 'lucide-vue-next'

const { getMyPgpKey, uploadMyPgpKey, deleteMyPgpKey, getMe } = useApi()
const { generateKeyPair, clearLocalKeys, hasLocalPrivateKey, exportPrivateKey, importPrivateKey, getLocalFingerprint } = usePGP()
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()

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
    toast.error('请输入密码短语')
    return
  }
  if (generateForm.passphrase !== generateForm.confirmPassphrase) {
    toast.error('两次输入的密码不一致')
    return
  }
  if (generateForm.passphrase.length < 8) {
    toast.error('密码短语至少 8 个字符')
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
    toast.success('密钥对已生成并保存')
    await loadKeyInfo()
  } catch (e: any) {
    console.error('生成密钥失败', e)
    toast.error(e.data?.detail || '生成密钥失败')
  } finally {
    generating.value = false
  }
}

const handleDeleteKey = async () => {
  const ok = await confirmDialog({ message: '确定删除 PGP 密钥？删除后加密邮件将无法解密！', type: 'danger' })
  if (!ok) return
  try {
    await deleteMyPgpKey()
    clearLocalKeys()
    toast.success('密钥已删除')
    await loadKeyInfo()
  } catch (e: any) {
    toast.error(e.data?.detail || '删除失败')
  }
}

const copyPublicKey = async () => {
  if (!keyInfo.value?.public_key) return
  try {
    await navigator.clipboard.writeText(keyInfo.value.public_key)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch {
    toast.error('复制失败')
  }
}

const downloadPrivateKey = () => {
  const key = exportPrivateKey()
  if (!key) {
    toast.error('未找到本地私钥')
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
  toast.success('私钥已下载，请妥善保管！')
}

const handleImportPrivateKey = async () => {
  if (!importForm.privateKey.trim() || !importForm.passphrase) {
    toast.error('请输入私钥和密码')
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
    toast.success('私钥已导入')
    await loadKeyInfo()
  } catch (e: any) {
    toast.error('私钥格式无效或密码错误')
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
      <h2 class="text-lg font-bold text-gray-900 dark:text-white">端到端加密 (PGP)</h2>
      <p class="text-sm text-gray-500 mt-1">使用 PGP 加密保护邮件隐私。密钥对在浏览器本地生成，私钥不会上传到服务器。</p>
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
            <div class="font-medium text-gray-900 dark:text-white">PGP 加密已启用</div>
            <div class="text-xs text-gray-500">指纹: {{ keyInfo.fingerprint }}</div>
          </div>
        </div>

        <!-- 本地私钥状态 -->
        <div class="flex items-center gap-2 text-sm" :class="hasLocalPrivateKey ? 'text-green-600' : 'text-amber-500'">
          <Key class="w-4 h-4" />
          <span v-if="hasLocalPrivateKey">本地私钥可用（可解密邮件）</span>
          <span v-else>本地未找到私钥（无法解密邮件，请导入私钥）</span>
        </div>

        <div class="text-xs text-gray-400">
          公钥上传时间: {{ formatDate(keyInfo.created_at) }}
        </div>

        <!-- 操作按钮 -->
        <div class="flex flex-wrap gap-2">
          <button @click="copyPublicKey" class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <Check v-if="copied" class="w-4 h-4 text-green-500" />
            <Copy v-else class="w-4 h-4" />
            复制公钥
          </button>
          <button v-if="hasLocalPrivateKey" @click="downloadPrivateKey" class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <Download class="w-4 h-4" /> 导出私钥
          </button>
          <button v-if="!hasLocalPrivateKey" @click="showImportModal = true; importForm.privateKey = ''; importForm.passphrase = ''"
            class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap border border-primary text-primary rounded-lg hover:bg-primary/5 transition-colors">
            <Upload class="w-4 h-4" /> 导入私钥
          </button>
          <button @click="handleDeleteKey" class="flex items-center gap-1.5 px-3 py-1.5 text-sm whitespace-nowrap text-red-500 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            <Trash2 class="w-4 h-4" /> 删除密钥
          </button>
        </div>
      </div>

      <!-- 无公钥 -->
      <div v-else class="bg-white dark:bg-bg-panelDark rounded-xl p-6 border border-gray-200 dark:border-border-dark text-center">
        <Shield class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
        <p class="text-lg font-medium text-gray-900 dark:text-white mb-1">尚未设置 PGP 加密</p>
        <p class="text-sm text-gray-500 mb-4">生成密钥对后，可以加密发送和接收邮件</p>
        <button @click="showGenerateModal = true; generateForm.passphrase = ''; generateForm.confirmPassphrase = ''"
          class="px-5 py-2.5 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
          生成密钥对
        </button>
      </div>

      <!-- 使用说明 -->
      <div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800/30">
        <div class="flex items-start gap-3">
          <AlertCircle class="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
          <div class="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <p class="font-medium">关于 PGP 加密</p>
            <ul class="list-disc list-inside space-y-0.5 text-xs">
              <li>密钥对在浏览器中生成，私钥仅存储在本地 localStorage</li>
              <li>发送加密邮件需要收件人的公钥（平台内自动查找）</li>
              <li>更换浏览器或清除数据后需要重新导入私钥</li>
              <li>建议生成后立即导出并安全备份私钥</li>
            </ul>
          </div>
        </div>
      </div>
    </template>

    <!-- 生成密钥弹窗 -->
    <CommonModal v-model="showGenerateModal" title="生成 PGP 密钥对" width-class="w-full max-w-md">
      <div class="space-y-4">
        <p class="text-sm text-gray-500">设置一个密码短语来保护您的私钥。此密码不同于账户密码，请牢记。</p>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">密码短语</label>
          <input v-model="generateForm.passphrase" type="password" placeholder="至少 8 个字符"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">确认密码</label>
          <input v-model="generateForm.confirmPassphrase" type="password" placeholder="再次输入"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm"
            @keyup.enter="handleGenerate" />
        </div>
      </div>
      <template #footer>
        <button @click="showGenerateModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">取消</button>
        <button @click="handleGenerate" :disabled="generating"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="generating" class="w-4 h-4 animate-spin" />
          {{ generating ? '生成中...' : '生成密钥' }}
        </button>
      </template>
    </CommonModal>

    <!-- 导入私钥弹窗 -->
    <CommonModal v-model="showImportModal" title="导入私钥" width-class="w-full max-w-lg">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">私钥（ASCII Armor 格式）</label>
          <textarea v-model="importForm.privateKey" rows="6" placeholder="-----BEGIN PGP PRIVATE KEY BLOCK-----..."
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm font-mono resize-y"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">密码短语</label>
          <input v-model="importForm.passphrase" type="password" placeholder="私钥的密码短语"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm" />
        </div>
      </div>
      <template #footer>
        <button @click="showImportModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm">取消</button>
        <button @click="handleImportPrivateKey" :disabled="importing"
          class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="importing" class="w-4 h-4 animate-spin" />
          {{ importing ? '验证中...' : '导入' }}
        </button>
      </template>
    </CommonModal>
  </div>
</template>
