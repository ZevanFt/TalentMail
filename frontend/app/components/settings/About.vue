<script setup lang="ts">
import { Mail, Shield, Users, Inbox, Palette, Heart } from 'lucide-vue-next'

const { t } = useI18n()

const version = '1.0.0'
const buildDate = '2025'

const features = computed(() => [
  { icon: Mail, title: t('settings.about.features.mail.title'), desc: t('settings.about.features.mail.desc') },
  { icon: Shield, title: t('settings.about.features.security.title'), desc: t('settings.about.features.security.desc') },
  { icon: Users, title: t('settings.about.features.users.title'), desc: t('settings.about.features.users.desc') },
  { icon: Inbox, title: t('settings.about.features.pool.title'), desc: t('settings.about.features.pool.desc') },
  { icon: Palette, title: t('settings.about.features.theme.title'), desc: t('settings.about.features.theme.desc') },
])

const techStack = [
  { name: 'Nuxt.js 3', typeKey: 'settings.about.techTypes.frontend' },
  { name: 'FastAPI', typeKey: 'settings.about.techTypes.backend' },
  { name: 'PostgreSQL', typeKey: 'settings.about.techTypes.database' },
  { name: 'docker-mailserver', typeKey: 'settings.about.techTypes.mailServer' },
  { name: 'Caddy', typeKey: 'settings.about.techTypes.reverseProxy' },
]
</script>

<template>
  <div class="space-y-8">
    <!-- 标题 -->
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
        <Heart class="w-5 h-5 text-primary" />
      </div>
      <div>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ t('settings.tabs.about') }} TalentMail</h2>
        <p class="text-sm text-gray-500">{{ t('settings.about.subtitle') }}</p>
      </div>
    </div>

    <!-- 产品信息 -->
    <div class="card bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark p-8">
      <div class="flex items-center gap-6">
        <img src="/logo.png" alt="Talenting Logo" class="h-24 shrink-0" />
        <div>
          <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">TalentMail</h3>
          <p class="text-gray-500 dark:text-gray-400 mb-3">{{ t('settings.about.tagline') }}</p>
          <div class="flex items-center gap-4 text-sm text-gray-400">
            <span>{{ t('settings.about.version', { v: version }) }}</span>
            <span>•</span>
            <span>© {{ buildDate }} Talenting</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能特性 -->
    <div class="card bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('settings.about.featuresTitle') }}</h3>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div v-for="feature in features" :key="feature.title"
          class="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50">
          <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <component :is="feature.icon" class="w-5 h-5 text-primary" />
          </div>
          <div>
            <div class="font-medium text-gray-900 dark:text-white text-sm">{{ feature.title }}</div>
            <div class="text-xs text-gray-500">{{ feature.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 技术栈 -->
    <div class="card bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-200 dark:border-border-dark p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('settings.about.techStackTitle') }}</h3>
      <div class="flex flex-wrap gap-2">
        <div v-for="tech in techStack" :key="tech.name"
          class="px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 text-sm">
          <span class="font-medium text-gray-900 dark:text-white">{{ tech.name }}</span>
          <span class="text-gray-400 ml-1">{{ t(tech.typeKey) }}</span>
        </div>
      </div>
    </div>

    <!-- 版权声明 -->
    <div class="card bg-gradient-to-r from-primary/5 to-purple-500/5 rounded-2xl border border-primary/10 p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">{{ t('settings.about.copyrightTitle') }}</h3>
      <div class="text-sm text-gray-600 dark:text-gray-400 space-y-2">
        <p>Copyright © 2025 Talenting. All Rights Reserved.</p>
        <p>{{ t('settings.about.copyrightPrivate') }}</p>
        <p class="text-primary font-medium">{{ t('settings.about.author') }}</p>
      </div>
    </div>

    <!-- 底部 -->
    <div class="text-center text-sm text-gray-400 py-4">
      {{ t('settings.about.madeWith') }} <Heart class="w-4 h-4 inline text-red-500" /> by 且试新茶趁年华 @ Talenting
    </div>
  </div>
</template>
