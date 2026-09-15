<script setup lang="ts">
import { BookOpen, Copy, Check, ExternalLink, KeyRound, Terminal, Zap } from 'lucide-vue-next'

const { t } = useI18n()
const { appName } = useConfig()
const toast = useToast()

useHead({ title: computed(() => `${t('developers.title')} - ${appName}`) })

const copied = ref('')
const copy = async (id: string, text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = id
    setTimeout(() => { if (copied.value === id) copied.value = '' }, 1500)
  } catch {
    toast.error(t('developers.copyFailed'))
  }
}

const baseUrl = computed(() => {
  if (import.meta.client) return `${window.location.origin}/api`
  return '/api'
})

const curlSample = computed(() => `curl -X POST ${baseUrl.value}/pool/mailboxes \\
  -H "Authorization: Bearer tm_YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: ci-job-\${CI_JOB_ID}" \\
  -d '{"prefix":"e2e","purpose":"signup"}'`)

const pythonSample = `from talentmail_client import TalentMailClient

client = TalentMailClient(
    base_url="https://mail.example.com/api",
    api_key="tm_YOUR_API_KEY",
)
mailbox = client.create_temp_mailbox(prefix="e2e", purpose="signup")
code = client.wait_for_code(mailbox["id"], timeout=60)
print(mailbox["email"], code)`

const nodeSample = `import { TalentMailClient } from './talentmail-client.mjs'

const client = new TalentMailClient({
  baseUrl: 'https://mail.example.com/api',
  apiKey: process.env.TALENTMAIL_API_KEY,
})
const mailbox = await client.createTempMailbox({ prefix: 'e2e' })
const code = await client.waitForCode(mailbox.id, { timeoutMs: 60000 })
console.log(mailbox.email, code)`

const scopes = [
  { scope: 'temp_mailbox:create', desc: t('developers.scopes.create') },
  { scope: 'temp_mailbox:read', desc: t('developers.scopes.readMb') },
  { scope: 'temp_email:read', desc: t('developers.scopes.readMail') },
  { scope: 'temp_code:read', desc: t('developers.scopes.readCode') },
  { scope: 'temp_mailbox:extend', desc: t('developers.scopes.extend') },
  { scope: 'temp_mailbox:restore', desc: t('developers.scopes.restore') },
  { scope: 'system_email:send', desc: t('developers.scopes.sendSys') },
]

const endpoints = [
  { method: 'POST', path: '/pool/mailboxes', desc: t('developers.ep.createMb') },
  { method: 'GET', path: '/pool/mailboxes', desc: t('developers.ep.listMb') },
  { method: 'GET', path: '/pool/mailboxes/{id}/emails', desc: t('developers.ep.listMail') },
  { method: 'GET', path: '/pool/mailboxes/{id}/codes/latest', desc: t('developers.ep.latestCode') },
  { method: 'POST', path: '/pool/mailboxes/{id}/extend', desc: t('developers.ep.extend') },
  { method: 'POST', path: '/pool/mailboxes/{id}/restore', desc: t('developers.ep.restore') },
]

const methodClass = (m: string) =>
  m === 'GET' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
    : m === 'POST' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300'
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-bg-dark">
    <!-- Hero -->
    <div class="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-bg-panelDark">
      <div class="max-w-4xl mx-auto px-6 py-12">
        <div class="flex items-center gap-2 text-sm text-primary font-medium mb-3">
          <Zap class="w-4 h-4" />
          {{ t('developers.eyebrow') }}
        </div>
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-3">
          {{ t('developers.title') }}
        </h1>
        <p class="text-gray-500 dark:text-gray-400 max-w-2xl leading-relaxed">
          {{ t('developers.subtitle') }}
        </p>
        <div class="flex flex-wrap gap-3 mt-6">
          <NuxtLink to="/login" class="btn-primary inline-flex items-center gap-2">
            <KeyRound class="w-4 h-4" />
            {{ t('developers.ctaLogin') }}
          </NuxtLink>
          <a href="#quickstart" class="btn-secondary inline-flex items-center gap-2">
            <BookOpen class="w-4 h-4" />
            {{ t('developers.ctaQuickstart') }}
          </a>
        </div>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-6 py-10 space-y-12">
      <!-- Steps -->
      <section id="quickstart" class="space-y-4">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('developers.stepsTitle') }}</h2>
        <ol class="space-y-3">
          <li v-for="(step, i) in [t('developers.step1'), t('developers.step2'), t('developers.step3'), t('developers.step4')]"
            :key="i" class="flex gap-3 items-start">
            <span class="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">{{ i + 1 }}</span>
            <span class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{{ step }}</span>
          </li>
        </ol>
      </section>

      <!-- Auth -->
      <section class="space-y-3">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('developers.authTitle') }}</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ t('developers.authDesc') }}</p>
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-bg-panelDark p-4 font-mono text-sm text-gray-800 dark:text-gray-200">
          Authorization: Bearer tm_xxxxxxxx
        </div>
      </section>

      <!-- Scopes -->
      <section class="space-y-3">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('developers.scopesTitle') }}</h2>
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-bg-panelDark overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 dark:border-gray-700 text-left text-xs text-gray-400 uppercase">
                <th class="px-4 py-2.5 font-medium">{{ t('developers.colScope') }}</th>
                <th class="px-4 py-2.5 font-medium">{{ t('developers.colDesc') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in scopes" :key="s.scope" class="border-b border-gray-50 dark:border-gray-800 last:border-0">
                <td class="px-4 py-2.5 font-mono text-xs text-primary">{{ s.scope }}</td>
                <td class="px-4 py-2.5 text-gray-600 dark:text-gray-300">{{ s.desc }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Endpoints -->
      <section class="space-y-3">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('developers.endpointsTitle') }}</h2>
        <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-bg-panelDark divide-y divide-gray-50 dark:divide-gray-800">
          <div v-for="ep in endpoints" :key="ep.method + ep.path" class="flex items-center gap-3 px-4 py-3">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded shrink-0" :class="methodClass(ep.method)">{{ ep.method }}</span>
            <code class="text-xs font-mono text-gray-800 dark:text-gray-200 flex-1 truncate">{{ ep.path }}</code>
            <span class="text-xs text-gray-500 hidden sm:block">{{ ep.desc }}</span>
          </div>
        </div>
        <p class="text-xs text-gray-400">{{ t('developers.baseHint') }} <code class="font-mono">{{ baseUrl }}</code></p>
      </section>

      <!-- Code samples -->
      <section class="space-y-4">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white inline-flex items-center gap-2">
          <Terminal class="w-5 h-5" /> {{ t('developers.samplesTitle') }}
        </h2>

        <div v-for="sample in [
          { id: 'curl', label: 'curl', code: curlSample },
          { id: 'py', label: 'Python', code: pythonSample },
          { id: 'node', label: 'Node.js', code: nodeSample },
        ]" :key="sample.id" class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-bg-panelDark overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-800/40">
            <span class="text-xs font-semibold text-gray-600 dark:text-gray-300">{{ sample.label }}</span>
            <button class="text-xs text-gray-500 hover:text-primary inline-flex items-center gap-1" @click="copy(sample.id, sample.code)">
              <Check v-if="copied === sample.id" class="w-3.5 h-3.5 text-green-500" />
              <Copy v-else class="w-3.5 h-3.5" />
              {{ copied === sample.id ? t('developers.copied') : t('developers.copy') }}
            </button>
          </div>
          <pre class="p-4 text-xs font-mono text-gray-800 dark:text-gray-200 overflow-x-auto whitespace-pre">{{ sample.code }}</pre>
        </div>
        <p class="text-xs text-gray-400">{{ t('developers.sdkHint') }}</p>
      </section>

      <!-- Rate limit -->
      <section class="space-y-3">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('developers.ratelimitTitle') }}</h2>
        <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-1.5 list-disc pl-5">
          <li>{{ t('developers.rl1') }}</li>
          <li>{{ t('developers.rl2') }}</li>
          <li>{{ t('developers.rl3') }}</li>
        </ul>
      </section>

      <!-- Footer nav -->
      <section class="pt-4 border-t border-gray-200 dark:border-gray-800 flex flex-wrap gap-4 text-sm">
        <NuxtLink to="/login" class="text-primary hover:underline inline-flex items-center gap-1">
          {{ t('developers.backApp') }} <ExternalLink class="w-3.5 h-3.5" />
        </NuxtLink>
      </section>
    </div>
  </div>
</template>

<style scoped>
.btn-primary {
  @apply px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors font-medium;
}
.btn-secondary {
  @apply px-4 py-2 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors font-medium;
}
</style>
