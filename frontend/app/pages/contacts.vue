<script setup lang="ts">
import { Search, Plus, Pencil, Trash2, X, User } from 'lucide-vue-next'

const { getContacts, createContact, updateContact, deleteContact } = useApi()

interface Contact { id: number; name: string | null; email: string | null; phone: string | null; notes: string | null }
const contacts = ref<Contact[]>([])
const searchQuery = ref('')
const showModal = ref(false)
const editingContact = ref<Contact | null>(null)
const form = reactive({ name: '', email: '', phone: '', notes: '' })
const loading = ref(false)

const loadContacts = async () => {
  loading.value = true
  try { contacts.value = await getContacts(searchQuery.value || undefined) } catch {} finally { loading.value = false }
}

const openModal = (contact?: Contact) => {
  editingContact.value = contact || null
  form.name = contact?.name || ''
  form.email = contact?.email || ''
  form.phone = contact?.phone || ''
  form.notes = contact?.notes || ''
  showModal.value = true
}

const save = async () => {
  if (!form.name.trim() || !form.email.trim()) return
  try {
    if (editingContact.value) {
      await updateContact(editingContact.value.id, form)
    } else {
      await createContact(form)
    }
    showModal.value = false
    await loadContacts()
  } catch {}
}

const remove = async (id: number) => {
  if (!confirm('确定删除此联系人？')) return
  try { await deleteContact(id); await loadContacts() } catch {}
}

let debounceTimer: any
watch(searchQuery, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadContacts, 300)
})

onMounted(loadContacts)
</script>

<template>
  <div class="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
    <header class="flex items-center justify-between px-6 py-4 border-b dark:border-gray-800 bg-white dark:bg-gray-900">
      <h1 class="text-xl font-bold">通讯录</h1>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input v-model="searchQuery" placeholder="搜索联系人..." class="pl-9 pr-4 py-2 w-64 border rounded-lg dark:bg-gray-800 dark:border-gray-700" />
        </div>
        <button @click="openModal()" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover">
          <Plus class="w-4 h-4" /> 添加联系人
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
      <div v-else-if="contacts.length === 0" class="text-center py-12 text-gray-500">
        <User class="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>暂无联系人</p>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="c in contacts" :key="c.id" class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border dark:border-gray-700">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <span class="text-primary font-bold">{{ (c.name || '?').charAt(0).toUpperCase() }}</span>
              </div>
              <div>
                <div class="font-medium">{{ c.name }}</div>
                <div class="text-sm text-gray-500">{{ c.email }}</div>
              </div>
            </div>
            <div class="flex gap-1">
              <button @click="openModal(c)" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><Pencil class="w-4 h-4" /></button>
              <button @click="remove(c.id)" class="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded text-red-500"><Trash2 class="w-4 h-4" /></button>
            </div>
          </div>
          <div v-if="c.phone" class="mt-2 text-sm text-gray-500">📞 {{ c.phone }}</div>
          <div v-if="c.notes" class="mt-1 text-sm text-gray-400 truncate">{{ c.notes }}</div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 shadow-xl">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-bold text-lg">{{ editingContact ? '编辑联系人' : '添加联系人' }}</h3>
            <button @click="showModal = false"><X class="w-5 h-5" /></button>
          </div>
          <div class="space-y-3">
            <input v-model="form.name" placeholder="姓名 *" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
            <input v-model="form.email" type="email" placeholder="邮箱 *" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
            <input v-model="form.phone" placeholder="电话" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
            <textarea v-model="form.notes" placeholder="备注" rows="2" class="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"></textarea>
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <button @click="showModal = false" class="px-4 py-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">取消</button>
            <button @click="save" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover">保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>