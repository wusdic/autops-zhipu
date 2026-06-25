/**
 * HTML 净化工具 — 基于 DOMPurify 防止 XSS 攻击。
 *
 * 用于所有 v-html 渲染场景（知识库内容、AI 助手回复、富文本编辑器等）。
 *
 * 早期版本使用自研正则净化，无法可靠防御 SVG/MathML 命名空间注入、
 * 换行/实体编码绕过等攻击，现统一改用业界标准的 DOMPurify。
 */
import DOMPurify from 'dompurify'

/**
 * 净化 HTML 字符串，移除 XSS 危险内容。
 *
 * @param dirty 待净化的 HTML 字符串
 * @returns 净化后的安全 HTML 字符串
 */
export function sanitizeHtml(dirty: string): string {
  if (!dirty) return ''
  return DOMPurify.sanitize(dirty, {
    USE_PROFILES: { html: true },
    // 禁止已知危险标签/属性，保留常用富文本能力
    FORBID_TAGS: ['style', 'form', 'input', 'button'],
    FORBID_ATTR: ['style'],
  })
}

/**
 * 安全的 Markdown → HTML 转换 + XSS 净化。
 * 先做简易 Markdown 语法替换，再通过 DOMPurify 净化 HTML。
 */
export function safeMarkdown(text: string): string {
  if (!text) return ''

  const html = text
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')

  return sanitizeHtml(html)
}
