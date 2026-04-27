<script setup lang="ts">
/**
 * 邮件签名管理设置页
 */
import { PenLine, Plus, Trash2, Star, Edit3 } from 'lucide-vue-next'

const { getSignatures, createSignature, updateSignature, deleteSignature } = useApi()
const toast = useToast()

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

// 预览
const showPreview = ref(false)

const loadSignatures = async () => {
  loading.value = true
  try {
    const res = await getSignatures()
    signatures.value = res.items || res
    total.value = res.total ?? signatures.value.length
  } catch (e: any) {
    toast.error(e.data?.detail || '加载签名失败')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  form.name = ''
  form.content_html = ''
  form.is_default = false
  showPreview.value = false
  showModal.value = true
}

const openEdit = (sig: Signature) => {
  editingId.value = sig.id
  form.name = sig.name
  form.content_html = sig.content_html
  form.is_default = sig.is_default
  showPreview.value = false
  showModal.value = true
}

const handleSave = async () => {
  if (!form.name.trim()) {
    toast.error('请输入签名名称')
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
      toast.success('签名已更新')
    } else {
      await createSignature({
        name: form.name.trim(),
        content_html: form.content_html,
        is_default: form.is_default,
      })
      toast.success('签名已创建')
    }
    showModal.value = false
    await loadSignatures()
  } catch (e: any) {
    toast.error(e.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (sig: Signature) => {
  if (!confirm(`确定要删除签名「${sig.name}」吗？`)) return
  try {
    await deleteSignature(sig.id)
    toast.success('签名已删除')
    await loadSignatures()
  } catch (e: any) {
    toast.error(e.data?.detail || '删除失败')
  }
}

const handleSetDefault = async (sig: Signature) => {
  try {
    await updateSignature(sig.id, { is_default: true })
    toast.success(`已将「${sig.name}」设为默认签名`)
    await loadSignatures()
  } catch (e: any) {
    toast.error(e.data?.detail || '设置失败')
  }
}

onMounted(loadSignatures)
</script>

<template>
  <div class="space-y-6">
    <!-- 标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">邮件签名</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">管理您的邮件签名，发送邮件时自动附加默认签名</p>
      </div>
      <button
        @click="openCreate"
        class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors whitespace-nowrap"
      >
        <Plus class="w-4 h-4" /> 新建签名
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
      <p class="text-gray-500 dark:text-gray-400 mb-2">还没有创建邮件签名</p>
      <p class="text-sm text-gray-400 dark:text-gray-500 mb-6">创建签名后，发送邮件时会自动附加默认签名</p>
      <button @click="openCreate" class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors">
        <Plus class="w-4 h-4" /> 创建第一个签名
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
            >默认</span>
          </div>
          <div class="flex items-center gap-1">
            <button
              v-if="!sig.is_default"
              @click="handleSetDefault(sig)"
              class="p-1.5 text-gray-400 hover:text-yellow-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="设为默认"
            >
              <Star class="w-4 h-4" />
            </button>
            <button
              @click="openEdit(sig)"
              class="p-1.5 text-gray-400 hover:text-primary rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="编辑"
            >
              <Edit3 class="w-4 h-4" />
            </button>
            <button
              @click="handleDelete(sig)"
              class="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="删除"
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
          (空签名)
        </div>
      </div>

      <p class="text-xs text-gray-400 text-center">最多创建 20 个签名</p>
    </div>

    <!-- 创建/编辑弹窗 -->
    <CommonModal v-model="showModal" :title="editingId ? '编辑签名' : '新建签名'" max-width="lg">
      <div class="space-y-4">
        <!-- 签名名称 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">签名名称</label>
          <input
            v-model="form.name"
            type="text"
            maxlength="100"
            placeholder="例如：工作签名、个人签名"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <!-- 签名内容 (HTML) -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">签名内容 (HTML)</label>
            <button
              @click="showPreview = !showPreview"
              class="text-xs text-primary hover:underline"
            >{{ showPreview ? '编辑模式' : '预览效果' }}</button>
          </div>
          <div v-if="showPreview" class="min-h-[120px] p-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm" v-html="form.content_html"></div>
          <textarea
            v-else
            v-model="form.content_html"
            rows="6"
            placeholder="<p>Best regards,</p><p><strong>Your Name</strong></p><p>Company Inc.</p>"
            class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          ></textarea>
        </div>

        <!-- 设为默认 -->
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="form.is_default" class="rounded border-gray-300 text-primary focus:ring-primary" />
          <span class="text-sm text-gray-700 dark:text-gray-300">设为默认签名</span>
        </label>

        <!-- 操作按钮 -->
        <div class="flex justify-end gap-3 pt-2">
          <button
            @click="showModal = false"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >取消</button>
          <button
            @click="handleSave"
            :disabled="saving"
            class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 whitespace-nowrap"
          >{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </CommonModal>
  </div>
</template>
