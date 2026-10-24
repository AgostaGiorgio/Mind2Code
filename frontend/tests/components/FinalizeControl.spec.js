import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const h = vi.hoisted(() => ({ finalizeProject: vi.fn() }))

vi.mock('@/services/api', () => ({ finalizeProject: h.finalizeProject }))

import FinalizeControl from '@/components/ui/FinalizeControl.vue'

function makeProject(overrides = {}) {
  return {
    id: 'id-101',
    executionId: 101,
    name: 'Alpha',
    githubUrl: 'https://github.com/me/alpha',
    completionPercentage: 100,
    finalizationPercentage: 0,
    finalRepoUrl: null,
    finalizeError: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  h.finalizeProject.mockReset()
})

describe('FinalizeControl', () => {
  it('shows a placeholder when the project is not fully complete', () => {
    const wrapper = mount(FinalizeControl, {
      props: { project: makeProject({ completionPercentage: 40 }) },
    })
    expect(wrapper.text()).toContain('—')
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('shows a rocket that triggers finalization for an eligible project', async () => {
    h.finalizeProject.mockResolvedValue(undefined)
    const wrapper = mount(FinalizeControl, { props: { project: makeProject() } })

    await wrapper.get('button[aria-label="Finalize project Alpha"]').trigger('click')
    await flushPromises()

    expect(h.finalizeProject).toHaveBeenCalledWith(101)
  })

  it('shows the orange finalization ring while in progress', () => {
    const wrapper = mount(FinalizeControl, {
      props: { project: makeProject({ finalizationPercentage: 60 }) },
    })
    expect(wrapper.get('[role="img"]').attributes('aria-label')).toBe('60% complete')
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('surfaces an API error behind a warning icon', async () => {
    h.finalizeProject.mockRejectedValue(new Error('boom'))
    const wrapper = mount(FinalizeControl, { props: { project: makeProject() } })

    await wrapper.get('button[aria-label="Finalize project Alpha"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('button[aria-label="Show finalization error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('boom')
  })

  it('shows the persisted finalize error stored on the project', () => {
    const wrapper = mount(FinalizeControl, {
      props: { project: makeProject({ finalizeError: 'repo already exists' }) },
    })
    expect(wrapper.find('button[aria-label="Show finalization error"]').exists()).toBe(true)
  })
})
