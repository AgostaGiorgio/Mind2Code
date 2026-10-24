import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import Badge from '@/components/ui/Badge.vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Field from '@/components/ui/Field.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import SelectField from '@/components/ui/SelectField.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ToastHost from '@/components/ui/ToastHost.vue'
import { useToast } from '@/composables/useToast'

describe('Badge', () => {
  it('renders its slot content and optional dot', () => {
    const wrapper = mount(Badge, { props: { color: '#ff0000', dot: true }, slots: { default: 'NEW' } })
    expect(wrapper.text()).toContain('NEW')
    expect(wrapper.find('span > span').exists()).toBe(true)
    expect(wrapper.attributes('style')).toContain('color: rgb(255, 0, 0)')
  })
})

describe('EmptyState', () => {
  it('renders title, description and slot', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'Nothing', description: 'Add some' },
      slots: { default: '<button>retry</button>' },
    })
    expect(wrapper.text()).toContain('Nothing')
    expect(wrapper.text()).toContain('Add some')
    expect(wrapper.find('button').text()).toBe('retry')
  })
})

describe('Skeleton', () => {
  it('renders the requested number of lines', () => {
    const wrapper = mount(Skeleton, { props: { lines: 2, height: 'h-3' } })
    expect(wrapper.findAll('.animate-pulse')).toHaveLength(2)
    expect(wrapper.find('.animate-pulse').classes()).toContain('h-3')
  })
})

describe('Field', () => {
  it('emits update:modelValue and blur', async () => {
    const wrapper = mount(Field, { props: { modelValue: '', label: 'Name', placeholder: 'Type' } })
    expect(wrapper.text()).toContain('Name')
    await wrapper.get('input').setValue('hello')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['hello'])
    await wrapper.get('input').trigger('blur')
    expect(wrapper.emitted('blur')).toBeTruthy()
  })

  it('shows the error, suffix and hint variants', async () => {
    const wrapper = mount(Field, { props: { modelValue: 5, error: 'required', suffix: '%' } })
    expect(wrapper.text()).toContain('required')
    expect(wrapper.text()).toContain('%')

    await wrapper.setProps({ error: '', hint: 'helpful' })
    expect(wrapper.text()).toContain('helpful')
  })
})

describe('SelectField', () => {
  it('renders options and emits on change', async () => {
    const options = [
      { value: 'a', label: 'Alpha' },
      { value: 'b', label: 'Beta' },
    ]
    const wrapper = mount(SelectField, { props: { modelValue: 'a', options, label: 'Pick' } })
    expect(wrapper.findAll('option')).toHaveLength(2)
    await wrapper.get('select').setValue('b')
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual(['b'])
    expect(wrapper.emitted('change').at(-1)).toEqual(['b'])
  })

  it('renders a disabled placeholder option', () => {
    const wrapper = mount(SelectField, { props: { placeholder: 'Choose', options: [] } })
    const placeholder = wrapper.get('option')
    expect(placeholder.text()).toBe('Choose')
    expect(placeholder.attributes('disabled')).toBeDefined()
  })
})

describe('SegmentedControl', () => {
  it('marks the active option and emits selection', async () => {
    const options = [
      { value: 'x', label: 'X' },
      { value: 'y', label: 'Y' },
    ]
    const wrapper = mount(SegmentedControl, { props: { modelValue: 'x', options } })
    expect(wrapper.findAll('button')).toHaveLength(2)
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['y'])
  })
})

describe('BottomSheet', () => {
  it('renders its content when open and emits close', async () => {
    const wrapper = mount(BottomSheet, {
      props: { open: true, title: 'Sheet' },
      slots: { default: '<p>body</p>' },
      global: { stubs: { teleport: true } },
    })
    expect(wrapper.text()).toContain('Sheet')
    expect(wrapper.text()).toContain('body')

    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders nothing when closed', () => {
    const wrapper = mount(BottomSheet, {
      props: { open: false },
      global: { stubs: { teleport: true } },
    })
    expect(wrapper.text()).not.toContain('Sheet')
  })
})

describe('ToastHost', () => {
  it('renders toasts pushed into the store', async () => {
    const { push, toasts, dismiss } = useToast()
    toasts.value.slice().forEach((t) => dismiss(t.id))

    const wrapper = mount(ToastHost)
    push('First', 'success', 0)
    push('Second', 'error', 0)
    await nextTick()

    expect(wrapper.text()).toContain('First')
    expect(wrapper.text()).toContain('Second')

    toasts.value.slice().forEach((t) => dismiss(t.id))
  })
})
