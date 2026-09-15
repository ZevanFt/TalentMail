/** 词典组装：基础词典 + 各命名空间片段深合并。
 *
 * 片段由 i18n 迁移按命名空间独立维护（fragments/*.zh.ts / *.en.ts），
 * 文件内容即对应命名空间的子对象，这里负责包上命名空间再合并。
 */
import zhCN from './zh-CN'
import enUS from './en-US'
import settingsZh from './fragments/settings.zh'
import settingsEn from './fragments/settings.en'
import adminZh from './fragments/admin.zh'
import adminEn from './fragments/admin.en'
import adminToolsZh from './fragments/adminTools.zh'
import adminToolsEn from './fragments/adminTools.en'
import settingsSecurityZh from './fragments/settingsSecurity.zh'
import settingsSecurityEn from './fragments/settingsSecurity.en'
import mailZh from './fragments/mail.zh'
import mailEn from './fragments/mail.en'
import workflowsZh from './fragments/workflows.zh'
import workflowsEn from './fragments/workflows.en'
import layoutZh from './fragments/layout.zh'
import layoutEn from './fragments/layout.en'
import drivePagesZh from './fragments/drivePages.zh'
import drivePagesEn from './fragments/drivePages.en'
import authPagesZh from './fragments/authPages.zh'
import authPagesEn from './fragments/authPages.en'
import miscZh from './fragments/misc.zh'
import miscEn from './fragments/misc.en'

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

function deepMerge<T extends Record<string, unknown>>(base: T, patch: Record<string, unknown>): T {
  const out: Record<string, unknown> = { ...base }
  for (const [key, value] of Object.entries(patch)) {
    const existing = out[key]
    if (isPlainObject(existing) && isPlainObject(value)) {
      out[key] = deepMerge(existing, value)
    } else {
      out[key] = value
    }
  }
  return out as T
}

export const zhCNFull = deepMerge(
  deepMerge(
    deepMerge(zhCN, {
      settings: settingsZh,
      admin: adminZh,
      adminTools: adminToolsZh,
      settingsSecurity: settingsSecurityZh,
      mail: mailZh,
      workflows: workflowsZh,
    }),
    layoutZh
  ),
  deepMerge(drivePagesZh, deepMerge(authPagesZh, miscZh))
)

export const enUSFull = deepMerge(
  deepMerge(
    deepMerge(enUS, {
      settings: settingsEn,
      admin: adminEn,
      adminTools: adminToolsEn,
      settingsSecurity: settingsSecurityEn,
      mail: mailEn,
      workflows: workflowsEn,
    }),
    layoutEn
  ),
  deepMerge(drivePagesEn, deepMerge(authPagesEn, miscEn))
)

export default { zhCNFull, enUSFull }
