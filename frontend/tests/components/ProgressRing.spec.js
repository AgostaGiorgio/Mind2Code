import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ProgressRing from '@/components/ui/ProgressRing.vue'

function dashOffset(wrapper) {
  return Number(wrapper.findAll('circle')[1].attributes('stroke-dashoffset'))
}

describe('ProgressRing', () => {
  it('renders the bare number and an accessible label', () => {
    const wrapper = mount(ProgressRing, { props: { value: 40 } })
    expect(wrapper.text()).toBe('40')
    expect(wrapper.text()).not.toContain('%')
    expect(wrapper.attributes('role')).toBe('img')
    expect(wrapper.attributes('aria-label')).toBe('40% complete')
  })

  it('clamps out-of-range values', () => {
    expect(mount(ProgressRing, { props: { value: 150 } }).attributes('aria-label')).toBe(
      '100% complete',
    )
    expect(mount(ProgressRing, { props: { value: -10 } }).attributes('aria-label')).toBe(
      '0% complete',
    )
  })

  it('renders the warning tone arc in orange', () => {
    const wrapper = mount(ProgressRing, { props: { value: 50, tone: 'warning' } })
    const arc = wrapper.findAll('circle')[1]
    expect(arc.classes()).toContain('text-amber-400')
  })

  it('fills the arc proportionally to the value', () => {
    const empty = mount(ProgressRing, { props: { value: 0 } })
    const half = mount(ProgressRing, { props: { value: 50 } })
    expect(dashOffset(empty)).toBeGreaterThan(dashOffset(half))
    expect(dashOffset(half)).toBeGreaterThan(0)
  })
})
