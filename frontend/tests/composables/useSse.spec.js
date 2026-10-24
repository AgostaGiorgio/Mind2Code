import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const h = vi.hoisted(() => ({
  createEventSource: vi.fn(),
  parseProgressEvent: vi.fn(),
  parseFinalizationEvent: vi.fn(),
}))

vi.mock('@/services/api', () => ({
  createEventSource: h.createEventSource,
  parseProgressEvent: h.parseProgressEvent,
  parseFinalizationEvent: h.parseFinalizationEvent,
}))

import { useSse } from '@/composables/useSse'

class FakeEventSource {
  constructor(url) {
    this.url = url
    this.closed = false
    this.listeners = {}
    FakeEventSource.instances.push(this)
  }

  addEventListener(type, cb) {
    this.listeners[type] = cb
  }

  close() {
    this.closed = true
  }

  emit(type, data) {
    if (this.listeners[type]) {
      this.listeners[type]({ data })
    } else {
      this[`on${type}`]?.({})
    }
  }
}
FakeEventSource.instances = []

function mountSse(onProgress = vi.fn(), onFinalization = vi.fn()) {
  let api
  const wrapper = mount(
    defineComponent({
      setup() {
        api = useSse(onProgress, onFinalization)
        return () => null
      },
    }),
  )
  return { wrapper, api, onProgress, onFinalization }
}

const latest = () => FakeEventSource.instances.at(-1)

beforeEach(() => {
  FakeEventSource.instances = []
  h.createEventSource.mockReset()
  h.parseProgressEvent.mockReset()
  h.parseFinalizationEvent.mockReset()
  h.createEventSource.mockImplementation((url) => new FakeEventSource(url ?? '/api/v1/events'))
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useSse', () => {
  it('opens a connection on mount and reports connected on open', () => {
    const { api } = mountSse()
    expect(FakeEventSource.instances).toHaveLength(1)
    expect(api.status.value).toBe('connecting')

    latest().emit('open')
    expect(api.status.value).toBe('connected')
  })

  it('forwards valid progress events to the callback', () => {
    const onProgress = vi.fn()
    mountSse(onProgress)

    const event = { executionId: 101, completionPercentage: 75 }
    h.parseProgressEvent.mockReturnValue(event)
    latest().emit('progress', 'raw')

    expect(h.parseProgressEvent).toHaveBeenCalledWith('raw')
    expect(onProgress).toHaveBeenCalledWith(event)
  })

  it('ignores malformed payloads without throwing', () => {
    const onProgress = vi.fn()
    mountSse(onProgress)

    h.parseProgressEvent.mockReturnValue(null)
    expect(() => latest().emit('progress', 'garbage')).not.toThrow()
    expect(onProgress).not.toHaveBeenCalled()
  })

  it('forwards valid finalization events to the callback', () => {
    const onFinalization = vi.fn()
    mountSse(vi.fn(), onFinalization)

    const event = {
      executionId: 101,
      finalizationPercentage: 60,
      finalRepoUrl: null,
      finalizeError: null,
    }
    h.parseFinalizationEvent.mockReturnValue(event)
    latest().emit('finalization', 'raw')

    expect(h.parseFinalizationEvent).toHaveBeenCalledWith('raw')
    expect(onFinalization).toHaveBeenCalledWith(event)
  })

  it('reconnects with exponential backoff on error', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0)
    const { api } = mountSse()
    latest().emit('open')
    expect(api.status.value).toBe('connected')

    // first failure -> reconnecting, source closed
    latest().emit('error')
    expect(api.status.value).toBe('reconnecting')
    expect(FakeEventSource.instances).toHaveLength(1)
    expect(latest().closed).toBe(true)

    // base delay is 1000ms
    vi.advanceTimersByTime(999)
    expect(FakeEventSource.instances).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(FakeEventSource.instances).toHaveLength(2)

    // second failure doubles the delay to 2000ms
    latest().emit('error')
    vi.advanceTimersByTime(1999)
    expect(FakeEventSource.instances).toHaveLength(2)
    vi.advanceTimersByTime(1)
    expect(FakeEventSource.instances).toHaveLength(3)

    // an open resets the backoff
    latest().emit('open')
    expect(api.status.value).toBe('connected')
    latest().emit('error')
    vi.advanceTimersByTime(1000)
    expect(FakeEventSource.instances).toHaveLength(4)
  })

  it('caps the backoff at 30s', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0)
    mountSse()
    // failures without an open -> attempts 1..7 (1000,2000,4000,8000,16000,30000,30000)
    const expected = [1000, 2000, 4000, 8000, 16000, 30000, 30000]
    expected.forEach((delay, index) => {
      latest().emit('error')
      const before = FakeEventSource.instances.length
      vi.advanceTimersByTime(delay - 1)
      expect(FakeEventSource.instances).toHaveLength(before)
      vi.advanceTimersByTime(1)
      expect(FakeEventSource.instances).toHaveLength(before + 1)
      expect(expected[index]).toBe(delay)
    })
  })

  it('disconnects on unmount and stops reconnecting', () => {
    const { wrapper, api } = mountSse()
    latest().emit('open')

    wrapper.unmount()

    expect(api.status.value).toBe('disconnected')
    expect(latest().closed).toBe(true)

    const count = FakeEventSource.instances.length
    latest().emit('error')
    vi.advanceTimersByTime(60000)
    expect(FakeEventSource.instances).toHaveLength(count)
    expect(api.status.value).toBe('disconnected')
  })
})
