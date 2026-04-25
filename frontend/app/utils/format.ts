/**
 * 通用格式化工具函数
 * Nuxt 3 会自动导入 utils/ 目录下的顶层导出
 */

/** 格式化文件大小 (bytes → 可读字符串) */
export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

/** formatFileSize 的别名，兼容已有代码 */
export const formatSize = formatFileSize

/** 格式化日期 (ISO → yyyy/MM/dd) */
export const formatDate = (date: string | null): string => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

/** 格式化日期时间 (ISO → yyyy/MM/dd HH:mm:ss) */
export const formatDateTime = (date: string | null): string => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

/** 获取发件人首字母头像 */
export const getAvatar = (sender: string): string => {
  if (!sender) return '?'
  const match = sender.match(/^([^<]+)/) || sender.match(/<([^>]+)>/)
  const name = match?.[1]?.trim() || sender
  return name.charAt(0).toUpperCase()
}
