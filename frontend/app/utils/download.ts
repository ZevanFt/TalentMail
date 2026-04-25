/**
 * 安全文件下载工具
 * 使用 Authorization header 而不是 URL 中的 token，防止 JWT 泄漏
 */
export const secureDownload = async (url: string, filename?: string) => {
  const token = useCookie('token')
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token.value}` },
  })
  if (!res.ok) throw new Error(`下载失败: ${res.status}`)
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename || url.split('/').pop()?.split('?')[0] || 'download'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(a.href)
}
