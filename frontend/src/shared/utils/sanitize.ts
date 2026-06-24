/**
 * 轻量级 HTML 净化工具 — 防止 XSS 攻击。
 *
 * 用于所有 v-html 渲染场景（知识库内容、AI 助手回复、富文本编辑器等）。
 * 移除 <script>、on* 事件属性、javascript: 协议等危险内容。
 *
 * 对于更严格的净化需求，可后续引入 DOMPurify（npm i dompurify）。
 */

/**
 * 净化 HTML 字符串，移除 XSS 危险内容。
 *
 * @param dirty 待净化的 HTML 字符串
 * @returns 净化后的安全 HTML 字符串
 */
export function sanitizeHtml(dirty: string): string {
  if (!dirty) return ''

  let html = dirty

  // 1. 移除 <script>...</script> 标签（含内容）
  html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script\s*>/gi, '')

  // 2. 移除 <iframe>、<object>、<embed>、<applet> 标签
  html = html.replace(/<\/?(iframe|object|embed|applet)\b[^>]*>/gi, '')

  // 3. 移除所有 on* 事件属性（onclick, onload, onerror 等）
  html = html.replace(/\s+on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '')

  // 4. 移除 javascript: 协议的 href/src
  html = html.replace(/(href|src)\s*=\s*["']?\s*javascript\s*:/gi, '$1="')

  // 5. 移除 data: 协议的 src（可用于 XSS，如 data:text/html）
  html = html.replace(/src\s*=\s*["']?\s*data\s*:/gi, 'src="')

  // 6. 移除 style 属性中的 expression()（IE 专用，但保持兼容）
  html = html.replace(/style\s*=\s*"[^"]*expression\s*\([^)]*\)[^"]*"/gi, '')

  return html
}

/**
 * 安全的 Markdown → HTML 转换 + XSS 净化。
 * 先做简易 Markdown 语法替换，再净化 HTML。
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
