<script setup lang="ts">
import { Search, Plus, RefreshCw, Copy, Mail, History, BarChart, Trash2, Star, Box, ArrowLeft } from 'lucide-vue-next'
const { isGenerateOpen, isHistoryOpen, isStatsOpen } = useGlobalModal()
const router = useRouter()

definePageMeta({ layout: 'pool' })

const accounts = ref([
    { id: 'T', email: 'test001@mymail.com', lastUsed: '刚刚', active: true, color: 'bg-purple-500' },
    { id: 'R', email: 'register02@mymail.com', lastUsed: '5分钟前', active: true, color: 'bg-gray-400' },
    { id: 'S', email: 'signup@mymail.com', lastUsed: '1小时前', active: true, color: 'bg-gray-400' }
])
const selectedAccount = ref(accounts.value[0])

const messages = ref([
    { id: 1, sender: 'Steam', code: '847291', time: '刚刚', read: false },
    { id: 2, sender: 'Discord', code: '582034', time: '2分钟前', read: true },
    { id: 3, sender: 'Twitter', code: 'KC84HT', time: '10分钟前', read: true }
])
const selectedMessage = ref(messages.value[0])
</script>

<template>
    <div class="flex w-full h-full bg-white dark:bg-bg-dark overflow-hidden">

        <!-- 第一栏：账号列表 -->
        <!-- 修改点：w-64 (256px) 对应主页 Sidebar -->
        <div
            class="w-64 h-full bg-gray-50/80 dark:bg-bg-panelDark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">

            <!-- 顶部 Header -->
            <div class="h-14 flex items-center px-4 gap-3 border-b border-gray-200/50 dark:border-gray-800 shrink-0">
                <button @click="router.push('/')"
                    class="p-2 -ml-2 text-gray-500 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                    <ArrowLeft class="w-5 h-5" />
                </button>
                <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <Box class="w-5 h-5 text-primary" />
                    账号池
                </div>
            </div>

            <!-- 搜索 -->
            <div class="p-3 pb-2">
                <div class="relative">
                    <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input type="text" placeholder="搜索账号..."
                        class="w-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg py-1.5 pl-9 pr-4 text-xs focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all">
                </div>
            </div>

            <!-- 列表 -->
            <div class="flex-1 overflow-y-auto px-2 space-y-1 py-2 custom-scrollbar">
                <div v-for="acc in accounts" :key="acc.email" @click="selectedAccount = acc"
                    class="p-3 rounded-xl cursor-pointer hover:bg-white dark:hover:bg-gray-800 transition-all border border-transparent hover:border-gray-200 dark:hover:border-gray-700 relative group"
                    :class="{ 'bg-white dark:bg-gray-800 shadow-sm border-gray-200 dark:border-gray-700': selectedAccount.email === acc.email }">
                    <div v-if="selectedAccount.email === acc.email"
                        class="absolute left-0 top-3 bottom-3 w-1 bg-primary rounded-r-full"></div>
                    <div class="flex items-center gap-3 pl-2">
                        <div
                            :class="`w-8 h-8 rounded-full ${acc.color} text-white flex items-center justify-center font-bold text-xs shrink-0`">
                            {{ acc.id }}
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ acc.email }}</div>
                            <div class="flex items-center justify-between mt-0.5">
                                <span class="text-[10px] text-gray-400">创建于 {{ acc.lastUsed }}</span>
                                <RefreshCw v-if="selectedAccount.email === acc.email" class="w-3 h-3 text-gray-400" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 底部统计 -->
            <div
                class="p-3 border-t border-gray-200 dark:border-gray-800 flex justify-between text-[10px] text-gray-400 bg-gray-100/50 dark:bg-gray-900/50">
                <span>3 个活跃账号</span>
                <span>共 12 封邮件</span>
            </div>
        </div>

        <!-- 第二栏：邮件列表 -->
        <!-- 修改点：w-80 (320px) 对应主页 EmailList -->
        <div
            class="w-80 h-full bg-white dark:bg-bg-dark border-r border-gray-200 dark:border-border-dark flex flex-col shrink-0">

            <div
                class="h-14 flex items-center justify-between px-5 border-b border-gray-100 dark:border-gray-800 shrink-0 bg-gray-50/30 dark:bg-gray-900/30">
                <div class="flex items-center gap-3 min-w-0">
                    <div
                        class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white font-bold shrink-0 text-xs">
                        {{ selectedAccount.id }}</div>
                    <div class="min-w-0">
                        <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ selectedAccount.email
                            }}</div>
                    </div>
                </div>
                <button class="text-gray-400 hover:text-primary transition-colors">
                    <RefreshCw class="w-4 h-4" />
                </button>
            </div>

            <div class="flex-1 overflow-y-auto">
                <div v-for="msg in messages" :key="msg.id" @click="selectedMessage = msg"
                    class="px-5 py-4 border-b border-gray-50 dark:border-gray-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors relative"
                    :class="{ 'bg-purple-50/40 dark:bg-gray-800/60': selectedMessage.id === msg.id }">
                    <div class="flex items-center justify-between mb-1">
                        <div class="flex items-center gap-2">
                            <div class="w-2 h-2 rounded-full bg-primary" v-if="!msg.read"></div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ msg.sender }}</div>
                        </div>
                        <span class="text-xs text-gray-400">{{ msg.time }}</span>
                    </div>
                    <div class="text-xs text-gray-500 mb-2">验证码 {{ msg.code }}</div>
                    <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-primary/10 text-primary text-xs font-bold font-mono rounded">{{
                            msg.code }}</span>
                        <Copy class="w-3 h-3 text-gray-400" />
                    </div>
                </div>
            </div>
        </div>

        <!-- 第三栏：详情 -->
        <div class="flex-1 h-full bg-gray-50/30 dark:bg-bg-panelDark flex flex-col min-w-0">

            <div
                class="h-14 border-b border-gray-200 dark:border-border-dark flex items-center justify-end px-6 gap-3 shrink-0 bg-white dark:bg-bg-dark">
                <button @click="isHistoryOpen = true" class="btn-tool">
                    <History class="w-4 h-4" /> 历史
                </button>
                <button @click="isStatsOpen = true" class="btn-tool">
                    <BarChart class="w-4 h-4" /> 统计
                </button>
                <button @click="isGenerateOpen = true"
                    class="flex items-center gap-2 px-4 py-1.5 bg-primary text-white rounded-lg hover:bg-primary-hover shadow-md shadow-primary/20 transition-all font-medium text-sm ml-2">
                    <Plus class="w-4 h-4" /> 生成临时邮箱
                </button>
            </div>

            <div class="flex-1 p-10 overflow-y-auto flex flex-col">
                <template v-if="selectedMessage">
                    <div class="flex items-start justify-between mb-10">
                        <div class="flex items-center gap-4">
                            <div
                                class="w-14 h-14 rounded-full bg-primary flex items-center justify-center text-2xl text-white font-bold shadow-lg shadow-primary/20">
                                {{ selectedMessage.sender[0] }}</div>
                            <div>
                                <div class="text-2xl font-bold text-gray-900 dark:text-white mb-1">{{
                                    selectedMessage.sender }}</div>
                                <div class="text-sm text-gray-400">{{ selectedMessage.time }}</div>
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <button class="icon-btn">
                                <Star class="w-5 h-5" />
                            </button>
                            <button class="icon-btn">
                                <Trash2 class="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                    <div class="font-bold text-gray-900 dark:text-white mb-4">验证码 {{ selectedMessage.code }}</div>
                    <div
                        class="bg-purple-50/50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-900/30 rounded-2xl p-12 flex flex-col items-center justify-center relative overflow-hidden group border-dashed">
                        <div class="text-sm text-gray-500 mb-4">验证码 (已自动识别)</div>
                        <div class="text-7xl font-mono font-bold text-primary tracking-widest mb-8 drop-shadow-sm">{{
                            selectedMessage.code }}</div>
                        <button
                            class="flex items-center gap-2 px-8 py-3 bg-primary text-white rounded-xl hover:bg-primary-hover shadow-xl shadow-primary/30 transition-all active:scale-95 text-lg font-medium">
                            <Copy class="w-5 h-5" /> 复制
                        </button>
                    </div>
                </template>
                <template v-else>
                    <div class="flex-1 flex flex-col items-center justify-center text-gray-400">
                        <Mail class="w-20 h-20 opacity-10 mb-6" />
                        <p class="text-lg">选择一封邮件查看验证码</p>
                    </div>
                </template>
            </div>
        </div>

        <!-- 弹窗 -->
        <PoolCreateModal />
        <PoolHistoryModal />
        <PoolStatsModal />
    </div>
</template>

<style scoped>
.btn-tool {
    @apply flex items-center gap-2 px-3 py-1.5 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-sm transition-colors border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900;
}

.icon-btn {
    @apply p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400 transition-colors;
}
</style>