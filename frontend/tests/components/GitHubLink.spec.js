import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import GitHubLink from '@/components/ui/GitHubLink.vue'

describe('GitHubLink', () => {
  it('renders a safe link that opens in a new tab', () => {
    const wrapper = mount(GitHubLink, {
      props: { url: 'https://github.com/me/alpha', label: 'Repo Alpha' },
    })
    const link = wrapper.get('a')
    expect(link.attributes('href')).toBe('https://github.com/me/alpha')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
    expect(link.attributes('aria-label')).toBe('Repo Alpha')
  })

  it('renders nothing for an unsafe URL', () => {
    const wrapper = mount(GitHubLink, { props: { url: 'javascript:alert(1)' } })
    expect(wrapper.find('a').exists()).toBe(false)
  })

  it('renders nothing for an empty URL', () => {
    const wrapper = mount(GitHubLink, { props: { url: '' } })
    expect(wrapper.find('a').exists()).toBe(false)
  })
})
