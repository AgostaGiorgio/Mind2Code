import { beforeEach, describe, expect, it, vi } from 'vitest'

const h = vi.hoisted(() => ({ getProjects: vi.fn() }))

vi.mock('@/services/api', () => ({ getProjects: h.getProjects }))

function makeProject(executionId, name, completionPercentage, createdAt) {
  return {
    id: `${name}-id`,
    executionId,
    name,
    githubUrl: `https://github.com/me/${name.toLowerCase()}`,
    completionPercentage,
    createdAt,
    updatedAt: createdAt,
  }
}

async function freshStore() {
  vi.resetModules()
  const mod = await import('@/stores/projects')
  return mod.useProjectsStore()
}

beforeEach(() => {
  h.getProjects.mockReset()
})

describe('useProjectsStore', () => {
  it('starts empty and not loading', async () => {
    const store = await freshStore()
    expect(store.state.loading).toBe(false)
    expect(store.state.error).toBeNull()
    expect(store.hasProjects.value).toBe(false)
    expect(store.list.value).toEqual([])
  })

  it('loads projects, indexes them by executionId and sorts newest first', async () => {
    const store = await freshStore()
    h.getProjects.mockResolvedValue([
      makeProject(101, 'Alpha', 40, '2024-01-01T00:00:00Z'),
      makeProject(102, 'Beta', 10, '2024-03-01T00:00:00Z'),
    ])

    await store.load()

    expect(store.state.loading).toBe(false)
    expect(Object.keys(store.state.projects)).toEqual(['101', '102'])
    expect(store.list.value.map((p) => p.name)).toEqual(['Beta', 'Alpha'])
    expect(store.hasProjects.value).toBe(true)
  })

  it('captures the error message when loading fails', async () => {
    const store = await freshStore()
    h.getProjects.mockRejectedValue(new Error('network down'))

    await store.load()

    expect(store.state.error).toBe('network down')
    expect(store.state.loading).toBe(false)
    expect(store.hasProjects.value).toBe(false)
  })

  it('uses a fallback message for non-Error failures', async () => {
    const store = await freshStore()
    h.getProjects.mockRejectedValue('exploded')

    await store.load()

    expect(store.state.error).toBe('Failed to load projects.')
  })

  it('retry re-runs the load', async () => {
    const store = await freshStore()
    h.getProjects.mockResolvedValue([makeProject(101, 'Alpha', 40, '2024-01-01T00:00:00Z')])

    await store.retry()

    expect(store.list.value).toHaveLength(1)
    expect(h.getProjects).toHaveBeenCalledTimes(1)
  })

  it('applies a progress event to the matching project only', async () => {
    const store = await freshStore()
    h.getProjects.mockResolvedValue([
      makeProject(101, 'Alpha', 40, '2024-01-01T00:00:00Z'),
      makeProject(102, 'Beta', 10, '2024-01-01T00:00:00Z'),
    ])
    await store.load()

    store.applyProgressEvent({ executionId: 101, completionPercentage: 75 })

    const byId = Object.fromEntries(store.list.value.map((p) => [p.executionId, p]))
    expect(byId[101].completionPercentage).toBe(75)
    expect(byId[102].completionPercentage).toBe(10)
  })

  it('ignores a progress event with an unknown executionId without side effects', async () => {
    const store = await freshStore()
    h.getProjects.mockResolvedValue([makeProject(101, 'Alpha', 40, '2024-01-01T00:00:00Z')])
    await store.load()

    expect(() =>
      store.applyProgressEvent({ executionId: 999, completionPercentage: 50 }),
    ).not.toThrow()
    expect(store.list.value[0].completionPercentage).toBe(40)
  })
})
