import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useToast } from '@/composables/useToast'

beforeEach(() => {
  vi.useFakeTimers()
  const { toasts, dismiss } = useToast()
  toasts.value.slice().forEach((t) => dismiss(t.id))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useToast', () => {
  it('pushes a toast and returns an id', () => {
    const { toasts, push } = useToast()
    const id = push('hello')
    expect(id).toBeTypeOf('number')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0]).toMatchObject({ id, message: 'hello', type: 'info' })
  })

  it('auto-dismisses after the timeout', () => {
    const { toasts, push } = useToast()
    push('temporary', 'info', 1000)
    expect(toasts.value).toHaveLength(1)

    vi.advanceTimersByTime(1000)
    expect(toasts.value).toHaveLength(0)
  })

  it('keeps a toast when timeout is zero', () => {
    const { toasts, push } = useToast()
    push('sticky', 'info', 0)
    vi.advanceTimersByTime(60000)
    expect(toasts.value).toHaveLength(1)
  })

  it('sets the type for success / error / info helpers', () => {
    const { toasts, success, error, info } = useToast()
    success('ok')
    error('bad')
    info('note')
    expect(toasts.value.map((t) => t.type)).toEqual(['success', 'error', 'info'])
  })

  it('uses a longer default timeout for errors', () => {
    const { toasts, error } = useToast()
    error('bad')
    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(1500)
    expect(toasts.value).toHaveLength(0)
  })

  it('dismisses a toast by id', () => {
    const { toasts, push, dismiss } = useToast()
    const id = push('x', 'info', 0)
    dismiss(id)
    expect(toasts.value).toHaveLength(0)
  })
})
