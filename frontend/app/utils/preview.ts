/**
 * 文件预览工具函数
 * 与后端 PREVIEWABLE_TYPES 保持同步
 * Nuxt 自动导入 utils/ 下的导出
 */

const PREVIEWABLE_TYPES = new Set([
  'application/pdf',
  'text/plain', 'text/markdown', 'text/csv',
  'application/json', 'application/xml', 'text/xml',
  'text/css', 'text/javascript', 'application/javascript',
])

/** 判断文件是否可安全预览 */
export const isPreviewable = (contentType: string | null): boolean => {
  if (!contentType) return false
  const ct = contentType.toLowerCase().split(';')[0].trim()
  // 图片（排除 SVG — XSS 风险）
  if (ct.startsWith('image/') && ct !== 'image/svg+xml') return true
  return PREVIEWABLE_TYPES.has(ct)
}

/** 预览类型 */
export type PreviewType = 'image' | 'pdf' | 'text' | 'unsupported'

/** 获取文件的预览类型 */
export const getPreviewType = (contentType: string | null): PreviewType => {
  if (!contentType) return 'unsupported'
  const ct = contentType.toLowerCase().split(';')[0].trim()
  if (ct.startsWith('image/') && ct !== 'image/svg+xml') return 'image'
  if (ct === 'application/pdf') return 'pdf'
  if (PREVIEWABLE_TYPES.has(ct)) return 'text'
  return 'unsupported'
}
