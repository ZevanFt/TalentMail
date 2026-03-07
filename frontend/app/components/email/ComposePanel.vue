<script setup lang="ts">
import { Paperclip, Send, Loader2, Eye, X, FileText, Bold, Italic, Underline, List, ListOrdered, Link2, Quote, Eraser } from 'lucide-vue-next'
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
const editorRef = ref<HTMLDivElement | null>(null)

const appliedTemplate = ref<any>(null)

const loadDefaultSignature = async () => {
  try {
    const res = await getDefaultSignature()
    defaultSignature.value = res.signature || ''
  } catch (e) {
    console.error('加载签名失败', e)
  }
}

const modalTitle = computed(() => {
  switch (composeState.value.mode) {
    case 'reply': return '回复'
    case 'replyAll': return '回复全部'
    case 'forward': return '转发'
    case 'draft': return '编辑草稿'
    default: return '新邮件'
  }
})

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

const extractEmail = (sender: string) => {
  const match = sender.match(/<([^>]+)>/)
  return match ? match[1] : sender
}

const escapeHtml = (input: string) => input
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const textToHtml = (text: string) => {
  if (!text) return ''
  return `<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>`
}

const stripHtml = (html: string) => {
  if (!html) return ''
  if (import.meta.client) {
    const div = document.createElement('div')
    div.innerHTML = html
    return (div.textContent || div.innerText || '')
      .replace(/\u00A0/g, ' ')
      .trim()
  }
  return html.replace(/<[^>]+>/g, '').trim()
}

const sanitizeHtml = (html: string) => {
  if (!html || !import.meta.client) return html
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')

  doc.querySelectorAll('script, style, iframe, object, embed').forEach((el) => el.remove())

  doc.querySelectorAll('*').forEach((el) => {
    const attrs = [...el.attributes]
    for (const attr of attrs) {
      const name = attr.name.toLowerCase()
      const value = attr.value
      if (name.startsWith('on')) {
        el.removeAttribute(attr.name)
      }
      if ((name === 'href' || name === 'src') && /^javascript:/i.test(value)) {
        el.removeAttribute(attr.name)
      }
    }
  })

  return doc.body.innerHTML
}

const signatureHtml = computed(() => {
  if (!defaultSignature.value.trim()) return ''
  return `<p><br></p><p>${escapeHtml(defaultSignature.value).replace(/\n/g, '<br>')}</p>`
})

const setBodyHtml = async (html: string) => {
  body.value = sanitizeHtml(html)
  await nextTick()
  if (editorRef.value) {
    editorRef.value.innerHTML = body.value
  }
}

const syncBodyFromEditor = () => {
  body.value = sanitizeHtml(editorRef.value?.innerHTML || '')
}

const applyFormat = (command: string, value?: string) => {
  if (!import.meta.client || !editorRef.value) return
  editorRef.value.focus()
  document.execCommand(command, false, value)
  syncBodyFromEditor()
}

const insertLink = () => {
  if (!import.meta.client) return
  const link = window.prompt('请输入链接 URL')
  if (!link) return
  applyFormat('createLink', link)
}

const clearFormatting = () => {
  applyFormat('removeFormat')
}

const handlePaste = (e: ClipboardEvent) => {
  if (!import.meta.client) return
  e.preventDefault()

  const html = e.clipboardData?.getData('text/html')
  const text = e.clipboardData?.getData('text/plain') || ''

  const content = html
    ? sanitizeHtml(html)
    : escapeHtml(text).replace(/\n/g, '<br>')

  document.execCommand('insertHTML', false, content)
  syncBodyFromEditor()
}

watch(() => [isComposeOpen.value, composeState.value], async () => {
  if (!isComposeOpen.value) return

  if (!defaultSignature.value) {
    await loadDefaultSignature()
  }

  const { mode, originalEmail } = composeState.value
  if (!originalEmail || mode === 'compose') {
    recipients.value = ''
    ccRecipients.value = ''
    subject.value = ''
    showCc.value = false
    await setBodyHtml(signatureHtml.value)
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
    const allCc = [...parsed.to, ...parsed.cc].filter(e => e !== senderEmail)
    ccRecipients.value = allCc.join(', ')
    showCc.value = allCc.length > 0
  } else if (mode === 'forward') {
    recipients.value = ''
    ccRecipients.value = ''
    showCc.value = false
  }

  const subjectPrefix = mode === 'forward' ? 'Fwd: ' : 'Re: '
  const cleanSubject = originalEmail.subject.replace(/^(Re:|Fwd:)\s*/gi, '')
  subject.value = subjectPrefix + cleanSubject

  const originalBody = originalEmail.body_text || stripHtml(originalEmail.body_html || '')
  const quoteHtml = `
    <p><br></p>
    <hr />
    <p><strong>原始邮件</strong></p>
    <p>发件人: ${escapeHtml(originalEmail.sender)}</p>
    <p>时间: ${escapeHtml(formatTime(originalEmail.received_at))}</p>
    <p>主题: ${escapeHtml(originalEmail.subject || '')}</p>
    <blockquote style="margin:8px 0 0;padding-left:12px;border-left:3px solid #d1d5db;color:#6b7280;">
      ${escapeHtml(originalBody).replace(/\n/g, '<br>')}
    </blockquote>
  `

  await setBodyHtml(`${signatureHtml.value}${quoteHtml}`)
}, { immediate: true })

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
  syncBodyFromEditor()

  if (!recipients.value || !subject.value) {
    error.value = '请填写收件人和主题'
    return
  }

  sending.value = true
  error.value = ''
  try {
    const { mode, originalEmail } = composeState.value
    const safeHtml = sanitizeHtml(body.value)

    await sendEmail({
      to: recipients.value,
      cc: ccRecipients.value || undefined,
      subject: subject.value,
      body_html: safeHtml,
      body_text: stripHtml(safeHtml),
      reply_to_id: (mode === 'reply' || mode === 'replyAll') && originalEmail ? originalEmail.id : undefined,
      is_tracked: isTracked.value,
      attachment_ids: attachments.value.map(a => a.id)
    })

    if (draftId.value) {
      try {
        await deleteDraft(draftId.value)
      } catch (e) {
        console.error('删除草稿失败', e)
      }
    }

    if (typeof window !== 'undefined') {
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

    const sentFolder = folders.value.find(f => f.role === 'sent')
    if (sentFolder) {
      currentFolderId.value = sentFolder.id
      await loadEmails(sentFolder.id)
    }
  } catch (e: any) {
    error.value = e.data?.detail || '发送失败'
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

const hasContent = computed(() => {
  const sigText = defaultSignature.value.trim()
  let bodyText = stripHtml(body.value)

  if (sigText) {
    bodyText = bodyText.replace(sigText, '').trim()
  }

  const hasRecipients = recipients.value.trim().length > 0
  const hasSubject = subject.value.trim().length > 0
  const hasBody = bodyText.length > 0

  return hasRecipients || hasSubject || hasBody
})

const tryClose = () => {
  syncBodyFromEditor()
  if (hasContent.value) {
    showDraftConfirm.value = true
    return
  }
  closeAndReset()
}

const handleSaveDraft = async () => {
  syncBodyFromEditor()
  savingDraft.value = true
  try {
    const safeHtml = sanitizeHtml(body.value)
    const data = {
      to: recipients.value,
      cc: ccRecipients.value,
      subject: subject.value,
      body_text: stripHtml(safeHtml),
      body_html: safeHtml
    }
    if (draftId.value) {
      await updateDraft(draftId.value, data)
    } else {
      const res = await saveDraft(data)
      draftId.value = res.data.id
    }
    showDraftConfirm.value = false
    closeAndReset()

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
  if (editorRef.value) {
    editorRef.value.innerHTML = ''
  }
}

watch(() => composeState.value, async (state) => {
  if (state.mode === 'draft' && state.originalEmail) {
    const email = state.originalEmail
    draftId.value = email.id
    subject.value = email.subject || ''
    await setBodyHtml(email.body_html || textToHtml(email.body_text || ''))
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

const handleTemplateSelect = async (data: {
  template: any
  metadata: any
  variables: Record<string, string>
  renderedSubject: string
  renderedBody: string
}) => {
  subject.value = data.renderedSubject
  appliedTemplate.value = data.template
  await setBodyHtml(`${sanitizeHtml(data.renderedBody)}${signatureHtml.value}`)
}

const handleTemplateClear = () => {
  appliedTemplate.value = null
}
</script>

<template>
  <CommonModal v-model="showDraftConfirm" title="保存草稿？" widthClass="w-full max-w-sm">
    <div class="flex items-start gap-3 py-2">
      <div class="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center shrink-0">
        <svg class="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path>
        </svg>
      </div>
      <div>
        <p class="text-gray-700 dark:text-gray-300 font-medium">是否将当前内容保存为草稿？</p>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">保存后可在草稿箱中继续编辑</p>
      </div>
    </div>
    <template #footer>
      <button @click="discardDraft"
        class="px-5 py-2.5 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200
               hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all duration-200 font-medium">
        不保存
      </button>
      <button @click="handleSaveDraft" :disabled="savingDraft"
        class="px-5 py-2.5 bg-gradient-to-r from-primary to-primary-hover text-white rounded-xl
               hover:shadow-lg hover:shadow-primary/30 transition-all duration-200 font-semibold
               disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
        <Loader2 v-if="savingDraft" class="w-4 h-4 animate-spin" />
        <span>{{ savingDraft ? '保存中...' : '保存草稿' }}</span>
      </button>
    </template>
  </CommonModal>

  <section v-if="isComposeOpen" class="flex-1 h-full flex flex-col min-w-0">
    <div class="px-4 py-3.5 border-b border-gray-200/50 dark:border-gray-800/50 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2 min-w-0">
        <h2 class="text-xs font-bold text-gray-600 dark:text-gray-400 tracking-wide">{{ modalTitle }}</h2>
        <div v-if="appliedTemplate" class="hidden md:flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <FileText class="w-3.5 h-3.5" />
          <span class="font-medium max-w-36 truncate">{{ appliedTemplate.name }}</span>
        </div>
      </div>
      <div class="flex items-center gap-1 p-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-800/80">
        <TemplateSelector
          compact
          toolbar
          @select="handleTemplateSelect"
          @clear="handleTemplateClear"
        />
        <button
          @click="handleSaveDraft"
          :disabled="savingDraft"
          class="px-3 py-1.5 text-xs rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          {{ savingDraft ? '保存中...' : '保存草稿' }}
        </button>
        <button
          @click="tryClose"
          class="p-1.5 rounded-md text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
          title="关闭写信面板"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-4">
      <div v-if="error" class="px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 text-sm flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <span>{{ error }}</span>
      </div>

      <div class="flex items-stretch gap-2">
        <div class="flex-1 relative group">
          <input v-model="recipients" type="text" placeholder="收件人 (多个用逗号分隔)"
            class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                   focus:bg-white dark:focus:bg-gray-900 focus:ring-2 focus:ring-primary/30 focus:border-primary
                   outline-none transition-all duration-200 placeholder:text-gray-400">
          <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
        </div>
        <button v-if="!showCc" @click="showCc = true"
          class="px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary dark:hover:text-primary
                 bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-800 border-2 border-gray-200 dark:border-gray-700
                 rounded-xl transition-all duration-200 hover:scale-105">
          抄送
        </button>
      </div>

      <div v-if="showCc" class="relative group animate-in fade-in slide-in-from-top-2 duration-200">
        <input v-model="ccRecipients" type="text" placeholder="抄送 (多个用逗号分隔)"
          class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                 focus:bg-white dark:focus:bg-gray-900 focus:ring-2 focus:ring-primary/30 focus:border-primary
                 outline-none transition-all duration-200 placeholder:text-gray-400">
        <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
      </div>

      <div class="relative group">
        <input v-model="subject" type="text" placeholder="主题"
          class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                 focus:bg-white dark:focus:bg-gray-900 focus:ring-2 focus:ring-primary/30 focus:border-primary
                 outline-none transition-all duration-200 placeholder:text-gray-400">
        <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
      </div>

      <div class="border-2 border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden bg-gray-50 dark:bg-gray-900/50">
        <div class="flex items-center gap-1 px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/60">
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="加粗" @click="applyFormat('bold')">
            <Bold class="w-4 h-4" />
          </button>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="斜体" @click="applyFormat('italic')">
            <Italic class="w-4 h-4" />
          </button>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="下划线" @click="applyFormat('underline')">
            <Underline class="w-4 h-4" />
          </button>
          <div class="w-px h-5 bg-gray-200 dark:bg-gray-700 mx-1"></div>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="无序列表" @click="applyFormat('insertUnorderedList')">
            <List class="w-4 h-4" />
          </button>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="有序列表" @click="applyFormat('insertOrderedList')">
            <ListOrdered class="w-4 h-4" />
          </button>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="引用" @click="applyFormat('formatBlock', 'blockquote')">
            <Quote class="w-4 h-4" />
          </button>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="插入链接" @click="insertLink">
            <Link2 class="w-4 h-4" />
          </button>
          <button class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800" type="button" title="清除格式" @click="clearFormatting">
            <Eraser class="w-4 h-4" />
          </button>
        </div>

        <div
          ref="editorRef"
          class="min-h-[360px] px-4 py-3 bg-white dark:bg-gray-900 outline-none prose prose-sm dark:prose-invert max-w-none"
          contenteditable="true"
          @input="syncBodyFromEditor"
          @blur="syncBodyFromEditor"
          @paste="handlePaste"
        ></div>
      </div>
    </div>

    <div class="h-20 border-t border-gray-200/50 dark:border-gray-800/50 px-6 flex items-center gap-3 shrink-0">
      <div class="flex items-center gap-3 mr-auto min-w-0">
        <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />
        <button @click="fileInput?.click()" :disabled="uploading"
          class="p-2.5 text-gray-500 hover:text-primary dark:hover:text-primary bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700
                 rounded-xl transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          title="添加附件">
          <Loader2 v-if="uploading" class="w-5 h-5 animate-spin text-primary" />
          <Paperclip v-else class="w-5 h-5" />
        </button>
        <div v-if="attachments.length" class="flex flex-wrap gap-2 max-w-md">
          <span v-for="att in attachments" :key="att.id"
            class="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700
                   border border-gray-200 dark:border-gray-600 rounded-lg text-xs text-gray-700 dark:text-gray-300
                   shadow-sm hover:shadow transition-all duration-200 group">
            <Paperclip class="w-3 h-3 text-gray-400 group-hover:text-primary transition-colors" />
            <span class="font-medium">{{ att.filename }}</span>
            <span class="text-gray-400">({{ formatFileSize(att.size) }})</span>
            <button @click="removeAttachment(att)"
              class="ml-1 p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors group/btn"
              title="删除附件">
              <X class="w-3 h-3 text-gray-400 group-hover/btn:text-red-500 transition-colors" />
            </button>
          </span>
        </div>
      </div>

      <button @click="isTracked = !isTracked"
        class="flex items-center gap-2.5 px-3 py-2 text-sm font-medium mr-4 rounded-xl transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800"
        :class="isTracked ? 'text-primary' : 'text-gray-500 dark:text-gray-400'">
        <div class="relative w-10 h-5 rounded-full transition-all duration-200 shadow-inner"
          :class="isTracked ? 'bg-primary shadow-primary/30' : 'bg-gray-300 dark:bg-gray-600'">
          <div class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-md transition-all duration-200"
            :class="isTracked ? 'translate-x-5' : 'translate-x-0.5'"></div>
        </div>
        <Eye class="w-4 h-4 transition-transform duration-200" :class="isTracked ? 'scale-110' : ''" />
        <span class="transition-colors">追踪</span>
      </button>

      <button @click="handleSend" :disabled="sending"
        class="flex items-center gap-2.5 px-7 py-2.5 bg-gradient-to-r from-primary to-primary-hover text-white
               rounded-xl hover:shadow-lg hover:shadow-primary/30 active:scale-95
               transition-all duration-200 font-semibold disabled:opacity-50 disabled:cursor-not-allowed
               disabled:hover:shadow-none disabled:active:scale-100">
        <Loader2 v-if="sending" class="w-4 h-4 animate-spin" />
        <Send v-else class="w-4 h-4" />
        <span>{{ sending ? '发送中...' : '发送' }}</span>
      </button>
    </div>
  </section>
</template>
