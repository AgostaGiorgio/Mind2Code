import { reactive, readonly } from 'vue'
import { createProject } from '@/services/api'

const state = reactive({
  status: 'idle', // idle | creating | created | error
  payload: null,
  project: null,
  error: null,
})

// Invalidates stale requests (e.g. the user leaves the page and retries).
let runId = 0

async function run(payload) {
  const current = ++runId

  state.payload = payload
  state.project = null
  state.error = null
  state.status = 'creating'

  try {
    const project = await createProject(payload)
    if (current !== runId) return
    state.project = project
    state.status = 'created'
  } catch (e) {
    if (current !== runId) return
    state.error = e instanceof Error ? e.message : 'Failed to create the project.'
    state.status = 'error'
  }
}

export function useProjectCreation() {
  const start = (payload) => {
    if (!payload) return
    run(payload)
  }

  const retry = () => {
    if (state.payload) run(state.payload)
  }

  const reset = () => {
    runId += 1
    state.status = 'idle'
    state.payload = null
    state.project = null
    state.error = null
  }

  return { state: readonly(state), start, retry, reset }
}
