<script setup lang="ts">
/**
 * 邮件签名管理设置页
 */
import { PenLine, Plus, Trash2, Star, Edit3 } from 'lucide-vue-next'

const { getSignatures, createSignature, updateSignature, deleteSignature } = useApi()
const toast = useToast()
const { t } = useI18n()

interface Signature {
  id: number
  name: string
  content_html: string
  is_default: boolean
}

const loading = ref(true)
const signatures = ref<Signature[]>([])
const total = ref(0)

// 弹窗
const showModal = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  name: '',
  content_html: '',
  is_default: false,
})
const saving = ref(false)

const loadSignatures = async () => {
  loading.value = true
  try {
    const res = await getSignatures()
    signatures.value = res.items || res
    total.value = res.total ?? signatures.value.length
  } catch (e: any) {
    toast.error(e.data?.detail || t('settings.signatures.loadFailed'))
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  form.name = ''
  form.content_html = ''
  form.is_default = false
  showModal.value = true
}

const openEdit = (sig: Signature) => {
  editingId.value = sig.id
  form.name = sig.name
  form.content_html = sig.content_html
  form.is_default = sig.is_default
  showModal.value = true
}

const handleSave = async () => {
  if (!form.name.trim()) {
    toast.error(t('settings.signatures.nameRequired'))
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateSignature(editingId.value, {
        name: form.name.trim(),
        content_html: form.content_html,
        is_default: form.is_default,
      })
      toast.success(t('settings.signatures.updated'))
    } else {
      await createSignature({
        name: form.name.trim(),
        content_html: form.content_html,
        is_default: form.is_default,
      })
      toast.success(t('settings.signatures.created'))
    }
    showModal.value = false
    await loadSignatures()
  } catch (e: any) {
    toast.error(e.data?.detail || t('settings.signatures.saveFailed'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (sig: Signature) => {
  if (!confirm(t('settings.signatures.confirmDelete', { name: sig.name }))) return
  try {
    await deleteSignature(sig.id)
    toast.success(t('settings.signatures.deleted'))
    await loadSignatures()
  } catch (e: any) {
    toast.error(e.data?.detail || t('settings.signatures.deleteFailed'))
  }
}

const handleSetDefault = async (sig: Signature) => {
  try {
    await updateSignature(sig.id, { is_default: true })
    toast.success(t('settings.signatures.setDefaultSuccess', { name: sig.name }))
    await loadSignatures()
  } catch (e: any) {
    toast.error(e.data?.detail || t('settings.signatures.setDefaultFailed'))
  }
}

onMounted(loadSignatures)
</script>

<template>
  <div class="space-y-6">
    <!-- 标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('settings.tabs.signatures') }}</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ t('settings.signatures.subtitle') }}</p>
      </div>
      <button
        @click="openCreate"
        class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors whitespace-nowrap"
      >
        <Plus class="w-4 h-4" /> {{ t('settings.signatures.create') }}
      </button>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="p-4 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark">
        <div class="flex items-center gap-3">
          <div class="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
          <div class="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        </div>
        <div class="mt-3 h-12 bg-gray-100 dark:bg-gray-800 rounded animate-pulse"></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="signatures.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
      <PenLine class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
      <p class="text-gray-500 dark:text-gray-400 mb-2">{{ t('settings.signatures.emptyTitle') }}</p>
      <p class="text-sm text-gray-400 dark:text-gray-500 mb-6">{{ t('settings.signatures.emptyDesc') }}</p>
      <button @click="openCreate" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
        <Plus class="w-4 h-4" /> {{ t('settings.signatures.createFirst') }}
      </button>
    </div>

    <!-- 签名列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="sig in signatures"
        :key="sig.id"
        class="p-4 bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="font-medium text-gray-900 dark:text-white">{{ sig.name }}</span>
            <span
              v-if="sig.is_default"
              class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs rounded-full whitespace-nowrap"
            >{{ t('settings.signatures.defaultBadge') }}</span>
          </div>
          <div class="flex items-center gap-1">
            <button
              v-if="!sig.is_default"
              @click="handleSetDefault(sig)"
              class="p-1.5 text-gray-400 hover:text-yellow-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              :title="t('settings.signatures.setDefault')"
            >
              <Star class="w-4 h-4" />
            </button>
            <button
              @click="openEdit(sig)"
              class="p-1.5 text-gray-400 hover:text-primary rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              :title="t('settings.automation.edit')"
            >
              <Edit3 class="w-4 h-4" />
            </button>
            <button
              @click="handleDelete(sig)"
              class="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              :title="t('common.delete')"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
        <!-- 签名预览 -->
        <div
          v-if="sig.content_html"
          class="text-sm text-gray-600 dark:text-gray-400 border-t border-gray-100 dark:border-gray-800 pt-2 mt-2 line-clamp-3"
          v-html="sig.content_html"
        ></div>
        <div v-else class="text-sm text-gray-400 italic border-t border-gray-100 dark:border-gray-800 pt-2 mt-2">
          {{ t('settings.signatures.emptySignature') }}
        </div>
      </div>

      <p class="text-xs text-gray-400 text-center">{{ t('settings.signatures.maxHint') }}</p>
    </div>

    <!-- 创建/编辑弹窗 -->
    <CommonModal v-model="showModal" :title="editingId ? t('settings.signatures.editTitle') : t('settings.signatures.create')" max-width="2xl">
      <div class="space-y-4">
        <!-- 签名名称 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settings.signatures.name') }}</label>
          <input
            v-model="form.name"
            type="text"
            maxlength="100"
            :placeholder="t('settings.signatures.namePlaceholder')"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <!-- 签名内容（富文本编辑器） -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ t('settings.signatures.content') }}</label>
          <EditorRichEditor
            v-model="form.content_html"
            :placeholder="t('settings.signatures.contentPlaceholder')"
            :min-height="150"
          />
        </div>

        <!-- 设为默认 -->
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="form.is_default" class="rounded border-gray-300 text-primary focus:ring-primary" />
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ t('settings.signatures.setAsDefault') }}</span>
        </label>

        <!-- 操作按钮 -->
        <div class="flex justify-end gap-3 pt-2">
          <button
            @click="showModal = false"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >{{ t('common.cancel') }}</button>
          <button
            @click="handleSave"
            :disabled="saving"
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 whitespace-nowrap"
          >{{ saving ? t('settings.common.saving') : t('common.save') }}</button>
        </div>
      </div>
    </CommonModal>
  </div>
</template>
