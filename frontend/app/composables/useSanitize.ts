/**
 * 邮件 HTML 消毒 composable
 * 使用 DOMPurify 防止 XSS 攻击
 */
import DOMPurify from 'dompurify'

export const useSanitize = () => {
  /**
   * 消毒邮件 HTML，移除脚本、事件处理器等危险内容
   * 保留正常的 HTML 标签、样式、图片（包括追踪像素）
   */
  const sanitizeEmailHtml = (dirty: string): string => {
    if (!dirty || !import.meta.client) return dirty

    return DOMPurify.sanitize(dirty, {
      // 允许常见的邮件 HTML 标签
      ALLOWED_TAGS: [
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
      ],
      // 允许常见的属性
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title', 'width', 'height',
        'style', 'class', 'id', 'name',
        'target', 'rel',
        'border', 'cellpadding', 'cellspacing', 'align', 'valign',
        'bgcolor', 'color', 'size', 'face',
        'colspan', 'rowspan',
        'dir', 'lang',
      ],
      // 允许 data: URI 用于内联图片
      ALLOW_DATA_ATTR: false,
      // 允许的 URI 协议
      ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel|cid|data):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i,
    })
  }

  return {
    sanitizeEmailHtml,
  }
}
