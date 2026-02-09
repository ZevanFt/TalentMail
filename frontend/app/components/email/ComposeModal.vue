<script setup lang="ts">
import { Paperclip, Send, Loader2, Eye, X, FileText } from 'lucide-vue-next'
import TemplateSelector from './TemplateSelector.vue'

const { isComposeOpen } = useGlobalModal()
const { sendEmail, saveDraft, updateDraft, deleteDraft, getDefaultSignature, uploadAttachment, deleteAttachment } = useApi()
const { composeState, resetCompose, formatTime, folders, loadEmails, currentFolderId } = useEmails()

interface UploadedFile {
  id: number
  filename: string
  size: number
}

const recipients = ref('')
const ccRecipients = ref('')
const subject = ref('')
const body = ref('')
const sending = ref(false)
const error = ref('')
const showCc = ref(false)
const isTracked = ref(false)
const draftId = ref<number | null>(null)
const showDraftConfirm = ref(false)
const savingDraft = ref(false)
const defaultSignature = ref('')
const attachments = ref<UploadedFile[]>([])
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 模板选择状态
const showTemplateSelector = ref(false)
const appliedTemplate = ref<any>(null)

// 加载默认签名
const loadDefaultSignature = async () => {
  try {
    const res = await getDefaultSignature()
    defaultSignature.value = res.signature || ''
  } catch (e) {
    console.error('加载签名失败', e)
  }
}

// 计算标题
const modalTitle = computed(() => {
  switch (composeState.value.mode) {
    case 'reply': return '回复'
    case 'replyAll': return '回复全部'
    case 'forward': return '转发'
    case 'draft': return '编辑草稿'
    default: return '新邮件'
  }
})

// 解析收件人 JSON
const parseRecipients = (recipientsStr: string) => {
  try {
    const data = JSON.parse(recipientsStr)
    return {
      to: (data.to || []).map((r: any) => r.email || r).filter(Boolean),
      cc: (data.cc || []).map((r: any) => r.email || r).filter(Boolean)
    }
  } catch {
    return { to: [recipientsStr], cc: [] }
  }
}

// 提取发件人邮箱
const extractEmail = (sender: string) => {
  const match = sender.match(/<([^>]+)>/)
  return match ? match[1] : sender
}

// 监听模式变化，预填内容
watch(() => [isComposeOpen.value, composeState.value], async () => {
  if (!isComposeOpen.value) return
  
  // 加载默认签名
  if (!defaultSignature.value) {
    await loadDefaultSignature()
  }
  
  const { mode, originalEmail } = composeState.value
  if (!originalEmail || mode === 'compose') {
    recipients.value = ''
    ccRecipients.value = ''
    subject.value = ''
    // 新邮件自动附加签名
    body.value = defaultSignature.value ? '\n\n' + defaultSignature.value : ''
    showCc.value = false
    return
  }

  const parsed = parseRecipients(originalEmail.recipients)
  const senderEmail = extractEmail(originalEmail.sender)
  
  if (mode === 'reply') {
    recipients.value = senderEmail || ''
    ccRecipients.value = ''
    showCc.value = false
  } else if (mode === 'replyAll') {
    recipients.value = senderEmail || ''
    // 抄送：原收件人 + 原抄送（排除自己）
    const allCc = [...parsed.to, ...parsed.cc].filter(e => e !== senderEmail)
    ccRecipients.value = allCc.join(', ')
    showCc.value = allCc.length > 0
  } else if (mode === 'forward') {
    recipients.value = ''
    ccRecipients.value = ''
    showCc.value = false
  }

  // 主题
  const subjectPrefix = mode === 'forward' ? 'Fwd: ' : 'Re: '
  const cleanSubject = originalEmail.subject.replace(/^(Re:|Fwd:)\s*/gi, '')
  subject.value = subjectPrefix + cleanSubject

  // 正文引用（带签名）
  const sig = defaultSignature.value ? '\n\n' + defaultSignature.value : ''
  const quote = `\n\n-------- 原始邮件 --------\n发件人: ${originalEmail.sender}\n时间: ${formatTime(originalEmail.received_at)}\n主题: ${originalEmail.subject}\n\n${originalEmail.body_text || ''}`
  body.value = mode === 'forward' ? sig + quote : sig + quote
}, { immediate: true })

// 附件上传
const handleFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  
  uploading.value = true
  try {
    for (const file of input.files) {
      const res = await uploadAttachment(file)
      attachments.value.push({ id: res.id, filename: res.filename, size: res.size })
    }
  } catch (e) {
    console.error('上传失败', e)
    error.value = '附件上传失败'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

const removeAttachment = async (att: UploadedFile) => {
  try {
    await deleteAttachment(att.id)
    attachments.value = attachments.value.filter(a => a.id !== att.id)
  } catch (e) {
    console.error('删除附件失败', e)
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const handleSend = async () => {
  if (!recipients.value || !subject.value) {
    error.value = '请填写收件人和主题'
    return
  }
  
  sending.value = true
  error.value = ''
  try {
    const { mode, originalEmail } = composeState.value
    await sendEmail({
      to: recipients.value,
      cc: ccRecipients.value || undefined,
      subject: subject.value,
      body_text: body.value,
      reply_to_id: (mode === 'reply' || mode === 'replyAll') && originalEmail ? originalEmail.id : undefined,
      is_tracked: isTracked.value,
      attachment_ids: attachments.value.map(a => a.id)
    })
    
    // 如果是从草稿发送，删除草稿
    if (draftId.value) {
      try {
        await deleteDraft(draftId.value)
      } catch (e) {
        console.error('删除草稿失败', e)
      }
    }
    
    // 显示成功提示（使用浏览器原生通知）
    if (typeof window !== 'undefined') {
      // 创建一个临时的成功提示元素
      const toast = document.createElement('div')
      toast.className = 'fixed top-4 right-4 z-50 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in'
      toast.innerHTML = `
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        <span>邮件已加入发送队列，请在"已发送"文件夹查看发送状态</span>
      `
      document.body.appendChild(toast)
      setTimeout(() => {
        toast.style.opacity = '0'
        toast.style.transition = 'opacity 0.3s'
        setTimeout(() => document.body.removeChild(toast), 300)
      }, 5000)
    }

    closeAndReset()

    // 发送成功后，切换到已发送文件夹并刷新
    const sentFolder = folders.value.find(f => f.role === 'sent')
    if (sentFolder) {
      currentFolderId.value = sentFolder.id
      await loadEmails(sentFolder.id)
    }
  } catch (e: any) {
    error.value = e.data?.detail || '发送失败'
    // 显示错误提示
    if (typeof window !== 'undefined') {
      const toast = document.createElement('div')
      toast.className = 'fixed top-4 right-4 z-50 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2'
      toast.innerHTML = `
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        <span>${error.value}</span>
      `
      document.body.appendChild(toast)
      setTimeout(() => {
        toast.style.opacity = '0'
        toast.style.transition = 'opacity 0.3s'
        setTimeout(() => document.body.removeChild(toast), 300)
      }, 5000)
    }
  } finally {
    sending.value = false
  }
}

// 检查是否有内容（排除只有签名的情况）
const hasContent = computed(() => {
  // 移除签名后检查正文是否有内容
  let bodyContent = body.value
  if (defaultSignature.value) {
    // 签名可能带有前导换行符，需要处理
    const sigWithNewlines = '\n\n' + defaultSignature.value
    bodyContent = bodyContent.replace(sigWithNewlines, '').replace(defaultSignature.value, '')
  }
  bodyContent = bodyContent.trim()
  
  const hasRecipients = recipients.value.trim().length > 0
  const hasSubject = subject.value.trim().length > 0
  const hasBody = bodyContent.length > 0
  
  return hasRecipients || hasSubject || hasBody
})

// 尝试关闭弹窗（返回 false 阻止关闭）
const beforeClose = () => {
  console.log('beforeClose called, hasContent:', hasContent.value)
  console.log('recipients:', recipients.value)
  console.log('subject:', subject.value)
  console.log('body:', body.value)
  
  if (hasContent.value) {
    showDraftConfirm.value = true
    return false
  }
  closeAndReset()
  return true
}

// 保存草稿
const handleSaveDraft = async () => {
  savingDraft.value = true
  try {
    const data = {
      to: recipients.value,
      cc: ccRecipients.value,
      subject: subject.value,
      body_text: body.value
    }
    if (draftId.value) {
      await updateDraft(draftId.value, data)
    } else {
      const res = await saveDraft(data)
      draftId.value = res.data.id
    }
    showDraftConfirm.value = false
    closeAndReset()
    // 刷新草稿箱
    const draftsFolder = folders.value.find(f => f.role === 'drafts')
    if (draftsFolder && currentFolderId.value === draftsFolder.id) {
      await loadEmails(draftsFolder.id)
    }
  } catch (e) {
    console.error('保存草稿失败', e)
  } finally {
    savingDraft.value = false
  }
}

// 不保存直接关闭
const discardDraft = async () => {
  if (draftId.value) {
    try {
      await deleteDraft(draftId.value)
    } catch (e) {
      console.error('删除草稿失败', e)
    }
  }
  showDraftConfirm.value = false
  closeAndReset()
}

// 关闭并重置
const closeAndReset = () => {
  isComposeOpen.value = false
  resetCompose()
  recipients.value = ''
  ccRecipients.value = ''
  subject.value = ''
  body.value = ''
  isTracked.value = false
  draftId.value = null
  attachments.value = []
}

// 从草稿打开时加载内容
watch(() => composeState.value, (state) => {
  if (state.mode === 'draft' && state.originalEmail) {
    const email = state.originalEmail
    draftId.value = email.id
    subject.value = email.subject || ''
    body.value = email.body_text || ''
    // 解析收件人
    try {
      const r = JSON.parse(email.recipients || '{}')
      recipients.value = (r.to || []).map((x: any) => x.email).join(', ')
      ccRecipients.value = (r.cc || []).map((x: any) => x.email).join(', ')
      showCc.value = ccRecipients.value.length > 0
    } catch {
      recipients.value = ''
      ccRecipients.value = ''
    }
  }
}, { immediate: true })

// 处理模板选择
const handleTemplateSelect = (data: {
  template: any
  metadata: any
  variables: Record<string, string>
  renderedSubject: string
  renderedBody: string
}) => {
  // 应用模板到邮件
  subject.value = data.renderedSubject
  // 保留签名，在模板内容后追加
  const sig = defaultSignature.value ? '\n\n' + defaultSignature.value : ''
  // 将 HTML 转换为纯文本（简单处理）
  const plainText = data.renderedBody
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<[^>]+>/g, '')
    .trim()
  body.value = plainText + sig
  appliedTemplate.value = data.template
  showTemplateSelector.value = false
}

const handleTemplateClear = () => {
  appliedTemplate.value = null
}
</script>

<template>
  <!-- 草稿确认对话框 -->
  <CommonModal v-model="showDraftConfirm" title="保存草稿？" widthClass="w-full max-w-sm">
    <p class="text-gray-600 dark:text-gray-400">是否将当前内容保存为草稿？</p>
    <template #footer>
      <button @click="discardDraft" class="px-4 py-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
        不保存
      </button>
      <button @click="handleSaveDraft" :disabled="savingDraft" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50">
        {{ savingDraft ? '保存中...' : '保存草稿' }}
      </button>
    </template>
  </CommonModal>

  <CommonModal v-model="isComposeOpen" :title="modalTitle" widthClass="w-full max-w-3xl" :before-close="beforeClose">
    <div class="space-y-3">
      <!-- 模板选择区 -->
      <div class="flex items-center gap-4 pb-3 border-b border-gray-200 dark:border-gray-700">
        <TemplateSelector
          @select="handleTemplateSelect"
          @clear="handleTemplateClear"
        />
        <div v-if="appliedTemplate" class="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
          <FileText class="w-4 h-4" />
          <span>已应用: {{ appliedTemplate.name }}</span>
        </div>
      </div>
      
      <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>
      <div class="flex items-center gap-2">
        <input v-model="recipients" type="text" placeholder="收件人 (多个用逗号分隔)" class="flex-1 px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
        <button v-if="!showCc" @click="showCc = true" class="text-sm text-gray-500 hover:text-primary px-2">抄送</button>
      </div>
      <div v-if="showCc">
        <input v-model="ccRecipients" type="text" placeholder="抄送 (多个用逗号分隔)" class="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
      </div>
      <div>
        <input v-model="subject" type="text" placeholder="主题" class="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
      </div>
      <div>
        <textarea v-model="body" placeholder="内容..." class="w-full h-64 px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none custom-scrollbar"></textarea>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center gap-2 mr-auto">
        <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />
        <button @click="fileInput?.click()" :disabled="uploading" class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
          <Loader2 v-if="uploading" class="w-5 h-5 animate-spin" />
          <Paperclip v-else class="w-5 h-5" />
        </button>
        <div v-if="attachments.length" class="flex flex-wrap gap-1">
          <span v-for="att in attachments" :key="att.id" class="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-400">
            {{ att.filename }} ({{ formatFileSize(att.size) }})
            <button @click="removeAttachment(att)" class="hover:text-red-500"><X class="w-3 h-3" /></button>
          </span>
        </div>
      </div>
      <button @click="isTracked = !isTracked" class="flex items-center gap-2 text-sm mr-4 transition-colors" :class="isTracked ? 'text-primary' : 'text-gray-400'">
        <div class="relative w-9 h-5 rounded-full transition-colors" :class="isTracked ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'">
          <div class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform" :class="isTracked ? 'translate-x-4' : 'translate-x-0.5'"></div>
        </div>
        <Eye class="w-4 h-4" />
        <span>追踪</span>
      </button>
      <button @click="handleSend" :disabled="sending" class="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all font-medium disabled:opacity-50">
        <Loader2 v-if="sending" class="w-4 h-4 animate-spin" />
        <Send v-else class="w-4 h-4" /> {{ sending ? '发送中...' : '发送' }}
      </button>
    </template>
  </CommonModal>
</template>