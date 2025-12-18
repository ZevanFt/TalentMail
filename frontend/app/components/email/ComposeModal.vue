<script setup lang="ts">
import { Paperclip, Send, Loader2, Eye } from 'lucide-vue-next'

const { isComposeOpen } = useGlobalModal()
const { sendEmail } = useApi()
const { composeState, resetCompose, formatTime, folders, loadEmails, currentFolderId } = useEmails()

const recipients = ref('')
const ccRecipients = ref('')
const subject = ref('')
const body = ref('')
const sending = ref(false)
const error = ref('')
const showCc = ref(false)
const isTracked = ref(false)

// 计算标题
const modalTitle = computed(() => {
  switch (composeState.value.mode) {
    case 'reply': return '回复'
    case 'replyAll': return '回复全部'
    case 'forward': return '转发'
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
watch(() => [isComposeOpen.value, composeState.value], () => {
  if (!isComposeOpen.value) return
  
  const { mode, originalEmail } = composeState.value
  if (!originalEmail || mode === 'compose') {
    recipients.value = ''
    ccRecipients.value = ''
    subject.value = ''
    body.value = ''
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

  // 正文引用
  const quote = `\n\n-------- 原始邮件 --------\n发件人: ${originalEmail.sender}\n时间: ${formatTime(originalEmail.received_at)}\n主题: ${originalEmail.subject}\n\n${originalEmail.body_text || ''}`
  body.value = mode === 'forward' ? quote : '\n' + quote
}, { immediate: true })

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
      is_tracked: isTracked.value
    })
    isComposeOpen.value = false
    resetCompose()
    recipients.value = ''
    ccRecipients.value = ''
    subject.value = ''
    body.value = ''
    isTracked.value = false
    
    // 发送成功后，切换到已发送文件夹并刷新
    const sentFolder = folders.value.find(f => f.role === 'sent')
    if (sentFolder) {
      currentFolderId.value = sentFolder.id
      await loadEmails(sentFolder.id)
    }
  } catch (e: any) {
    error.value = e.data?.detail || '发送失败'
  } finally {
    sending.value = false
  }
}

// 关闭时重置状态
watch(isComposeOpen, (open) => {
  if (!open) resetCompose()
})
</script>

<template>
  <CommonModal v-model="isComposeOpen" :title="modalTitle" widthClass="w-full max-w-3xl">
    <div class="space-y-3">
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
      <button class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 mr-auto">
        <Paperclip class="w-5 h-5" />
      </button>
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