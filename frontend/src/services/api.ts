import axios, { AxiosError, type AxiosInstance } from 'axios'
import type {
  ApiError,
  CreateProjectPayload,
  FinalizationEvent,
  ProgressEvent,
  Project,
  ProjectDetail,
  ProgressUpdatePayload,
} from '@/types'

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export class ProjectApiError extends Error implements ApiError {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ProjectApiError'
  }
}

function normalizeError(error: unknown): ProjectApiError {
  if (error instanceof AxiosError && error.response) {
    const data = error.response.data as
      | { error?: { message?: string }; detail?: unknown }
      | undefined
    const detail = typeof data?.detail === 'string' ? data.detail : undefined
    const message = data?.error?.message ?? detail ?? error.message
    return new ProjectApiError(error.response.status, message)
  }
  if (error instanceof Error) {
    return new ProjectApiError(0, error.message)
  }
  return new ProjectApiError(0, 'An unexpected error occurred.')
}

export async function getProjects(): Promise<Project[]> {
  try {
    const { data } = await apiClient.get<Project[]>('/api/v1/projects')
    return data
  } catch (error) {
    throw normalizeError(error)
  }
}

export async function getProject(executionId: number): Promise<ProjectDetail> {
  try {
    const { data } = await apiClient.get<ProjectDetail>(`/api/v1/projects/${executionId}`)
    return data
  } catch (error) {
    throw normalizeError(error)
  }
}

export async function createProject(payload: CreateProjectPayload): Promise<ProjectDetail> {
  try {
    // The backend calls two n8n webhooks synchronously; allow more than the
    // default 10s client timeout.
    const { data } = await apiClient.post<ProjectDetail>('/api/v1/projects', payload, {
      timeout: 90000,
    })
    return data
  } catch (error) {
    throw normalizeError(error)
  }
}

export async function updateProjectName(
  executionId: number,
  name: string,
): Promise<ProjectDetail> {
  try {
    const { data } = await apiClient.patch<ProjectDetail>(`/api/v1/projects/${executionId}`, { name })
    return data
  } catch (error) {
    throw normalizeError(error)
  }
}

export async function postProgress(
  executionId: number,
  completionPercentage: number,
): Promise<Project> {
  try {
    const payload: ProgressUpdatePayload = { completionPercentage }
    const { data } = await apiClient.post<Project>(
      `/api/v1/projects/${executionId}/progress`,
      payload,
    )
    return data
  } catch (error) {
    throw normalizeError(error)
  }
}

export async function finalizeProject(executionId: number): Promise<void> {
  try {
    // The backend waits on the n8n webhook, which shares the N8N_TIMEOUT_SECONDS timeout.
    await apiClient.post(`/api/v1/projects/${executionId}/finalize`, null, {
      timeout: 45000,
    })
  } catch (error) {
    throw normalizeError(error)
  }
}

export function createEventSource(): EventSource {
  return new EventSource(`${import.meta.env.VITE_API_BASE_URL}/api/v1/events`)
}

export function parseProgressEvent(data: string): ProgressEvent | null {
  try {
    const parsed = JSON.parse(data) as unknown
    if (
      parsed &&
      typeof parsed === 'object' &&
      'executionId' in parsed &&
      'completionPercentage' in parsed &&
      typeof (parsed as { executionId: unknown }).executionId === 'number' &&
      typeof (parsed as { completionPercentage: unknown }).completionPercentage === 'number'
    ) {
      return parsed as ProgressEvent
    }
  } catch {
    // malformed payload: ignore
  }
  return null
}

export function parseFinalizationEvent(data: string): FinalizationEvent | null {
  try {
    const parsed = JSON.parse(data) as unknown
    if (
      parsed &&
      typeof parsed === 'object' &&
      'executionId' in parsed &&
      'finalizationPercentage' in parsed &&
      typeof (parsed as { executionId: unknown }).executionId === 'number' &&
      typeof (parsed as { finalizationPercentage: unknown }).finalizationPercentage ===
        'number'
    ) {
      return parsed as FinalizationEvent
    }
  } catch {
    // malformed payload: ignore
  }
  return null
}
