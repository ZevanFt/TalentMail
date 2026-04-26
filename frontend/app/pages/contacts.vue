<script setup lang="ts">
import { Search, Plus, Pencil, Trash2, User, Loader2, AlertCircle } from 'lucide-vue-next'
useHead({ title: '通讯录 - TalentMail' })
const toast = useToast()
const { confirm: confirmDialog } = useConfirmDialog()
const { getContacts, createContact, updateContact, deleteContact } = useApi()

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
    formErrors.name = '姓名不能为空'
    valid = false
  }
  if (!form.email.trim()) {
    formErrors.email = '邮箱不能为空'
    valid = false
  } else if (!emailRegex.test(form.email.trim())) {
    formErrors.email = '请输入有效的邮箱地址'
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
    loadError.value = e.data?.detail || '加载联系人失败'
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
    toast.success(editingContact.value ? '联系人已更新' : '联系人已添加')
    await loadContacts()
  } catch (e: any) {
    console.error('保存联系人失败', e)
    toast.error(e.data?.detail || '保存失败')
  } finally { saving.value = false }
}

const remove = async (id: number) => {
  const ok = await confirmDialog({ message: '确定删除此联系人？', type: 'danger' })
  if (!ok) return
  deletingId.value = id
  try {
    await deleteContact(id)
    contacts.value = contacts.value.filter(c => c.id !== id)
    toast.success('联系人已删除')
  } catch (e: any) {
    console.error('删除联系人失败', e)
    toast.error(e.data?.detail || '删除失败')
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

onMounted(loadContacts)
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50 dark:bg-bg-dark">
    <header class="flex items-center justify-between px-4 lg:px-6 py-4 border-b border-gray-200 dark:border-border-dark bg-white dark:bg-bg-panelDark">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">通讯录</h1>
      <div class="flex items-center gap-3">
        <div class="relative hidden sm:block">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input v-model="searchQuery" placeholder="搜索联系人..."
            class="pl-9 pr-4 py-2 w-64 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
        </div>
        <button @click="openModal()" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium">
          <Plus class="w-4 h-4" /> 添加联系人
        </button>
      </div>
    </header>

    <!-- 移动端搜索 -->
    <div class="sm:hidden px-4 py-3 bg-white dark:bg-bg-panelDark border-b border-gray-200 dark:border-border-dark">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input v-model="searchQuery" placeholder="搜索联系人..."
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
        <button @click="loadContacts" class="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">重试</button>
      </div>

      <!-- 空态 -->
      <div v-else-if="contacts.length === 0" class="text-center py-12 text-gray-500">
        <User class="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p class="text-lg font-medium mb-1">{{ searchQuery ? '未找到匹配的联系人' : '暂无联系人' }}</p>
        <p class="text-sm text-gray-400">{{ searchQuery ? '试试其他关键词' : '点击上方按钮添加' }}</p>
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
              <button @click="openModal(c)" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors" title="编辑">
                <Pencil class="w-4 h-4" />
              </button>
              <button @click="remove(c.id)" :disabled="deletingId === c.id"
                class="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-400 hover:text-red-500 transition-colors disabled:opacity-50" title="删除">
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
    <CommonModal v-model="showModal" :title="editingContact ? '编辑联系人' : '添加联系人'">
      <div class="space-y-4">
        <div>
          <label for="contact-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">姓名 <span class="text-red-500">*</span></label>
          <input id="contact-name" v-model="form.name" placeholder="输入姓名"
            :class="['w-full px-3 py-2 border rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all', formErrors.name ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-border-dark']"
            @input="formErrors.name = ''" />
          <span v-if="formErrors.name" class="text-red-500 text-xs mt-1 block">{{ formErrors.name }}</span>
        </div>
        <div>
          <label for="contact-email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮箱 <span class="text-red-500">*</span></label>
          <input id="contact-email" v-model="form.email" type="email" placeholder="输入邮箱"
            :class="['w-full px-3 py-2 border rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all', formErrors.email ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-border-dark']"
            @input="formErrors.email = ''" />
          <span v-if="formErrors.email" class="text-red-500 text-xs mt-1 block">{{ formErrors.email }}</span>
        </div>
        <div>
          <label for="contact-phone" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">电话</label>
          <input id="contact-phone" v-model="form.phone" placeholder="输入电话（可选）"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all" />
        </div>
        <div>
          <label for="contact-notes" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">备注</label>
          <textarea id="contact-notes" v-model="form.notes" placeholder="输入备注（可选）" rows="2"
            class="w-full px-3 py-2 border border-gray-200 dark:border-border-dark rounded-lg bg-white dark:bg-bg-panelDark text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"></textarea>
        </div>
      </div>
      <template #footer>
        <button @click="showModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-sm">取消</button>
        <button @click="save" :disabled="saving"
          class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors text-sm font-medium disabled:opacity-50 flex items-center gap-2">
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </CommonModal>
  </div>
</template>
