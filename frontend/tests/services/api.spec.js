import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
}))

vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    default: {
      create: vi.fn(() => ({ get: mocks.get, post: mocks.post, patch: mocks.patch })),
    },
  }
})

import { AxiosError } from 'axios'
import {
  ProjectApiError,
  createEventSource,
  finalizeProject,
  getProject,
  getProjects,
  parseFinalizationEvent,
  parseProgressEvent,
  postProgress,
  updateProjectName,
} from '@/services/api'

const project = {
  id: 'a-uuid',
  executionId: 101,
  name: 'Alpha',
  githubUrl: 'https://github.com/me/alpha',
  completionPercentage: 40,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

function axiosErrorWith(status, data) {
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
    status,
    data,
    statusText: 'error',
    headers: {},
    config: {},
  })
}

beforeEach(() => {
  mocks.get.mockReset()
  mocks.post.mockReset()
  mocks.patch.mockReset()
})

describe('getProjects', () => {
  it('returns the parsed project list', async () => {
    mocks.get.mockResolvedValue({ data: [project] })
    await expect(getProjects()).resolves.toEqual([project])
    expect(mocks.get).toHaveBeenCalledWith('/api/v1/projects')
  })

  it('normalizes an HTTP error into ProjectApiError with backend message', async () => {
    mocks.get.mockRejectedValue(
      axiosErrorWith(422, { error: { message: 'completionPercentage invalid' } }),
    )
    await expect(getProjects()).rejects.toMatchObject({
      name: 'ProjectApiError',
      status: 422,
      message: 'completionPercentage invalid',
    })
  })

  it('falls back to the axios message when the body has no error field', async () => {
    mocks.get.mockRejectedValue(axiosErrorWith(500, {}))
    const error = await getProjects().catch((e) => e)
    expect(error).toBeInstanceOf(ProjectApiError)
    expect(error.status).toBe(500)
    expect(error.message).toBe('Request failed')
  })

  it('normalizes a transport error (no response) to status 0', async () => {
    mocks.get.mockRejectedValue(new AxiosError('Network Error', 'ERR_NETWORK'))
    const error = await getProjects().catch((e) => e)
    expect(error.status).toBe(0)
    expect(error.message).toBe('Network Error')
  })

  it('normalizes a generic Error to status 0', async () => {
    mocks.get.mockRejectedValue(new Error('boom'))
    const error = await getProjects().catch((e) => e)
    expect(error.status).toBe(0)
    expect(error.message).toBe('boom')
  })

  it('normalizes a non-Error rejection to a generic message', async () => {
    mocks.get.mockRejectedValue('nope')
    const error = await getProjects().catch((e) => e)
    expect(error.status).toBe(0)
    expect(error.message).toBe('An unexpected error occurred.')
  })
})

describe('getProject', () => {
  it('fetches a single project (with documents) by execution id', async () => {
    const detail = { ...project, requirements: 'req', codeSummary: 'code', testSummary: 'tests', finalReview: 'review' }
    mocks.get.mockResolvedValue({ data: detail })
    await expect(getProject(101)).resolves.toEqual(detail)
    expect(mocks.get).toHaveBeenCalledWith('/api/v1/projects/101')
  })

  it('normalizes an HTTP error into ProjectApiError', async () => {
    mocks.get.mockRejectedValue(axiosErrorWith(404, { error: { message: 'not found' } }))
    const error = await getProject(999).catch((e) => e)
    expect(error).toBeInstanceOf(ProjectApiError)
    expect(error.status).toBe(404)
  })
})

describe('updateProjectName', () => {
  it('patches the name and returns the updated project detail', async () => {
    const detail = {
      ...project,
      name: 'Beta',
      requirements: 'req',
      codeSummary: 'code',
      testSummary: 'tests',
      finalReview: 'review',
    }
    mocks.patch.mockResolvedValue({ data: detail })
    await expect(updateProjectName(101, 'Beta')).resolves.toEqual(detail)
    expect(mocks.patch).toHaveBeenCalledWith('/api/v1/projects/101', { name: 'Beta' })
  })

  it('normalizes an HTTP error into ProjectApiError', async () => {
    mocks.patch.mockRejectedValue(axiosErrorWith(404, { error: { message: 'not found' } }))
    const error = await updateProjectName(999, 'X').catch((e) => e)
    expect(error).toBeInstanceOf(ProjectApiError)
    expect(error.status).toBe(404)
  })
})

describe('postProgress', () => {
  it('posts the completion percentage and returns the updated project', async () => {
    mocks.post.mockResolvedValue({ data: { ...project, completionPercentage: 75 } })
    const result = await postProgress(101, 75)
    expect(result.completionPercentage).toBe(75)
    expect(mocks.post).toHaveBeenCalledWith('/api/v1/projects/101/progress', {
      completionPercentage: 75,
    })
  })

  it('surfaces an error with the 404 status', async () => {
    mocks.post.mockRejectedValue(axiosErrorWith(404, { error: { message: 'not found' } }))
    const error = await postProgress(999, 50).catch((e) => e)
    expect(error.status).toBe(404)
  })
})

describe('createEventSource', () => {
  it('opens an EventSource against the events endpoint', () => {
    class FakeEventSource {
      constructor(url) {
        this.url = url
      }
    }
    vi.stubGlobal('EventSource', FakeEventSource)
    const source = createEventSource()
    expect(source.url).toContain('/api/v1/events')
    vi.unstubAllGlobals()
  })
})

describe('finalizeProject', () => {
  it('posts to the finalize endpoint', async () => {
    mocks.post.mockResolvedValue({ status: 204 })
    await expect(finalizeProject(101)).resolves.toBeUndefined()
    expect(mocks.post).toHaveBeenCalledWith('/api/v1/projects/101/finalize')
  })

  it('normalizes an HTTP error into ProjectApiError', async () => {
    mocks.post.mockRejectedValue(axiosErrorWith(409, { error: { message: 'not eligible' } }))
    const error = await finalizeProject(101).catch((e) => e)
    expect(error).toBeInstanceOf(ProjectApiError)
    expect(error.status).toBe(409)
  })
})

describe('parseFinalizationEvent', () => {
  it('parses a valid finalization payload', () => {
    expect(
      parseFinalizationEvent(
        '{"executionId":101,"finalizationPercentage":60,"finalRepoUrl":null,"finalizeError":null}',
      ),
    ).toEqual({
      executionId: 101,
      finalizationPercentage: 60,
      finalRepoUrl: null,
      finalizeError: null,
    })
  })

  it('returns null for malformed or mistyped payloads', () => {
    expect(parseFinalizationEvent('{not json')).toBeNull()
    expect(parseFinalizationEvent('{"executionId":101}')).toBeNull()
    expect(parseFinalizationEvent('{"executionId":"101","finalizationPercentage":60}')).toBeNull()
  })
})

describe('parseProgressEvent', () => {
  it('parses a valid progress payload', () => {
    expect(parseProgressEvent('{"executionId":101,"completionPercentage":75}')).toEqual({
      executionId: 101,
      completionPercentage: 75,
    })
  })

  it('returns null for malformed JSON', () => {
    expect(parseProgressEvent('{not json')).toBeNull()
  })

  it('returns null when required fields are missing', () => {
    expect(parseProgressEvent('{"executionId":101}')).toBeNull()
    expect(parseProgressEvent('{}')).toBeNull()
  })

  it('returns null when field types are wrong', () => {
    expect(parseProgressEvent('{"executionId":"101","completionPercentage":75}')).toBeNull()
    expect(parseProgressEvent('{"executionId":101,"completionPercentage":"75"}')).toBeNull()
  })

  it('returns null for non-object payloads', () => {
    expect(parseProgressEvent('42')).toBeNull()
    expect(parseProgressEvent('null')).toBeNull()
  })
})
