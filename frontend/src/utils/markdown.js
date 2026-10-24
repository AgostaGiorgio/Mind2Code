import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/common'

// The documents are authored as Markdown. `html: false` keeps any raw HTML in
// the source escaped, so rendering the output with v-html is safe by default.
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: false,
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
      } catch {
        // fall back to markdown-it's escaped output
      }
    }
    return ''
  },
})

// External links open in a new tab. markdown-it's default `validateLink`
// already rejects dangerous schemes (javascript:, data:, ...).
const defaultLinkOpen = md.renderer.rules.link_open
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  if (defaultLinkOpen) {
    return defaultLinkOpen(tokens, idx, options, env, self)
  }
  return self.renderToken(tokens, idx, options)
}

// Wrap tables in a scrollable container so a wide table scrolls on its own
// instead of adding a horizontal scroll to the whole page.
const defaultTableOpen =
  md.renderer.rules.table_open || ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))
md.renderer.rules.table_open = (tokens, idx, options, env, self) =>
  `<div class="markdown-table-wrap">${defaultTableOpen(tokens, idx, options, env, self)}`

const defaultTableClose =
  md.renderer.rules.table_close || ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))
md.renderer.rules.table_close = (tokens, idx, options, env, self) =>
  `${defaultTableClose(tokens, idx, options, env, self)}</div>`

export function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

export default md
