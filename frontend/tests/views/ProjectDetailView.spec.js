import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

const h = vi.hoisted(() => ({
  getProject: vi.fn(),
  updateProjectName: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  progressCb: null,
  statusRef: null,
}))

vi.mock('@/services/api', () => ({
  getProject: h.getProject,
  updateProjectName: h.updateProjectName,
  finalizeProject: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: h.toastSuccess, error: h.toastError }),
}))

vi.mock('@/composables/useSse', () => ({
  useSse: (cb) => {
    h.progressCb = cb
    if (!h.statusRef) h.statusRef = ref('connected')
    return { status: h.statusRef }
  },
}))

import ProjectDetailView from '@/views/ProjectDetailView.vue'

async function mountDetail() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/projects/:executionId', component: { template: '<div />' } },
    ],
  })
  await router.push('/projects/101')
  await router.isReady()
  return mount(ProjectDetailView, { global: { plugins: [router] } })
}

const project = {
  id: 'id-101',
  executionId: 101,
  name: 'Alpha',
  githubUrl: 'https://github.com/me/alpha',
  completionPercentage: 40,
  finalizationPercentage: 0,
  finalRepoUrl: null,
  finalizeError: null,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

const detail = {
  ...project,
  finalReview: '# Final Review\n\n- done',
  userInput: '# User Input\n\n- note',
  requirements: '# Requirements\n\n- one',
  codeSummary: 'CODE',
  testSummary: 'TESTS',
  retrospective: null,
}

async function mountLoaded() {
  h.getProject.mockResolvedValue({ ...detail })
  const wrapper = await mountDetail()
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  h.getProject.mockReset()
  h.updateProjectName.mockReset()
  h.toastSuccess.mockReset()
  h.toastError.mockReset()
  h.statusRef = ref('connected')
})

describe('ProjectDetailView', () => {
  it('loads the project detail and opens the Final Review tab first', async () => {
    const wrapper = await mountLoaded()

    expect(h.getProject).toHaveBeenCalledWith(101)
    expect(wrapper.text()).toContain('Alpha')
    expect(wrapper.find('[role="img"]').attributes('aria-label')).toBe('40% complete')
    // Header order: repository icons, editable title block, completion ring.
    const header = wrapper.findAll('.app-card')[0]
    expect(header.findAll(':scope > *').map((el) => el.element.tagName.toLowerCase())).toEqual([
      'div',
      'div',
      'span',
    ])
    expect(wrapper.get('a[target="_blank"]').attributes('href')).toBe(
      'https://github.com/me/alpha',
    )

    // The header also has an (empty) rename button, so keep only the tab labels.
    const tabs = wrapper.findAll('button').filter((b) => b.text().trim().length > 0)
    expect(tabs.map((t) => t.text())).toEqual([
      'Final Review',
      'User Input',
      'Requirements',
      'Code Summary',
      'Test Summary',
    ])
    expect(wrapper.get('.markdown-body').find('h1').text()).toBe('Final Review')
  })

  it('shows the user input document in the second tab', async () => {
    const wrapper = await mountLoaded()
    const tab = wrapper.findAll('button').find((b) => b.text() === 'User Input')
    await tab.trigger('click')
    expect(wrapper.get('.markdown-body').text()).toContain('note')
  })

  it('shows the retrospective with visual priority when present', async () => {
    h.getProject.mockResolvedValue({
      ...detail,
      retrospective: '# Retrospective\n\n- summary',
    })
    const wrapper = await mountDetail()
    await flushPromises()

    const cards = wrapper.findAll('.app-card')
    // header (0), finalization + retrospective merged (1), documents (2)
    const merged = cards[1]
    expect(merged.text()).toContain('Finalization')
    expect(merged.text()).toContain('Retrospective')
    expect(merged.get('.markdown-body').find('h1').text()).toBe('Retrospective')
  })

  it('does not render the retrospective card when absent', async () => {
    const wrapper = await mountLoaded()
    expect(wrapper.text()).not.toContain('Retrospective')
  })

  it('switches documents when another tab is selected', async () => {
    const wrapper = await mountLoaded()
    const tab = wrapper.findAll('button').find((b) => b.text() === 'Code Summary')
    await tab.trigger('click')
    expect(wrapper.get('.markdown-body').text()).toContain('CODE')
  })

  it('renders a back link to the dashboard', async () => {
    const wrapper = await mountLoaded()
    const back = wrapper.get('a[href="/"]')
    expect(back.text()).toContain('Back to projects')
  })

  it('updates the percentage and refetches on a progress event', async () => {
    h.getProject
      .mockResolvedValueOnce({ ...detail })
      .mockResolvedValueOnce({ ...detail, completionPercentage: 75 })
    const wrapper = await mountDetail()
    await flushPromises()
    expect(h.getProject).toHaveBeenCalledTimes(1)

    h.progressCb({ executionId: 101, completionPercentage: 75 })
    await flushPromises()

    expect(wrapper.find('[role="img"]').attributes('aria-label')).toBe('75% complete')
    expect(h.getProject).toHaveBeenCalledTimes(2)
  })

  it('ignores a progress event for another project', async () => {
    await mountLoaded()
    h.progressCb({ executionId: 999, completionPercentage: 10 })
    await flushPromises()
    expect(h.getProject).toHaveBeenCalledTimes(1)
  })

  it('shows a placeholder when a document is empty', async () => {
    h.getProject.mockResolvedValue({
      ...project,
      finalReview: null,
      userInput: null,
      requirements: null,
      codeSummary: null,
      testSummary: null,
    })
    const wrapper = await mountDetail()
    await flushPromises()
    expect(wrapper.text()).toContain('No content available.')
  })

  it('shows an error and retries the load', async () => {
    h.getProject.mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce({ ...detail })
    const wrapper = await mountDetail()
    await flushPromises()
    expect(wrapper.text()).toContain('boom')

    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Alpha')
  })

  it('renames the project from the header', async () => {
    const wrapper = await mountLoaded()
    await wrapper.get('button[aria-label^="Rename project"]').trigger('click')

    const input = wrapper.get('input[aria-label="Project name"]')
    expect(input.element.value).toBe('Alpha')

    h.updateProjectName.mockResolvedValue({ ...detail, name: 'Beta' })
    await input.setValue('Beta')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(h.updateProjectName).toHaveBeenCalledWith(101, 'Beta')
    expect(wrapper.get('h1').text()).toBe('Beta')
    expect(h.toastSuccess).toHaveBeenCalled()
    expect(wrapper.find('input[aria-label="Project name"]').exists()).toBe(false)
  })

  it('cancels editing without saving', async () => {
    const wrapper = await mountLoaded()
    await wrapper.get('button[aria-label^="Rename project"]').trigger('click')
    await wrapper.get('input[aria-label="Project name"]').setValue('Beta')

    const cancel = wrapper.findAll('button').find((b) => b.text().includes('Cancel'))
    await cancel.trigger('click')

    expect(wrapper.get('h1').text()).toBe('Alpha')
    expect(h.updateProjectName).not.toHaveBeenCalled()
  })

  it('shows an error and stays in edit mode when the rename fails', async () => {
    const wrapper = await mountLoaded()
    await wrapper.get('button[aria-label^="Rename project"]').trigger('click')

    h.updateProjectName.mockRejectedValueOnce(new Error('nope'))
    await wrapper.get('input[aria-label="Project name"]').setValue('Beta')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(h.toastError).toHaveBeenCalled()
    expect(wrapper.find('input[aria-label="Project name"]').exists()).toBe(true)
  })
})
