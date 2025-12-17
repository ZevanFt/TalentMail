export const useEmails = () => {
  const selectedEmailId = useState<number | null>('selectedEmailId', () => 1)

  const emails = useState('emails', () => [
    {
      id: 1,
      from: 'Talent Team',
      avatar: 'T',
      color: 'bg-primary',
      subject: '欢迎使用 TalentMail 🚀',
      snippet: '这是您的第一封邮件，体验一下极速的收发信体验吧...',
      body: `你好，Talent！\n\n欢迎来到 TalentMail。这不仅仅是一个邮件客户端，更是你高效工作的开始。\n\n目前我们已经完成了：\n1. Nuxt 4 架构迁移\n2. 响应式布局\n3. 模拟数据流\n\n加油！`,
      time: '10:32',
      date: '今天',
      read: false,
      starred: true
    },
    {
      id: 2,
      from: 'GitHub',
      avatar: 'G',
      color: 'bg-zinc-700',
      subject: '[GitHub] Security Alert',
      snippet: 'We noticed a new sign-in to your account...',
      body: 'Security Alert: We noticed a new sign-in to your GitHub account from a Linux device.',
      time: '09:15',
      date: '今天',
      read: true,
      starred: false
    }
  ])

  const selectedEmail = computed(() => 
    emails.value.find(e => e.id === selectedEmailId.value)
  )

  return { emails, selectedEmailId, selectedEmail }
}