/**
 * 邮件 HTML 消毒 composable
 * 使用 DOMPurify 防止 XSS 攻击
 */
import DOMPurify from 'dompurify'

// 共享的基础配置
const BASE_ALLOWED_TAGS = [
  'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'hr', 'div', 'span',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li', 'dl', 'dt', 'dd',
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'caption', 'colgroup', 'col',
  'img', 'figure', 'figcaption',
  'blockquote', 'pre', 'code',
  'sub', 'sup', 'small', 'big',
  'center', 'font',
  'section', 'article', 'header', 'footer', 'nav', 'aside', 'main',
  'details', 'summary',
]

const BASE_ALLOWED_ATTR = [
  'href', 'src', 'alt', 'title', 'width', 'height',
  'style', 'class', 'id', 'name',
  'target', 'rel',
  'border', 'cellpadding', 'cellspacing', 'align', 'valign',
  'bgcolor', 'color', 'size', 'face',
  'colspan', 'rowspan',
  'dir', 'lang',
]

const BASE_URI_REGEXP = /^(?:(?:https?|mailto|tel|cid|data):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i

export const useSanitize = () => {
  /**
   * 消毒邮件 HTML，移除脚本、事件处理器等危险内容
   * 保留正常的 HTML 标签、样式、图片（包括追踪像素）
   */
  const sanitizeEmailHtml = (dirty: string): string => {
    if (!dirty || !import.meta.client) return dirty

    return DOMPurify.sanitize(dirty, {
      ALLOWED_TAGS: BASE_ALLOWED_TAGS,
      ALLOWED_ATTR: BASE_ALLOWED_ATTR,
      ALLOW_DATA_ATTR: false,
      ALLOWED_URI_REGEXP: BASE_URI_REGEXP,
    })
  }

  /**
   * 消毒邮件 HTML 并阻止远程图片加载
   * 将远程图片的 src 存入 data-original-src，src 设为空
   */
  const sanitizeEmailHtmlBlockRemote = (dirty: string): string => {
    if (!dirty || !import.meta.client) return dirty

    // 注册 afterSanitizeAttributes hook 拦截远程图片
    const hookId = DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.tagName === 'IMG') {
        const src = node.getAttribute('src') || ''
        // 远程图片 = http:// 或 https:// 开头（非 data: / cid: 内联图片）
        if (/^https?:\/\//i.test(src)) {
          node.setAttribute('data-original-src', src)
          node.removeAttribute('src')
          // 设置占位样式
          node.setAttribute('style', (node.getAttribute('style') || '') + '; opacity: 0.3; filter: grayscale(1);')
          node.setAttribute('alt', node.getAttribute('alt') || '[远程图片已隐藏]')
        }
      }
    })

    try {
      return DOMPurify.sanitize(dirty, {
        ALLOWED_TAGS: BASE_ALLOWED_TAGS,
        ALLOWED_ATTR: [...BASE_ALLOWED_ATTR, 'data-original-src'],
        ALLOW_DATA_ATTR: false,
        ALLOWED_URI_REGEXP: BASE_URI_REGEXP,
      })
    } finally {
      // 仅清理本函数注册的 hook 类型，避免误删其他消费者的 hook
      DOMPurify.removeHook('afterSanitizeAttributes')
    }
  }

  /**
   * 将已消毒 HTML 中的远程图片 src 替换为代理 URL
   * 用于用户主动选择加载远程图片时
   */
  const proxyRemoteImages = (html: string): string => {
    if (!html || !import.meta.client) return html

    // 先正常消毒（保留远程图片 src）
    const clean = sanitizeEmailHtml(html)

    // 用 DOMParser 解析，将所有远程 img src 替换为代理地址
    const parser = new DOMParser()
    const doc = parser.parseFromString(clean, 'text/html')
    const images = doc.querySelectorAll('img[src]')

    images.forEach((img) => {
      const src = img.getAttribute('src') || ''
      if (/^https?:\/\//i.test(src)) {
        const proxyUrl = `/api/proxy/image?url=${encodeURIComponent(src)}`
        img.setAttribute('src', proxyUrl)
      }
    })

    return doc.body.innerHTML
  }

  /**
   * 检测 HTML 中是否包含远程图片
   */
  const hasRemoteImages = (html: string): boolean => {
    if (!html) return false
    return /<img[^>]+src=["']https?:\/\//i.test(html)
  }

  return {
    sanitizeEmailHtml,
    sanitizeEmailHtmlBlockRemote,
    proxyRemoteImages,
    hasRemoteImages,
  }
}
