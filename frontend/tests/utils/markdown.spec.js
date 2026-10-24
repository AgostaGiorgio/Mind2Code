import { describe, expect, it } from 'vitest'

import { renderMarkdown } from '@/utils/markdown'

describe('renderMarkdown', () => {
  it('renders headings, emphasis and lists', () => {
    const html = renderMarkdown('# Title\n\nSome **bold** and *italic*.\n\n- a\n- b')
    expect(html).toContain('<h1>Title</h1>')
    expect(html).toContain('<strong>bold</strong>')
    expect(html).toContain('<em>italic</em>')
    expect(html).toContain('<ul>')
  })

  it('renders GFM tables inside a scrollable wrapper', () => {
    const html = renderMarkdown('| a | b |\n| - | - |\n| 1 | 2 |')
    expect(html).toContain('<div class="markdown-table-wrap"><table>')
    expect(html).toContain('<th>a</th>')
    expect(html).toMatch(/<\/table>\s*<\/div>/)
  })

  it('escapes raw HTML instead of executing it', () => {
    const html = renderMarkdown('<script>alert(1)</script>')
    expect(html).not.toContain('<script>')
    expect(html).toContain('&lt;script&gt;')
  })

  it('opens rendered links in a new tab but rejects dangerous schemes', () => {
    const safe = renderMarkdown('[site](https://example.com)')
    expect(safe).toContain('href="https://example.com"')
    expect(safe).toContain('target="_blank"')
    expect(safe).toContain('rel="noopener noreferrer"')

    const unsafe = renderMarkdown('[x](javascript:alert(1))')
    expect(unsafe).not.toContain('href="javascript:')
  })

  it('highlights fenced code blocks', () => {
    const html = renderMarkdown('```js\nconst a = 1\n```')
    expect(html).toContain('<pre>')
    expect(html).toContain('class="hljs language-js"')
    expect(html).toContain('hljs-keyword')
  })

  it('returns an empty string for empty input', () => {
    expect(renderMarkdown('')).toBe('')
    expect(renderMarkdown(null)).toBe('')
    expect(renderMarkdown(undefined)).toBe('')
  })
})
