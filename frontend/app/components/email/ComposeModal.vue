<script setup lang="ts">
import { Paperclip, Send, Loader2 } from 'lucide-vue-next'

const { isComposeOpen } = useGlobalModal()
const { sendEmail } = useApi()

const recipients = ref('')
const subject = ref('')
const body = ref('')
const sending = ref(false)
const error = ref('')

const handleSend = async () => {
  if (!recipients.value || !subject.value) {
    error.value = '请填写收件人和主题'
    return
  }
  
  sending.value = true
  error.value = ''
  try {
    await sendEmail({ to: recipients.value, subject: subject.value, body_text: body.value })
    isComposeOpen.value = false
    recipients.value = ''
    subject.value = ''
    body.value = ''
  } catch (e: any) {
    error.value = e.data?.detail || '发送失败'
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <CommonModal v-model="isComposeOpen" title="新邮件" widthClass="w-full max-w-3xl">
    <div class="space-y-4">
      <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>
      <div>
        <input v-model="recipients" type="text" placeholder="收件人 (多个用逗号分隔)" class="w-full px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
      </div>
      <div>
        <input v-model="subject" type="text" placeholder="主题" class="w-full px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all">
      </div>
      <div>
        <textarea v-model="body" placeholder="内容..." class="w-full h-64 px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none custom-scrollbar"></textarea>
      </div>
    </div>

    <template #footer>
      <button class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 mr-auto">
        <Paperclip class="w-5 h-5" />
      </button>
      <button @click="handleSend" :disabled="sending" class="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-lg shadow-primary/20 transition-all font-medium disabled:opacity-50">
        <Loader2 v-if="sending" class="w-4 h-4 animate-spin" />
        <Send v-else class="w-4 h-4" /> {{ sending ? '发送中...' : '发送' }}
      </button>
    </template>
  </CommonModal>
</template>