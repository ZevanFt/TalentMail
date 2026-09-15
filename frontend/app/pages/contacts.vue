<script setup lang="ts">
import { Search, Plus, Pencil, Trash2, User, Loader2, AlertCircle, Download, Upload, ChevronDown } from 'lucide-vue-next'
const config = useConfig()
const { t } = useI18n()
useHead({ title: computed(() => `${t('contacts.title')} - ${config.appName}`) })
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { getContacts, createContact, updateContact, deleteContact, exportContactsUrl, importContacts } = useApi()

interface Contact { id: number; name: string | null; email: string | null; phone: string | null; notes: string | null }
const contacts = ref<Contact[]>([])
const searchQuery = ref('')
const showModal = ref(false)
const editingContact = ref<Contact | null>(null)
const form = reactive({ name: '', email: '', phone: '', notes: '' })
const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const deletingId = ref<number | null>(null)

// 表单验证
const formErrors = reactive({ name: '', email: '' })
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const validateForm = (): boolean => {
  formErrors.name = ''
  formErrors.email = ''
  let valid = true
  if (!form.name.trim()) {
    formErrors.name = t('contacts.nameRequired')
    valid = false
  }
  if (!form.email.trim()) {
    formErrors.email = t('contacts.emailRequired')
    valid = false
  } else if (!emailRegex.test(form.email.trim())) {
    formErrors.email = t('contacts.emailInvalid')
    valid = false
  }
  return valid
}

const clearErrors = () => {
  formErrors.name = ''
  formErrors.email = ''
}

const loadContacts = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getContacts(searchQuery.value || undefined)
    contacts.value = res.items || res as any
  } catch (e: any) {
    console.error('加载联系人失败', e)
    loadError.value = e.data?.detail || t('contacts.loadFailed')
    toast.error(loadError.value)
  } finally { loading.value = false }
}

const openModal = (contact?: Contact) => {
  editingContact.value = contact || null
  form.name = contact?.name || ''
  form.email = contact?.email || ''
  form.phone = contact?.phone || ''
  form.notes = contact?.notes || ''
  clearErrors()
  showModal.value = true
}

const save = async () => {
  if (!validateForm()) return
  saving.value = true
  try {
    if (editingContact.value) {
      await updateContact(editingContact.value.id, form)
    } else {
      await createContact(form)
    }
    showModal.value = false
    toast.success(editingContact.value ? t('contacts.updated') : t('contacts.added'))
    await loadContacts()
  } catch (e: any) {
    console.error('保存联系人失败', e)
    toast.error(e.data?.detail || t('contacts.saveFailed'))
  } finally { saving.value = false }
}

const remove = async (id: number) => {
  const ok = await confirmDialog({ message: t('contacts.confirmDelete'), type: 'danger' })
  if (!ok) return
  deletingId.value = id
  try {
    await deleteContact(id)
    contacts.value = contacts.value.filter(c => c.id !== id)
    toast.success(t('contacts.deleted'))
  } catch (e: any) {
    console.error('删除联系人失败', e)
    toast.error(e.data?.detail || t('contacts.deleteFailed'))
  } finally { deletingId.value = null }
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadContacts, 300)
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})

// ========== 导入/导出 ==========
const showExportMenu = ref(false)
const importing = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const handleExport = (format: 'csv' | 'vcf') => {
  showExportMenu.value = false
  const token = useCookie('token')
  const url = exportContactsUrl(format)
  // 用 fetch 方式下载（带 Authorization header）
  fetch(url, {
    headers: { Authorization: `Bearer ${token.value}` }
  }).then(res => {
    if (!res.ok) throw new Error(t('contacts.exportFailed'))
    return res.blob()
  }).then(blob => {
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = format === 'csv' ? 'contacts.csv' : 'contacts.vcf'
    a.click()
    URL.revokeObjectURL(blobUrl)
    toast.success(t('contacts.exportSuccess'))
  }).catch((e: any) => {
    console.error('导出失败', e)
    toast.error(t('contacts.exportFailed'))
  })
}

const triggerImport = () => {
  fileInputRef.value?.click()
}

const handleImportFile = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  // 验证文件类型
  const validTypes = ['.csv', '.vcf', '.vcard']
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!validTypes.includes(ext)) {
    toast.error(t('contacts.importTypeHint'))
    target.value = ''
    return
  }
  if (file.size > 1048576) {
    toast.error(t('contacts.importTooLarge'))
    target.value = ''
    return
  }
  importing.value = true
  try {
    const res = await importContacts(file)
    const msgs: string[] = []
    if (res.imported > 0) msgs.push(t('contacts.imported', { n: res.imported }))
    if (res.skipped > 0) msgs.push(t('contacts.skipped', { n: res.skipped }))
    if (res.errors?.length > 0) msgs.push(t('contacts.errorCount', { n: res.errors.length }))
    toast.success(msgs.join(t('contacts.listSeparator')) || t('contacts.importDone'))
    await loadContacts()
  } catch (e: any) {
    console.error('导入失败', e)
    toast.error(e.data?.detail || t('contacts.importFailed'))
  } finally {
    importing.value = false
    target.value = ''
  }
}

// 点击外部关闭导出菜单
const exportMenuRef = ref<HTMLDivElement | null>(null)
const onClickOutside = (e: MouseEvent) => {
  if (exportMenuRef.value && !exportMenuRef.value.contains(e.target as Node)) {
    showExportMenu.value = false
  }
}
watch(showExportMenu, (v) => {
  if (v) {
    setTimeout(() => document.addEventListener('click', onClickOutside), 0)
  } else {
    document.removeEventListener('click', onClickOutside)
  }
})

onMounted(loadContacts)
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50 dark:bg-bg-dark">
    <header class="flex items-center justify-between px-4 lg:px-6 py-4 border-b border-gray-200 dark:border-border-dark bg-white dark:bg-bg-panelDark">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('contacts.title') }}</h1>
      <div class="flex items-center gap-3">
        <div class="relative hidden sm:block">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input v-model="searchQuery" :placeholder="t('contacts.searchPlaceholder')"
            class="pl-9 pr-4 py-2 w-64 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
        </div>
        <!-- 导入按钮 -->
        <button @click="triggerImport" :disabled="importing"
          class="hidden sm:flex items-center gap-1.5 px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm text-gray-600 dark:text-gray-300 disabled:opacity-50">
          <Loader2 v-if="importing" class="w-4 h-4 animate-spin" />
          <Upload v-else class="w-4 h-4" />
          {{ t('contacts.import') }}
        </button>
        <input ref="fileInputRef" type="file" accept=".csv,.vcf,.vcard" class="hidden" @change="handleImportFile" />

        <!-- 导出下拉 -->
        <div ref="exportMenuRef" class="relative hidden sm:block">
          <button @click="showExportMenu = !showExportMenu"
            class="flex items-center gap-1.5 px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm text-gray-600 dark:text-gray-300">
            <Download class="w-4 h-4" />
            {{ t('contacts.export') }}
            <ChevronDown class="w-3 h-3" />
          </button>
          <Transition enter-active-class="transition duration-100 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
            leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
            <div v-if="showExportMenu" class="absolute right-0 mt-1 w-36 bg-white dark:bg-bg-panelDark border border-gray-200 dark:border-border-dark rounded-lg shadow-lg z-50 py-1">
              <button @click="handleExport('csv')" class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">CSV</button>
              <button @click="handleExport('vcf')" class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">vCard</button>
            </div>
          </Transition>
        </div>

        <button @click="openModal()" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium">
          <Plus class="w-4 h-4" /> {{ t('contacts.new') }}
        </button>
      </div>
    </header>

    <!-- 移动端搜索 -->
    <div class="sm:hidden px-4 py-3 bg-white dark:bg-bg-panelDark border-b border-gray-200 dark:border-border-dark">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input v-model="searchQuery" :placeholder="t('contacts.searchPlaceholder')"
          class="w-full pl-9 pr-4 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-gray-50 dark:bg-bg-dark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
      </div>
    </div>

    <div class="flex-1 overflow-auto p-4 lg:p-6">
      <!-- 加载骨架屏 -->
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 6" :key="i" class="bg-white dark:bg-bg-panelDark rounded-xl p-4 border border-gray-200 dark:border-border-dark animate-pulse">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700" />
            <div class="flex-1 space-y-2">
              <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24" />
              <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-36" />
            </div>
          </div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-28 mt-2" />
        </div>
      </div>

      <!-- 错误态 -->
      <div v-else-if="loadError" class="text-center py-12">
        <AlertCircle class="w-12 h-12 mx-auto mb-3 text-red-400 opacity-60" />
        <p class="text-red-500 mb-3">{{ loadError }}</p>
        <button @click="loadContacts" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">{{ t('contacts.retry') }}</button>
      </div>

      <!-- 空态 -->
      <div v-else-if="contacts.length === 0" class="text-center py-12 text-gray-500">
        <User class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p class="text-lg font-medium mb-1">{{ searchQuery ? t('contacts.noMatch') : t('contacts.empty') }}</p>
        <p class="text-sm text-gray-400">{{ searchQuery ? t('contacts.noMatchHint') : t('contacts.emptyHint') }}</p>
      </div>

      <!-- 联系人列表 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="c in contacts" :key="c.id"
          class="bg-white dark:bg-bg-panelDark rounded-xl p-4 shadow-sm border border-gray-200 dark:border-border-dark hover:shadow-md transition-shadow">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <span class="text-primary font-bold">{{ (c.name || '?').charAt(0).toUpperCase() }}</span>
              </div>
              <div class="min-w-0">
                <div class="font-medium text-gray-900 dark:text-white truncate">{{ c.name }}</div>
                <div class="text-sm text-gray-500 truncate">{{ c.email }}</div>
              </div>
            </div>
            <div class="flex gap-1 shrink-0">
              <button @click="openModal(c)" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors" :title="t('contacts.edit')">
                <Pencil class="w-4 h-4" />
              </button>
              <button @click="remove(c.id)" :disabled="deletingId === c.id"
                class="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-400 hover:text-red-500 transition-colors disabled:opacity-50" :title="t('common.delete')">
                <Loader2 v-if="deletingId === c.id" class="w-4 h-4 animate-spin" />
                <Trash2 v-else class="w-4 h-4" />
              </button>
            </div>
          </div>
          <div v-if="c.phone" class="mt-2 text-sm text-gray-500 dark:text-gray-400">{{ c.phone }}</div>
          <div v-if="c.notes" class="mt-1 text-sm text-gray-400 dark:text-gray-500 truncate">{{ c.notes }}</div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑 Modal -->
    <CommonModal v-model="showModal" :title="editingContact ? t('contacts.edit') : t('contacts.new')">
      <div class="space-y-4">
        <div>
          <label for="contact-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('contacts.name') }} <span class="text-red-500">*</span></label>
          <input id="contact-name" v-model="form.name" :placeholder="t('contacts.namePlaceholder')"
            :class="['w-full px-3 py-2 border rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all', formErrors.name ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-border-dark']"
            @input="formErrors.name = ''" />
          <span v-if="formErrors.name" class="text-red-500 text-xs mt-1 block">{{ formErrors.name }}</span>
        </div>
        <div>
          <label for="contact-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('contacts.email') }} <span class="text-red-500">*</span></label>
          <input id="contact-email" v-model="form.email" type="email" :placeholder="t('contacts.emailPlaceholder')"
            :class="['w-full px-3 py-2 border rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all', formErrors.email ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-border-dark']"
            @input="formErrors.email = ''" />
          <span v-if="formErrors.email" class="text-red-500 text-xs mt-1 block">{{ formErrors.email }}</span>
        </div>
        <div>
          <label for="contact-phone" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('contacts.phone') }}</label>
          <input id="contact-phone" v-model="form.phone" :placeholder="t('contacts.phonePlaceholder')"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
        </div>
        <div>
          <label for="contact-notes" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('contacts.notes') }}</label>
          <textarea id="contact-notes" v-model="form.notes" :placeholder="t('contacts.notesPlaceholder')" rows="2"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"></textarea>
        </div>
      </div>
      <template #footer>
        <button @click="showModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-sm">{{ t('common.cancel') }}</button>
        <button @click="save" :disabled="saving"
          class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          {{ saving ? t('contacts.saving') : t('common.save') }}
        </button>
      </template>
    </CommonModal>
  </div>
</template>
