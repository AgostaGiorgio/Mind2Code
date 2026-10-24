import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import App from '@/App.vue'
import AppHeader from '@/components/AppHeader.vue'
import AppNavbar from '@/components/AppNavbar.vue'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/', name: 'dashboard', component: { template: '<div />' } }],
  })
}

describe('AppHeader', () => {
  it('renders the app title', () => {
    const wrapper = mount(AppHeader)
    expect(wrapper.text()).toContain('Mind2Code')
  })

  it('renders the "2" in the primary brand colour', () => {
    const wrapper = mount(AppHeader)
    expect(wrapper.get('.text-brand-primary').text()).toBe('2')
  })
})

describe('AppNavbar', () => {
  it('renders the home link and marks it active on the dashboard route', async () => {
    const router = makeRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(AppNavbar, { global: { plugins: [router] } })
    const link = wrapper.get('a')
    expect(link.attributes('aria-label')).toBe('Home')
    expect(link.attributes('aria-current')).toBe('page')
  })

  it('does not mark the link active on another route', async () => {
    const router = makeRouter()
    router.push('/other')
    await router.isReady()

    const wrapper = mount(AppNavbar, { global: { plugins: [router] } })
    const link = wrapper.get('a')
    expect(link.attributes('aria-current')).toBeUndefined()
  })
})

describe('App shell', () => {
  it('renders the header, navigation and routed content without a full reload', async () => {
    const router = makeRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router],
        stubs: { AppNavbar: true, ToastHost: true },
      },
    })
    expect(wrapper.findComponent(AppHeader).exists()).toBe(true)
    expect(wrapper.find('header').exists()).toBe(true)
    expect(wrapper.get('header').text()).toContain('Mind2Code')
  })
})
