<script setup lang="ts">
import { Mail, Shield, Users, Inbox, Palette, Heart } from 'lucide-vue-next'

const version = '1.0.0'
const buildDate = '2025'

const features = [
  { icon: Mail, title: '邮件收发', desc: 'SMTP/IMAP 完整支持' },
  { icon: Shield, title: '安全认证', desc: 'JWT + 2FA 双重保护' },
  { icon: Users, title: '用户管理', desc: '邀请码 + 会员订阅' },
  { icon: Inbox, title: '账号池', desc: '临时邮箱 + 验证码识别' },
  { icon: Palette, title: '主题切换', desc: '深色/浅色自适应' },
]

const techStack = [
  { name: 'Nuxt.js 3', type: '前端框架' },
  { name: 'FastAPI', type: '后端框架' },
  { name: 'PostgreSQL', type: '数据库' },
  { name: 'docker-mailserver', type: '邮件服务' },
  { name: 'Caddy', type: '反向代理' },
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
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">关于 TalentMail</h2>
        <p class="text-sm text-gray-500">现代化自托管邮件服务平台</p>
      </div>
    </div>

    <!-- Logo 和版本信息 -->
    <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-100 dark:border-border-dark p-8">
      <div class="flex flex-col items-center text-center">
        <img src="/logo.png" alt="Talenting Logo" class="h-16 mb-4" />
        <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">TalentMail</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">一个功能完整、安全可靠的企业级邮件解决方案</p>
        <div class="flex items-center gap-4 text-sm text-gray-400">
          <span>版本 {{ version }}</span>
          <span>•</span>
          <span>© {{ buildDate }} Talenting</span>
        </div>
      </div>
    </div>

    <!-- 功能特性 -->
    <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-100 dark:border-border-dark p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">功能特性</h3>
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
    <div class="bg-white dark:bg-bg-panelDark rounded-2xl border border-gray-100 dark:border-border-dark p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">技术栈</h3>
      <div class="flex flex-wrap gap-2">
        <div v-for="tech in techStack" :key="tech.name"
          class="px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 text-sm">
          <span class="font-medium text-gray-900 dark:text-white">{{ tech.name }}</span>
          <span class="text-gray-400 ml-1">{{ tech.type }}</span>
        </div>
      </div>
    </div>

    <!-- 版权声明 -->
    <div class="bg-gradient-to-r from-primary/5 to-purple-500/5 rounded-2xl border border-primary/10 p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">版权声明</h3>
      <div class="text-sm text-gray-600 dark:text-gray-400 space-y-2">
        <p>Copyright © 2025 Talenting. All Rights Reserved.</p>
        <p>本项目为私有项目，保留所有权利。未经授权，禁止复制、修改、分发或使用本项目的任何部分。</p>
        <p class="text-primary font-medium">作者: Zevan</p>
      </div>
    </div>

    <!-- 底部 -->
    <div class="text-center text-sm text-gray-400 py-4">
      Made with <Heart class="w-4 h-4 inline text-red-500" /> by Zevan @ Talenting
    </div>
  </div>
</template>