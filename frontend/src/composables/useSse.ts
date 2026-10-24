import { onUnmounted, ref, type Ref } from 'vue'
import {
  createEventSource,
  parseFinalizationEvent,
  parseProgressEvent,
} from '@/services/api'
import type { FinalizationEvent, ProgressEvent } from '@/types'

export type SseStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected'

const BASE_DELAY_MS = 1000
const MAX_DELAY_MS = 30000

export interface UseSseReturn {
  status: Ref<SseStatus>
}

export function useSse(
  onProgress: (event: ProgressEvent) => void,
  onFinalization?: (event: FinalizationEvent) => void,
): UseSseReturn {
  const status = ref<SseStatus>('connecting')

  let eventSource: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let attempt = 0
  let intentionalClose = false

  const clearTimers = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  const scheduleReconnect = () => {
    clearTimers()
    if (intentionalClose) return

    attempt += 1
    const exponential = BASE_DELAY_MS * 2 ** (attempt - 1)
    const capped = Math.min(exponential, MAX_DELAY_MS)
    const jitter = Math.floor(capped * 0.5 * Math.random())
    const delay = Math.floor(capped + jitter)

    status.value = 'reconnecting'
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  const connect = () => {
    if (eventSource || intentionalClose) return

    if (status.value !== 'connected') {
      status.value = attempt === 0 ? 'connecting' : 'reconnecting'
    }

    eventSource = createEventSource()

    eventSource.onopen = () => {
      status.value = 'connected'
      attempt = 0
    }

    eventSource.addEventListener('progress', (e: MessageEvent) => {
      const progress = parseProgressEvent(e.data)
      if (progress) {
        onProgress(progress)
      }
    })

    eventSource.addEventListener('finalization', (e: MessageEvent) => {
      const finalization = parseFinalizationEvent(e.data)
      if (finalization && onFinalization) {
        onFinalization(finalization)
      }
    })

    eventSource.onerror = () => {
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
      if (!intentionalClose) {
        scheduleReconnect()
      }
    }
  }

  const disconnect = () => {
    intentionalClose = true
    clearTimers()
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    status.value = 'disconnected'
  }

  onUnmounted(disconnect)

  connect()

  return { status }
}
