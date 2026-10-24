import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

const h = vi.hoisted(() => ({
  getProjects: vi.fn(),
  progressCb: null,
  statusRef: null,
}))

vi.mock('@/services/api', () => ({
  getProjects: h.getProjects,
  getProject: vi.fn(),
  postProgress: vi.fn(),
  finalizeProject: vi.fn(),
  createEventSource: vi.fn(),
  parseProgressEvent: vi.fn(),
  parseFinalizationEvent: vi.fn(),
}))

vi.mock('@/composables/useSse', () => ({
  useSse: (cb) => {
    h.progressCb = cb
    if (!h.statusRef) h.statusRef = ref('connected')
    return { status: h.statusRef }
  },
}))

import DashboardView from '@/views/DashboardView.vue'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/projects/:executionId', component: { template: '<div />' } },
    ],
  })
}

async function mountDashboard() {
  const router = makeRouter()
  await router.push('/')
  await router.isReady()
  return mount(DashboardView, { global: { plugins: [router] } })
}

function makeProject(executionId, name, githubUrl, completionPercentage, createdAt) {
  return {
    id: `${name}-id`,
    executionId,
    name,
    githubUrl,
    completionPercentage,
    finalizationPercentage: 0,
    finalRepoUrl: null,
    finalizeError: null,
    createdAt,
    updatedAt: createdAt,
  }
}

const alpha = makeProject(101, 'Alpha', 'https://github.com/me/alpha', 40, '2024-01-01T00:00:00Z')
const beta = makeProject(102, 'Beta', 'https://github.com/me/beta', 10, '2024-02-01T00:00:00Z')

async function mountLoaded(projects = [alpha, beta]) {
  // Clone because the store mutates project objects in place on progress events.
  h.getProjects.mockResolvedValue(projects.map((p) => ({ ...p })))
  const wrapper = await mountDashboard()
  await flushPromises()
  return wrapper
}

function rows(wrapper) {
  return wrapper.findAll('section[aria-label="Project list"] tbody tr')
}

beforeEach(() => {
  h.getProjects.mockReset()
  h.statusRef = ref('connected')
})

describe('US-1 / FR-3, FR-4, FR-5 — dashboard lists all projects', () => {
  it('renders one row per project with name and percentage', async () => {
    const wrapper = await mountLoaded()
    expect(rows(wrapper)).toHaveLength(2)

    const text = wrapper.text()
    expect(text).toContain('Alpha')
    expect(text).toContain('Beta')
    // The ring shows the bare number (no "%" symbol).
    const rings = wrapper.findAll('[role="img"]')
    expect(rings.map((r) => r.text())).toEqual(['10', '40'])
  })

  it('uses a single Status column for completion and finalization', async () => {
    const wrapper = await mountLoaded()
    const headers = wrapper.findAll('thead th').map((th) => th.text())
    expect(headers).toEqual(['Project', 'Status', 'Details'])
  })

  it('renders a circular progress ring per row', async () => {
    const wrapper = await mountLoaded()
    const rings = wrapper.findAll('[role="img"]')
    // The store sorts newest first: Beta (2024-02, 10%) then Alpha (2024-01, 40%).
    expect(rings.map((r) => r.attributes('aria-label'))).toEqual([
      '10% complete',
      '40% complete',
    ])
  })

  it('renders a GitHub icon link for each project', async () => {
    const wrapper = await mountLoaded()
    const links = wrapper.findAll('a[target="_blank"]')
    expect(links.map((l) => l.attributes('href'))).toEqual([
      'https://github.com/me/beta',
      'https://github.com/me/alpha',
    ])
  })

  it('links each row to the project detail page', async () => {
    const wrapper = await mountLoaded()
    const detailLinks = wrapper.findAll('a[href^="/projects/"]')
    expect(detailLinks.map((l) => l.attributes('href'))).toEqual([
      '/projects/102',
      '/projects/101',
    ])
  })

  it('shows an empty-state message and no rows when there are no projects', async () => {
    const wrapper = await mountLoaded([])
    expect(wrapper.text()).toContain('No projects yet')
    expect(rows(wrapper)).toHaveLength(0)
  })

  it('shows loading skeletons during the initial fetch', async () => {
    let resolve
    h.getProjects.mockReturnValue(new Promise((r) => (resolve = r)))
    const wrapper = await mountDashboard()
    await nextTick()
    expect(wrapper.text()).not.toContain('No projects yet')
    expect(wrapper.findAll('.animate-pulse').length).toBeGreaterThan(0)

    resolve([alpha])
    await flushPromises()
    expect(wrapper.text()).toContain('Alpha')
  })

  it('shows an error state with a retry button that reloads', async () => {
    h.getProjects.mockRejectedValueOnce(new Error('backend down'))
    const wrapper = await mountDashboard()
    await flushPromises()

    expect(wrapper.text()).toContain('Unable to load projects')
    expect(wrapper.text()).toContain('backend down')

    h.getProjects.mockResolvedValueOnce([alpha])
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Alpha')
  })
})

describe('US-2 / FR-6 — open GitHub repository', () => {
  it('opens the repository in a new tab with safe rel attributes', async () => {
    const wrapper = await mountLoaded([alpha])
    const link = wrapper.get('a[target="_blank"]')
    expect(link.attributes('href')).toBe('https://github.com/me/alpha')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
  })

  it('does not render an anchor for an unsafe URL', async () => {
    const unsafe = makeProject(103, 'Evil', 'javascript:alert(1)', 5, '2024-01-01T00:00:00Z')
    const wrapper = await mountLoaded([unsafe])
    expect(wrapper.find('a[target="_blank"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Evil')
  })
})

describe('Row navigation', () => {
  it('navigates to the detail page when a row is clicked', async () => {
    h.getProjects.mockResolvedValue([{ ...alpha }])
    const router = makeRouter()
    await router.push('/')
    await router.isReady()
    const push = vi.spyOn(router, 'push')
    const wrapper = mount(DashboardView, { global: { plugins: [router] } })
    await flushPromises()

    await rows(wrapper)[0].trigger('click')
    expect(push).toHaveBeenCalledWith('/projects/101')
  })

  it('does not navigate when the GitHub icon is clicked', async () => {
    h.getProjects.mockResolvedValue([{ ...alpha }])
    const router = makeRouter()
    await router.push('/')
    await router.isReady()
    const push = vi.spyOn(router, 'push')
    const wrapper = mount(DashboardView, { global: { plugins: [router] } })
    await flushPromises()

    await wrapper.get('span.inline-flex').trigger('click')
    expect(push).not.toHaveBeenCalled()
  })
})

describe('US-3 / FR-10, FR-11 — live completion updates', () => {
  it('updates the matching row on a progress event and leaves others untouched', async () => {
    const wrapper = await mountLoaded()
    expect(h.progressCb).toBeTypeOf('function')

    h.progressCb({ executionId: 101, completionPercentage: 75 })
    await nextTick()

    const rings = wrapper.findAll('[role="img"]')
    expect(rings.map((r) => r.attributes('aria-label'))).toEqual([
      '10% complete',
      '75% complete',
    ])
  })

  it('ignores a progress event for an unknown execution id without errors', async () => {
    const wrapper = await mountLoaded()
    expect(() => h.progressCb({ executionId: 999, completionPercentage: 50 })).not.toThrow()
    await nextTick()
    const rings = wrapper.findAll('[role="img"]')
    expect(rings.map((r) => r.attributes('aria-label'))).toEqual([
      '10% complete',
      '40% complete',
    ])
  })
})

describe('US-5 / FR-13 — connection status indicator', () => {
  it.each([
    ['connected', 'Connected'],
    ['reconnecting', 'Reconnecting'],
    ['disconnected', 'Disconnected'],
    ['connecting', 'Connecting'],
  ])('renders the %s status as "%s"', async (value, label) => {
    h.statusRef.value = value
    const wrapper = await mountLoaded()
    expect(wrapper.text()).toContain(label)
  })
})
