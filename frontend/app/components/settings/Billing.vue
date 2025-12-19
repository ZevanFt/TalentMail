<script setup lang="ts">
import { Plus, Trash2, Copy, Check, Package, Ticket, RefreshCw, Ban } from 'lucide-vue-next'

const { getPlans, createPlan, updatePlan, deletePlan: deletePlanApi, getRedemptionCodes, generateRedemptionCodes, getRedemptionCodeStats, revokeRedemptionCode } = useApi()

// ==================== 类型定义 ====================
interface Plan {
    id: number
    name: string
    price_monthly: string
    price_yearly: string
    storage_quota_bytes: number
    max_domains: number
    max_aliases: number
    allow_temp_mail: boolean
    max_temp_mailboxes: number
    features: Record<string, boolean>
}

interface RedemptionCode {
    id: number
    code: string
    plan_id: number
    duration_days: number
    status: string
    created_at: string
    expires_at: string | null
    used_at: string | null
    used_by_email: string | null
}

interface CodeStats {
    total: number
    unused: number
    used: number
    expired: number
}

// ==================== 状态 ====================
const activeSection = ref<'plans' | 'codes'>('plans')
const plans = ref<Plan[]>([])
const codes = ref<RedemptionCode[]>([])
const codeStats = ref<CodeStats>({ total: 0, unused: 0, used: 0, expired: 0 })
const loading = ref(false)
const copiedId = ref<number | null>(null)

// 套餐表单
const showPlanModal = ref(false)
const editingPlan = ref<Plan | null>(null)
const planForm = reactive({
    name: '',
    price_monthly: 0,
    price_yearly: 0,
    storage_quota_gb: 1,
    max_domains: 0,
    max_aliases: 5,
    allow_temp_mail: true,
    max_temp_mailboxes: 3,
})

// 兑换码表单
const codeForm = reactive({
    plan_id: 0,
    duration_days: 30,
    count: 1,
    prefix: '',
})
const generatedCodes = ref<string[]>([])
const showGeneratedModal = ref(false)

// ==================== API 调用 ====================
const loadPlans = async () => {
    try {
        plans.value = await getPlans()
        if (plans.value.length > 0 && !codeForm.plan_id) {
            codeForm.plan_id = plans.value[0]?.id || 0
        }
    } catch (e) {
        console.error('加载套餐失败', e)
    }
}

const loadCodes = async () => {
    loading.value = true
    try {
        const [codesData, statsData] = await Promise.all([
            getRedemptionCodes(),
            getRedemptionCodeStats(),
        ])
        codes.value = codesData
        codeStats.value = statsData
    } catch (e) {
        console.error('加载兑换码失败', e)
    } finally {
        loading.value = false
    }
}

const savePlan = async () => {
    try {
        const data = {
            name: planForm.name,
            price_monthly: planForm.price_monthly,
            price_yearly: planForm.price_yearly,
            storage_quota_bytes: planForm.storage_quota_gb * 1024 * 1024 * 1024,
            max_domains: planForm.max_domains,
            max_aliases: planForm.max_aliases,
            allow_temp_mail: planForm.allow_temp_mail,
            max_temp_mailboxes: planForm.max_temp_mailboxes,
        }
        if (editingPlan.value) {
            await updatePlan(editingPlan.value.id, data)
        } else {
            await createPlan(data)
        }
        showPlanModal.value = false
        await loadPlans()
    } catch (e: any) {
        alert(e.data?.detail || '保存失败')
    }
}

const handleDeletePlan = async (plan: Plan) => {
    if (!confirm(`确定删除套餐 "${plan.name}"？`)) return
    try {
        await deletePlanApi(plan.id)
        await loadPlans()
    } catch (e: any) {
        alert(e.data?.detail || '删除失败')
    }
}

const generateCodes = async () => {
    try {
        const result = await generateRedemptionCodes(codeForm)
        generatedCodes.value = result.codes
        showGeneratedModal.value = true
        await loadCodes()
    } catch (e: any) {
        alert(e.data?.detail || '生成失败')
    }
}

const revokeCode = async (code: RedemptionCode) => {
    if (!confirm('确定作废此兑换码？')) return
    try {
        await revokeRedemptionCode(code.id)
        await loadCodes()
    } catch (e: any) {
        alert(e.data?.detail || '操作失败')
    }
}

const copyCode = async (code: RedemptionCode) => {
    await navigator.clipboard.writeText(code.code)
    copiedId.value = code.id
    setTimeout(() => copiedId.value = null, 2000)
}

const copyAllCodes = async () => {
    await navigator.clipboard.writeText(generatedCodes.value.join('\n'))
}

// ==================== 辅助函数 ====================
const openPlanModal = (plan?: Plan) => {
    if (plan) {
        editingPlan.value = plan
        planForm.name = plan.name
        planForm.price_monthly = parseFloat(plan.price_monthly)
        planForm.price_yearly = parseFloat(plan.price_yearly)
        planForm.storage_quota_gb = Math.round(plan.storage_quota_bytes / 1024 / 1024 / 1024)
        planForm.max_domains = plan.max_domains
        planForm.max_aliases = plan.max_aliases
        planForm.allow_temp_mail = plan.allow_temp_mail
        planForm.max_temp_mailboxes = plan.max_temp_mailboxes
    } else {
        editingPlan.value = null
        Object.assign(planForm, {
            name: '',
            price_monthly: 0,
            price_yearly: 0,
            storage_quota_gb: 1,
            max_domains: 0,
            max_aliases: 5,
            allow_temp_mail: true,
            max_temp_mailboxes: 3,
        })
    }
    showPlanModal.value = true
}

const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) return `${Math.round(bytes / 1024 / 1024 / 1024)} GB`
    if (bytes >= 1024 * 1024) return `${Math.round(bytes / 1024 / 1024)} MB`
    return `${bytes} B`
}

const formatDate = (date: string | null) => {
    if (!date) return '-'
    return new Date(date).toLocaleDateString('zh-CN')
}

const getPlanName = (planId: number) => {
    return plans.value.find(p => p.id === planId)?.name || '未知'
}

const getStatusBadge = (status: string) => {
    switch (status) {
        case 'unused': return { text: '未使用', class: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' }
        case 'used': return { text: '已使用', class: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400' }
        case 'expired': return { text: '已过期', class: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' }
        default: return { text: status, class: 'bg-gray-100 text-gray-700' }
    }
}

onMounted(async () => {
    await loadPlans()
    await loadCodes()
})
</script>

<template>
    <div class="space-y-8">
        <h2 class="section-title">会员订阅管理</h2>

        <!-- 切换标签 -->
        <div class="flex gap-2 border-b border-gray-200 dark:border-gray-700">
            <button @click="activeSection = 'plans'" :class="['tab-item', activeSection === 'plans' ? 'active' : '']">
                <Package class="w-4 h-4" /> 套餐管理
            </button>
            <button @click="activeSection = 'codes'" :class="['tab-item', activeSection === 'codes' ? 'active' : '']">
                <Ticket class="w-4 h-4" /> 兑换码管理
            </button>
        </div>

        <!-- 套餐管理 -->
        <div v-if="activeSection === 'plans'" class="space-y-6">
            <div class="flex justify-between items-center">
                <p class="text-gray-500 text-sm">管理系统中的订阅套餐，所有套餐数据存储在数据库中</p>
                <button @click="openPlanModal()" class="btn-primary flex items-center gap-2">
                    <Plus class="w-4 h-4" /> 新建套餐
                </button>
            </div>

            <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div v-for="plan in plans" :key="plan.id"
                    class="card p-5 hover:shadow-lg transition-shadow cursor-pointer" @click="openPlanModal(plan)">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="font-bold text-lg text-gray-900 dark:text-white">{{ plan.name }}</h3>
                        <button @click.stop="handleDeletePlan(plan)" class="icon-btn text-red-500" title="删除">
                            <Trash2 class="w-4 h-4" />
                        </button>
                    </div>
                    <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                        <div class="flex justify-between">
                            <span>月付</span>
                            <span class="font-medium text-gray-900 dark:text-white">¥{{ plan.price_monthly }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>年付</span>
                            <span class="font-medium text-gray-900 dark:text-white">¥{{ plan.price_yearly }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>存储空间</span>
                            <span>{{ formatBytes(plan.storage_quota_bytes) }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>临时邮箱</span>
                            <span>{{ plan.max_temp_mailboxes }} 个</span>
                        </div>
                        <div class="flex justify-between">
                            <span>别名数量</span>
                            <span>{{ plan.max_aliases }} 个</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 兑换码管理 -->
        <div v-if="activeSection === 'codes'" class="space-y-6">
            <!-- 统计卡片 -->
            <div class="grid grid-cols-4 gap-4">
                <div class="card p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ codeStats.total }}</div>
                    <div class="text-sm text-gray-500">总计</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-2xl font-bold text-green-600">{{ codeStats.unused }}</div>
                    <div class="text-sm text-gray-500">未使用</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-2xl font-bold text-gray-600">{{ codeStats.used }}</div>
                    <div class="text-sm text-gray-500">已使用</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-2xl font-bold text-red-600">{{ codeStats.expired }}</div>
                    <div class="text-sm text-gray-500">已过期</div>
                </div>
            </div>

            <!-- 生成兑换码 -->
            <div class="card p-6">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">批量生成兑换码</h3>
                <div class="flex flex-wrap gap-x-4 gap-y-2 items-end">
                    <div class="flex items-center gap-2">
                        <label class="text-sm text-gray-500 whitespace-nowrap">套餐</label>
                        <select v-model="codeForm.plan_id" class="input-field w-32">
                            <option v-for="plan in plans" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="text-sm text-gray-500 whitespace-nowrap">有效天数</label>
                        <input v-model.number="codeForm.duration_days" type="number" min="1" class="input-field w-20">
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="text-sm text-gray-500 whitespace-nowrap">生成数量</label>
                        <input v-model.number="codeForm.count" type="number" min="1" max="100" class="input-field w-16">
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="text-sm text-gray-500 whitespace-nowrap">前缀（可选）</label>
                        <input v-model="codeForm.prefix" type="text" class="input-field w-24" placeholder="如 PRO">
                    </div>
                    <button @click="generateCodes" class="btn-primary flex items-center gap-2 h-[38px]">
                        <Plus class="w-4 h-4" /> 生成
                    </button>
                </div>
            </div>

            <!-- 兑换码列表 -->
            <div class="card overflow-hidden">
                <div class="flex justify-between items-center p-4 border-b border-gray-100 dark:border-gray-800">
                    <h3 class="font-bold text-gray-900 dark:text-white">兑换码列表</h3>
                    <button @click="loadCodes" class="icon-btn" title="刷新">
                        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
                    </button>
                </div>
                <div v-if="loading" class="p-8 text-center text-gray-500">加载中...</div>
                <div v-else-if="codes.length === 0" class="p-8 text-center text-gray-500">暂无兑换码</div>
                <table v-else class="w-full">
                    <thead class="bg-gray-50 dark:bg-gray-800/50">
                        <tr>
                            <th class="th">兑换码</th>
                            <th class="th">套餐</th>
                            <th class="th">天数</th>
                            <th class="th">状态</th>
                            <th class="th">使用者</th>
                            <th class="th">创建时间</th>
                            <th class="th">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                        <tr v-for="code in codes" :key="code.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                            <td class="td">
                                <code class="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono">{{
                                    code.code }}</code>
                            </td>
                            <td class="td">{{ getPlanName(code.plan_id) }}</td>
                            <td class="td">{{ code.duration_days }} 天</td>
                            <td class="td">
                                <span :class="['px-2 py-0.5 rounded-full text-xs', getStatusBadge(code.status).class]">
                                    {{ getStatusBadge(code.status).text }}
                                </span>
                            </td>
                            <td class="td text-gray-500 text-xs">{{ code.used_by_email || '-' }}</td>
                            <td class="td text-gray-500">{{ formatDate(code.created_at) }}</td>
                            <td class="td">
                                <div class="flex gap-2">
                                    <button @click="copyCode(code)" class="icon-btn" title="复制">
                                        <Check v-if="copiedId === code.id" class="w-4 h-4 text-green-500" />
                                        <Copy v-else class="w-4 h-4" />
                                    </button>
                                    <button v-if="code.status === 'unused'" @click="revokeCode(code)"
                                        class="icon-btn text-red-500" title="作废">
                                        <Ban class="w-4 h-4" />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 套餐编辑弹窗 -->
        <CommonModal v-model="showPlanModal" :title="editingPlan ? '编辑套餐' : '新建套餐'">
            <div class="space-y-4">
                <div class="space-y-1">
                    <label class="text-sm font-medium text-gray-700 dark:text-gray-300">套餐名称</label>
                    <input v-model="planForm.name" type="text" class="input-field w-full" placeholder="如 Pro">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">月付价格 (¥)</label>
                        <input v-model.number="planForm.price_monthly" type="number" min="0" step="0.01"
                            class="input-field w-full">
                    </div>
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">年付价格 (¥)</label>
                        <input v-model.number="planForm.price_yearly" type="number" min="0" step="0.01"
                            class="input-field w-full">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">存储空间 (GB)</label>
                        <input v-model.number="planForm.storage_quota_gb" type="number" min="1"
                            class="input-field w-full">
                    </div>
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">临时邮箱数量</label>
                        <input v-model.number="planForm.max_temp_mailboxes" type="number" min="0"
                            class="input-field w-full">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">别名数量</label>
                        <input v-model.number="planForm.max_aliases" type="number" min="0" class="input-field w-full">
                    </div>
                    <div class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">域名数量</label>
                        <input v-model.number="planForm.max_domains" type="number" min="0" class="input-field w-full">
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <input v-model="planForm.allow_temp_mail" type="checkbox" id="allow_temp_mail"
                        class="w-4 h-4 rounded border-gray-300">
                    <label for="allow_temp_mail" class="text-sm text-gray-700 dark:text-gray-300">允许使用临时邮箱</label>
                </div>
            </div>
            <template #footer>
                <button @click="showPlanModal = false" class="btn-secondary">取消</button>
                <button @click="savePlan" class="btn-primary">保存</button>
            </template>
        </CommonModal>

        <!-- 生成成功弹窗 -->
        <CommonModal v-model="showGeneratedModal" title="兑换码生成成功">
            <div class="space-y-4">
                <p class="text-sm text-gray-500">已生成 {{ generatedCodes.length }} 个兑换码：</p>
                <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-h-60 overflow-y-auto">
                    <div v-for="code in generatedCodes" :key="code" class="font-mono text-sm py-1">{{ code }}</div>
                </div>
            </div>
            <template #footer>
                <button @click="copyAllCodes" class="btn-secondary flex items-center gap-2">
                    <Copy class="w-4 h-4" /> 复制全部
                </button>
                <button @click="showGeneratedModal = false" class="btn-primary">关闭</button>
            </template>
        </CommonModal>
    </div>
</template>

<style scoped>
.section-title {
    @apply text-2xl font-bold text-gray-900 dark:text-white mb-6;
}

.card {
    @apply bg-white dark:bg-bg-panelDark rounded-xl border border-gray-200 dark:border-border-dark;
}

.tab-item {
    @apply flex items-center gap-2 px-4 py-3 text-sm font-medium text-gray-500 border-b-2 border-transparent hover:text-gray-700 dark:hover:text-gray-300 transition-colors;
}

.tab-item.active {
    @apply text-primary border-primary;
}

.input-field {
    @apply px-3 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all text-gray-900 dark:text-white;
}

.btn-primary {
    @apply px-4 py-2 bg-primary text-white text-sm rounded-lg hover:bg-primary-hover transition-colors shadow-sm shadow-primary/20 disabled:opacity-50;
}

.btn-secondary {
    @apply px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors;
}

.th {
    @apply px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider;
}

.td {
    @apply px-4 py-3 text-sm text-gray-900 dark:text-white;
}

.icon-btn {
    @apply p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500;
}
</style>