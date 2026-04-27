<script setup lang="ts">
import { Paperclip, Send, Loader2, Eye, X, FileText, FilePen, Clock, ChevronDown, CheckCircle, XCircle, Shield } from 'lucide-vue-next'
import TemplateSelector from './TemplateSelector.vue'

const toastNotify = useToast()
const { isComposeOpen, composeCloseGuard } = useGlobalModal()
const { sendEmail, saveDraft, updateDraft, deleteDraft, getDefaultSignature, uploadAttachment, deleteAttachment, getAliases, getMe, getComposeTemplates, lookupPgpKey } = useApi()
const { encryptMessage, hasLocalPrivateKey, exportPrivateKey } = usePGP()
const { composeState, resetCompose, formatTime, folders, loadEmails, currentFolderId } = useEmails()

interface UploadedFile {
  id: number
  filename: string
  size: number
}

const recipients = ref('')
const ccRecipients = ref('')
const bccRecipients = ref('')
const subject = ref('')
const body = ref('')
const sending = ref(false)
const error = ref('')
const showCc = ref(false)
const showBcc = ref(false)
const isTracked = ref(false)
const encryptEnabled = ref(false)
const draftId = ref<number | null>(null)
const showDraftConfirm = ref(false)
const closeRequestResolver = ref<((ok: boolean) => void) | null>(null)
const draftDialogAction = ref<'save' | 'discard' | null>(null)
const savingDraft = ref(false)
const defaultSignature = ref('')
const attachments = ref<UploadedFile[]>([])
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const editorRef = ref<any>(null)
const scheduledSendAt = ref<string>('')
const showScheduleMenu = ref(false)

const appliedTemplate = ref<any>(null)

// 发件人选择（别名发信）
const selectedFromAlias = ref<number | null>(null)
const userEmail = ref('')
const aliasOptions = ref<Array<{ id: number; alias_email: string; name: string | null }>>([])

const loadSenderOptions = async () => {
  try {
    const me = await getMe()
    userEmail.value = me.email
    const aliasesData = await getAliases()
    aliasOptions.value = aliasesData.filter((a: any) => a.is_active)
  } catch (e: any) {
    console.error('加载发件人选项失败', e)
  }
}

const loadDefaultSignature = async () => {
  try {
    const res = await getDefaultSignature()
    defaultSignature.value = res.signature || ''
  } catch (e: any) {
    console.error('加载签名失败', e)
    toastNotify.error('加载签名失败')
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
    // 先消毒再设 innerHTML，防止 img onerror 等 XSS 副作用
    const clean = sanitizeHtml(html)
    div.innerHTML = clean
    return (div.textContent || div.innerText || '')
      .replace(/\u00A0/g, ' ')
      .trim()
  }
  return html.replace(/<[^>]+>/g, '').trim()
}

// 使用 DOMPurify 统一消毒（替代手写 sanitizer）
const { sanitizeEmailHtml: sanitizeHtml } = useSanitize()

const signatureHtml = computed(() => {
  if (!defaultSignature.value.trim()) return ''
  return `<p><br></p><p>${escapeHtml(defaultSignature.value).replace(/\n/g, '<br>')}</p>`
})

const setBodyHtml = async (html: string) => {
  const safe = sanitizeHtml(html)
  body.value = safe
  await nextTick()
  editorRef.value?.setContent(safe)
}


watch(() => [isComposeOpen.value, composeState.value], async () => {
  if (!isComposeOpen.value) return

  if (!defaultSignature.value) {
    await loadDefaultSignature()
  }
  // 加载发件人选项（别名列表）
  if (!userEmail.value) {
    await loadSenderOptions()
  }
  selectedFromAlias.value = null

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
  } catch (e: any) {
    console.error('上传失败', e)
    error.value = '附件上传失败'
    toastNotify.error('附件上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

// 拖拽上传
const isDragging = ref(false)

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (e: DragEvent) => {
  // 只在离开容器时取消高亮
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  if (e.clientX <= rect.left || e.clientX >= rect.right || e.clientY <= rect.top || e.clientY >= rect.bottom) {
    isDragging.value = false
  }
}

const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (!files?.length) return
  uploading.value = true
  try {
    for (const file of files) {
      const res = await uploadAttachment(file)
      attachments.value.push({ id: res.id, filename: res.filename, size: res.size })
    }
    toastNotify.success(`已上传 ${files.length} 个附件`)
  } catch (e: any) {
    console.error('拖拽上传失败', e)
    toastNotify.error('附件上传失败')
  } finally {
    uploading.value = false
  }
}

const removeAttachment = async (att: UploadedFile) => {
  try {
    await deleteAttachment(att.id)
    attachments.value = attachments.value.filter(a => a.id !== att.id)
  } catch (e: any) {
    console.error('删除附件失败', e)
    toastNotify.error('删除附件失败')
  }
}

// formatFileSize 来自 utils/format.ts (Nuxt 自动导入)

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const validateRecipients = (field: string, label: string): string | null => {
  if (!field.trim()) return null
  const emails = field.split(/[,;，；]\s*/).map(e => e.trim()).filter(Boolean)
  for (const email of emails) {
    if (!emailRegex.test(email)) {
      return `${label}中「${email}」不是有效的邮箱地址`
    }
  }
  return null
}

const handleSend = async (scheduleTime?: string) => {
  if (!recipients.value || !subject.value) {
    error.value = '请填写收件人和主题'
    return
  }

  // 校验所有收件人邮箱格式
  const toError = validateRecipients(recipients.value, '收件人')
  if (toError) { error.value = toError; return }
  const ccError = validateRecipients(ccRecipients.value, '抄送')
  if (ccError) { error.value = ccError; return }
  const bccError = validateRecipients(bccRecipients.value, '密送')
  if (bccError) { error.value = bccError; return }

  sending.value = true
  error.value = ''
  showScheduleMenu.value = false
  try {
    const { mode, originalEmail } = composeState.value
    const safeHtml = sanitizeHtml(body.value)

    let finalBodyHtml = safeHtml
    let finalBodyText = editorRef.value?.getText() || stripHtml(safeHtml)

    // PGP 加密：查找收件人公钥并加密正文
    if (encryptEnabled.value) {
      try {
        const firstRecipient = recipients.value.split(',')[0].trim()
        const emailMatch = firstRecipient.match(/<([^>]+)>/) || [null, firstRecipient]
        const recipientEmail = (emailMatch[1] || firstRecipient).trim().toLowerCase()

        const lookup = await lookupPgpKey(recipientEmail)
        if (!lookup.has_key || !lookup.public_key) {
          error.value = `收件人 ${recipientEmail} 未设置 PGP 公钥，无法加密发送`
          sending.value = false
          return
        }

        const localKey = exportPrivateKey()
        const passphrase = localStorage.getItem('talentmail_pgp_passphrase') || undefined
        const encrypted = await encryptMessage(finalBodyText, lookup.public_key, localKey || undefined, passphrase)
        finalBodyHtml = `<pre style="white-space:pre-wrap;font-family:monospace;">${encrypted}</pre>`
        finalBodyText = encrypted
      } catch (e: any) {
        console.error('PGP 加密失败', e)
        error.value = 'PGP 加密失败: ' + (e.message || '未知错误')
        sending.value = false
        return
      }
    }

    const payload: Record<string, any> = {
      to: recipients.value,
      cc: ccRecipients.value || undefined,
      bcc: bccRecipients.value || undefined,
      subject: subject.value,
      body_html: finalBodyHtml,
      body_text: finalBodyText,
      reply_to_id: (mode === 'reply' || mode === 'replyAll') && originalEmail ? originalEmail.id : undefined,
      is_tracked: isTracked.value,
      attachment_ids: attachments.value.map(a => a.id),
      from_alias_id: selectedFromAlias.value || undefined
    }

    // 定时发送：将本地时间转为 UTC ISO 字符串
    const sendAt = scheduleTime || scheduledSendAt.value
    if (sendAt) {
      payload.scheduled_send_at = new Date(sendAt).toISOString()
    }

    await sendEmail(payload)

    if (draftId.value) {
      try {
        await deleteDraft(draftId.value)
      } catch (e: any) {
        console.error('删除草稿失败', e)
        toastNotify.error('删除草稿失败')
      }
    }

    if (sendAt) {
      toastNotify.success(`邮件已设置定时发送: ${new Date(sendAt).toLocaleString()}`, 5000)
    } else {
      toastNotify.success('邮件已加入发送队列，请在"已发送"文件夹查看发送状态', 5000)
    }

    closeAndReset()

    const sentFolder = folders.value.find(f => f.role === 'sent')
    if (sentFolder) {
      currentFolderId.value = sentFolder.id
      await loadEmails(sentFolder.id)
    }
  } catch (e: any) {
    error.value = e.data?.detail || '发送失败'
    toastNotify.error(error.value)
  } finally {
    sending.value = false
  }
}

const handleScheduleSend = () => {
  if (!scheduledSendAt.value) {
    error.value = '请选择定时发送时间'
    return
  }
  const selectedTime = new Date(scheduledSendAt.value)
  if (selectedTime <= new Date()) {
    error.value = '定时发送时间必须在未来'
    return
  }
  handleSend(scheduledSendAt.value)
}

// datetime-local 输入使用本地时间，需要格式化为 YYYY-MM-DDTHH:mm
const toLocalDatetimeStr = (d: Date): string => {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 快捷定时选项
const schedulePresets = computed(() => {
  const now = new Date()
  const later = new Date(now.getTime() + 2 * 60 * 60 * 1000) // 2小时后
  const tomorrow9am = new Date(now)
  tomorrow9am.setDate(tomorrow9am.getDate() + 1)
  tomorrow9am.setHours(9, 0, 0, 0)
  const nextMonday9am = new Date(now)
  nextMonday9am.setDate(nextMonday9am.getDate() + ((8 - nextMonday9am.getDay()) % 7 || 7))
  nextMonday9am.setHours(9, 0, 0, 0)

  return [
    { label: '2小时后', value: toLocalDatetimeStr(later) },
    { label: '明天上午9点', value: toLocalDatetimeStr(tomorrow9am) },
    { label: '下周一上午9点', value: toLocalDatetimeStr(nextMonday9am) },
  ]
})

const hasContent = computed(() => {
  const sigText = defaultSignature.value.trim()
  let bodyText = stripHtml(body.value)

  if (sigText) {
    bodyText = bodyText.replace(sigText, '').trim()
  }

  const hasRecipients = recipients.value.trim().length > 0
  const hasSubject = subject.value.trim().length > 0
  const hasBody = bodyText.length > 0
  const hasAttachments = attachments.value.length > 0

  return hasRecipients || hasSubject || hasBody || hasAttachments
})

const resolveCloseRequest = (ok: boolean) => {
  if (closeRequestResolver.value) {
    closeRequestResolver.value(ok)
    closeRequestResolver.value = null
  }
}

const requestCloseWithDraftGuard = async () => {
  if (!hasContent.value) {
    closeAndReset()
    return true
  }
  showDraftConfirm.value = true
  return await new Promise<boolean>((resolve) => {
    closeRequestResolver.value = resolve
  })
}

const tryClose = async () => {
  await requestCloseWithDraftGuard()
}

const handleSaveDraft = async () => {
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
    draftDialogAction.value = 'save'
    showDraftConfirm.value = false
    closeAndReset()
    resolveCloseRequest(true)

    const draftsFolder = folders.value.find(f => f.role === 'drafts')
    if (draftsFolder && currentFolderId.value === draftsFolder.id) {
      await loadEmails(draftsFolder.id)
    }
  } catch (e: any) {
    console.error('保存草稿失败', e)
    toastNotify.error('保存草稿失败')
  } finally {
    savingDraft.value = false
  }
}

const discardDraft = async () => {
  if (draftId.value) {
    try {
      await deleteDraft(draftId.value)
    } catch (e: any) {
      console.error('删除草稿失败', e)
      toastNotify.error('删除草稿失败')
    }
  }
  draftDialogAction.value = 'discard'
  showDraftConfirm.value = false
  closeAndReset()
  resolveCloseRequest(true)
}

const closeAndReset = () => {
  isComposeOpen.value = false
  resetCompose()
  recipients.value = ''
  ccRecipients.value = ''
  bccRecipients.value = ''
  subject.value = ''
  body.value = ''
  isTracked.value = false
  draftId.value = null
  attachments.value = []
  scheduledSendAt.value = ''
  showScheduleMenu.value = false
  showBcc.value = false
  editorRef.value?.setContent('')
}

watch(showDraftConfirm, (open) => {
  if (open) return
  if (draftDialogAction.value) {
    draftDialogAction.value = null
    return
  }
  // 对话框被关闭但未执行保存/丢弃动作时，视为取消切换
  resolveCloseRequest(false)
})

// ========== Ctrl+Enter 发送 / Ctrl+S 保存草稿 / Esc 关闭定时菜单 ==========
const handleComposeKeydown = (e: KeyboardEvent) => {
  // Ctrl/Cmd + Enter → 发送
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault()
    if (!sending.value) handleSend()
    return
  }
  // Ctrl/Cmd + S → 保存草稿
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    if (!savingDraft.value) autoSaveDraft()
    return
  }
  // Escape → 关闭定时菜单
  if (e.key === 'Escape' && showScheduleMenu.value) {
    showScheduleMenu.value = false
  }
}

// 定时菜单 click-outside 关闭
const handleClickOutsideSchedule = (e: MouseEvent) => {
  if (!showScheduleMenu.value) return
  const target = e.target as HTMLElement
  if (!target.closest('.schedule-menu-container')) {
    showScheduleMenu.value = false
  }
}

onMounted(() => {
  composeCloseGuard.value = requestCloseWithDraftGuard
  if (import.meta.client) {
    window.addEventListener('beforeunload', beforeUnloadHandler)
    window.addEventListener('keydown', handleComposeKeydown)
    document.addEventListener('click', handleClickOutsideSchedule, true)
  }
})

onUnmounted(() => {
  if (composeCloseGuard.value === requestCloseWithDraftGuard) {
    composeCloseGuard.value = null
  }
  resolveCloseRequest(false)
  if (import.meta.client) {
    window.removeEventListener('beforeunload', beforeUnloadHandler)
    window.removeEventListener('keydown', handleComposeKeydown)
    document.removeEventListener('click', handleClickOutsideSchedule, true)
  }
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
    autoSaveTimer = null
  }
})

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

// ========== 用户写信模板 ==========
interface UserComposeTemplate {
  id: number
  name: string | null
  subject: string | null
  body_html: string | null
}
const showComposeTemplateMenu = ref(false)
const composeTemplates = ref<UserComposeTemplate[]>([])
const loadingComposeTemplates = ref(false)
const composeTemplateMenuRef = ref<HTMLElement | null>(null)

const loadComposeTemplates = async () => {
  if (composeTemplates.value.length > 0) return // 已加载
  loadingComposeTemplates.value = true
  try {
    const res = await getComposeTemplates()
    composeTemplates.value = res.items || []
  } catch (e: any) {
    console.error('加载写信模板失败', e)
  } finally {
    loadingComposeTemplates.value = false
  }
}

const applyComposeTemplate = async (tmpl: UserComposeTemplate) => {
  showComposeTemplateMenu.value = false
  if (tmpl.subject) {
    subject.value = tmpl.subject
  }
  if (tmpl.body_html) {
    await setBodyHtml(`${sanitizeHtml(tmpl.body_html)}${signatureHtml.value}`)
  }
  toastNotify.success(`已应用模板「${tmpl.name}」`)
}

watch(showComposeTemplateMenu, (v) => {
  if (v) loadComposeTemplates()
})

const onClickOutsideComposeTemplate = (e: MouseEvent) => {
  if (composeTemplateMenuRef.value && !composeTemplateMenuRef.value.contains(e.target as Node)) {
    showComposeTemplateMenu.value = false
  }
}
watch(showComposeTemplateMenu, (v) => {
  if (v) {
    setTimeout(() => document.addEventListener('click', onClickOutsideComposeTemplate), 0)
  } else {
    document.removeEventListener('click', onClickOutsideComposeTemplate)
  }
})

// ========== 自动保存草稿（30 秒防抖） ==========
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
const autoSaveStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')

const autoSaveDraft = async () => {
  if (!hasContent.value || sending.value || savingDraft.value) return
  autoSaveStatus.value = 'saving'
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
    autoSaveStatus.value = 'saved'
    // 3 秒后恢复到 idle
    setTimeout(() => { if (autoSaveStatus.value === 'saved') autoSaveStatus.value = 'idle' }, 3000)
  } catch (e) {
    autoSaveStatus.value = 'error'
    console.error('自动保存草稿失败', e)
    setTimeout(() => { if (autoSaveStatus.value === 'error') autoSaveStatus.value = 'idle' }, 5000)
  }
}

watch(
  [recipients, ccRecipients, subject, body],
  () => {
    if (autoSaveTimer) clearTimeout(autoSaveTimer)
    if (!isComposeOpen.value) return
    autoSaveTimer = setTimeout(autoSaveDraft, 30000)
  },
  { deep: false }
)

// ========== beforeunload 保护 ==========
const beforeUnloadHandler = (e: BeforeUnloadEvent) => {
  if (isComposeOpen.value && hasContent.value) {
    e.preventDefault()
    // 现代浏览器忽略自定义消息，但需要赋值才能触发对话框
    e.returnValue = ''
  }
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

  <section v-if="isComposeOpen" class="flex-1 h-full flex flex-col min-w-0 relative"
    @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop">
    <!-- 拖拽上传覆盖层 -->
    <Transition name="fade">
      <div v-if="isDragging"
        class="absolute inset-0 z-50 bg-primary/10 dark:bg-primary/20 border-2 border-dashed border-primary rounded-xl
               flex items-center justify-center pointer-events-none">
        <div class="text-center">
          <Paperclip class="w-10 h-10 text-primary mx-auto mb-2" />
          <p class="text-sm font-bold text-primary">松开以添加附件</p>
        </div>
      </div>
    </Transition>
    <div class="h-12 px-4 border-b border-gray-200/50 dark:border-gray-800/50 flex items-center justify-between shrink-0">
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
        <!-- 用户写信模板 -->
        <div ref="composeTemplateMenuRef" class="relative">
          <button
            @click="showComposeTemplateMenu = !showComposeTemplateMenu"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            title="插入写信模板"
          >
            <FilePen class="w-3.5 h-3.5" />
            <span class="hidden lg:inline">快捷模板</span>
          </button>
          <Transition enter-active-class="transition duration-100 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
            leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
            <div v-if="showComposeTemplateMenu" class="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 max-h-72 overflow-y-auto">
              <div v-if="loadingComposeTemplates" class="p-4 text-center text-gray-500 text-sm">加载中...</div>
              <div v-else-if="composeTemplates.length === 0" class="p-4 text-center text-gray-500 text-sm">
                暂无模板，前往设置创建
              </div>
              <div v-else class="py-1">
                <button
                  v-for="tmpl in composeTemplates" :key="tmpl.id"
                  @click="applyComposeTemplate(tmpl)"
                  class="w-full text-left px-3 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ tmpl.name }}</div>
                  <div v-if="tmpl.subject" class="text-xs text-gray-400 truncate mt-0.5">{{ tmpl.subject }}</div>
                </button>
              </div>
            </div>
          </Transition>
        </div>
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

      <!-- 发件人选择（有别名时显示） -->
      <div v-if="aliasOptions.length > 0" class="flex items-center gap-2">
        <span class="text-xs font-medium text-gray-500 dark:text-gray-400 w-12 shrink-0">发件人</span>
        <select v-model="selectedFromAlias"
          class="flex-1 px-3 py-2 text-sm border-2 border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
          <option :value="null">{{ userEmail }}</option>
          <option v-for="alias in aliasOptions" :key="alias.id" :value="alias.id">
            {{ alias.alias_email }}{{ alias.name ? ` (${alias.name})` : '' }}
          </option>
        </select>
      </div>

      <div class="flex items-stretch gap-2">
        <div class="flex-1 relative group">
          <EmailContactAutocomplete v-model="recipients" placeholder="收件人 (多个用逗号分隔)" aria-label="收件人" />
          <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
        </div>
        <button v-if="!showCc" @click="showCc = true"
          class="px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary dark:hover:text-primary
                 bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-800 border-2 border-gray-200 dark:border-gray-700
                 rounded-xl transition-all duration-200 hover:scale-105">
          抄送
        </button>
        <button v-if="!showBcc" @click="showBcc = true"
          class="px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-primary dark:hover:text-primary
                 bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-800 border-2 border-gray-200 dark:border-gray-700
                 rounded-xl transition-all duration-200 hover:scale-105">
          密送
        </button>
      </div>

      <div v-if="showCc" class="relative group animate-in fade-in slide-in-from-top-2 duration-200">
        <EmailContactAutocomplete v-model="ccRecipients" placeholder="抄送 (多个用逗号分隔)" aria-label="抄送" />
        <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
      </div>

      <div v-if="showBcc" class="relative group animate-in fade-in slide-in-from-top-2 duration-200">
        <EmailContactAutocomplete v-model="bccRecipients" placeholder="密送 BCC (收件人互不可见)" aria-label="密送" />
        <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
      </div>

      <div class="relative group">
        <input v-model="subject" type="text" placeholder="主题" aria-label="邮件主题"
          class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900/50 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                 focus:bg-white dark:focus:bg-gray-900 focus:ring-2 focus:ring-primary/30 focus:border-primary
                 outline-none transition-all duration-200 placeholder:text-gray-400">
        <div class="absolute inset-0 -z-10 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-300"></div>
      </div>

      <LazyEditorRichEditor
        ref="editorRef"
        v-model="body"
        placeholder="撰写邮件内容..."
        :min-height="360"
      />
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

      <button @click="encryptEnabled = !encryptEnabled"
        class="flex items-center gap-2.5 px-3 py-2 text-sm font-medium mr-4 rounded-xl transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800"
        :class="encryptEnabled ? 'text-green-600' : 'text-gray-500 dark:text-gray-400'"
        title="PGP 加密">
        <div class="relative w-10 h-5 rounded-full transition-all duration-200 shadow-inner"
          :class="encryptEnabled ? 'bg-green-500 shadow-green-500/30' : 'bg-gray-300 dark:bg-gray-600'">
          <div class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-md transition-all duration-200"
            :class="encryptEnabled ? 'translate-x-5' : 'translate-x-0.5'"></div>
        </div>
        <Shield class="w-4 h-4 transition-transform duration-200" :class="encryptEnabled ? 'scale-110' : ''" />
        <span class="transition-colors">加密</span>
      </button>

      <!-- 自动保存状态指示器 -->
      <Transition name="fade">
        <span v-if="autoSaveStatus !== 'idle'" class="text-xs px-2 py-1 rounded-lg flex items-center gap-1 mr-2"
          :class="{
            'text-gray-400': autoSaveStatus === 'saving',
            'text-green-500': autoSaveStatus === 'saved',
            'text-red-400': autoSaveStatus === 'error',
          }">
          <Loader2 v-if="autoSaveStatus === 'saving'" class="w-3 h-3 animate-spin" />
          <CheckCircle v-else-if="autoSaveStatus === 'saved'" class="w-3 h-3" />
          <XCircle v-else-if="autoSaveStatus === 'error'" class="w-3 h-3" />
          {{ autoSaveStatus === 'saving' ? '保存中...' : autoSaveStatus === 'saved' ? '已保存' : '保存失败' }}
        </span>
      </Transition>

      <div class="relative flex items-center schedule-menu-container">
        <button @click="handleSend()" :disabled="sending"
          class="flex items-center gap-2.5 px-6 py-2.5 bg-gradient-to-r from-primary to-primary-hover text-white
                 rounded-l-xl hover:shadow-lg hover:shadow-primary/30 active:scale-95
                 transition-all duration-200 font-semibold disabled:opacity-50 disabled:cursor-not-allowed
                 disabled:hover:shadow-none disabled:active:scale-100"
          title="发送 (Ctrl+Enter)">
          <Loader2 v-if="sending" class="w-4 h-4 animate-spin" />
          <Send v-else class="w-4 h-4" />
          <span>{{ sending ? '发送中...' : '发送' }}</span>
        </button>
        <button @click="showScheduleMenu = !showScheduleMenu" :disabled="sending"
          class="px-2.5 py-2.5 bg-gradient-to-r from-primary-hover to-primary-hover text-white
                 rounded-r-xl border-l border-white/20 hover:brightness-110 active:scale-95
                 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
          <ChevronDown class="w-4 h-4" />
        </button>

        <!-- 定时发送下拉菜单 -->
        <div v-if="showScheduleMenu"
          class="absolute bottom-full right-0 mb-2 w-72 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <div class="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
              <Clock class="w-4 h-4 text-primary" />
              <span>定时发送</span>
            </div>
          </div>
          <div class="p-2 space-y-1">
            <button v-for="preset in schedulePresets" :key="preset.label"
              @click="handleSend(preset.value)"
              class="w-full px-3 py-2 text-left text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors">
              {{ preset.label }}
              <span class="text-xs text-gray-400 ml-1">{{ new Date(preset.value).toLocaleString() }}</span>
            </button>
          </div>
          <div class="px-3 py-2 border-t border-gray-100 dark:border-gray-700">
            <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">自定义时间</label>
            <div class="flex items-center gap-2">
              <input v-model="scheduledSendAt" type="datetime-local"
                :min="new Date().toISOString().slice(0, 16)"
                class="flex-1 px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300 outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary" />
              <button @click="handleScheduleSend" :disabled="!scheduledSendAt"
                class="px-3 py-1.5 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                确定
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
