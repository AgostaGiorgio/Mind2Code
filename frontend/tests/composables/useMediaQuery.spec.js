import { defineComponent, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useMediaQuery } from '@/composables/useMediaQuery'

function installMatchMedia({ matches = false } = {}) {
  const listeners = []
  const mql = {
    matches,
    addEventListener: vi.fn((type, cb) => listeners.push(cb)),
    removeEventListener: vi.fn((type, cb) => {
      const i = listeners.indexOf(cb)
      if (i >= 0) listeners.splice(i, 1)
    }),
    trigger(next) {
      mql.matches = next
      listeners.forEach((cb) => cb({ matches: next }))
    },
  }
  vi.stubGlobal('matchMedia', vi.fn(() => mql))
  return mql
}

function mountWithQuery(query) {
  let result
  const wrapper = mount(
    defineComponent({
      setup() {
        result = useMediaQuery(query)
        return () => null
      },
    }),
  )
  return { wrapper, result }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useMediaQuery', () => {
  it('reflects the initial match state', () => {
    installMatchMedia({ matches: true })
    const { result } = mountWithQuery('(min-width: 1024px)')
    expect(window.matchMedia).toHaveBeenCalledWith('(min-width: 1024px)')
    expect(result.value).toBe(true)
  })

  it('updates when the media query changes', async () => {
    const mql = installMatchMedia({ matches: false })
    const { result } = mountWithQuery('(min-width: 1024px)')
    expect(result.value).toBe(false)

    mql.trigger(true)
    await nextTick()
    expect(result.value).toBe(true)
  })

  it('removes the change listener on unmount', () => {
    const mql = installMatchMedia({ matches: false })
    const { wrapper } = mountWithQuery('(min-width: 1024px)')
    wrapper.unmount()
    expect(mql.removeEventListener).toHaveBeenCalled()
  })
})
