import { File, FileText, Image, Film, Music, Archive } from 'lucide-vue-next'
import type { Component } from 'vue'

/**
 * 根据 MIME 类型返回对应的 Lucide 图标组件
 */
export const getFileIcon = (contentType: string | null): Component => {
  if (!contentType) return File
  if (contentType.startsWith('image/')) return Image
  if (contentType.startsWith('video/')) return Film
  if (contentType.startsWith('audio/')) return Music
  if (contentType.includes('zip') || contentType.includes('rar') || contentType.includes('tar')) return Archive
  if (contentType.includes('pdf') || contentType.includes('document') || contentType.includes('text')) return FileText
  return File
}
