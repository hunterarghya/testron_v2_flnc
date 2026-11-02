import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { notifySessionExpired } from '~/api/session-events'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import OnScreenKeyboard from '~/shared/components/OnScreenKeyboard.vue'
import SessionExpiredDialog from '~/shared/components/SessionExpiredDialog.vue'
import { useSession } from '~/shared/composables/useSession'

function bodyButton(label: string): HTMLButtonElement | undefined {
  return [...document.body.querySelectorAll('button')].find(button => button.textContent?.trim() === label)
}

describe('ConfirmDialog', () => {
  it('needs the exact text typed before it can confirm', async () => {
    const wrapper = await mountSuspended(ConfirmDialog, {
      props: { open: true, title: 'Delete Rina Das?', description: 'x', confirmLabel: 'Delete permanently', danger: true, typedConfirmation: 'Rina Das' },
      attachTo: document.body,
    })
    await nextTick()
    expect(bodyButton('Delete permanently')?.disabled).toBe(true)

    const input = document.body.querySelector('input') as HTMLInputElement
    input.value = 'Rina Das'
    input.dispatchEvent(new Event('input'))
    await nextTick()
    bodyButton('Delete permanently')?.click()

    expect(wrapper.emitted('confirm')).toEqual([['Rina Das']])
    wrapper.unmount()
  })

  it('confirms at once when no typing is asked for', async () => {
    const wrapper = await mountSuspended(ConfirmDialog, {
      props: { open: true, title: 'Decline 2 students?', description: 'x', confirmLabel: 'Decline' },
      attachTo: document.body,
    })
    await nextTick()

    bodyButton('Decline')?.click()

    expect(wrapper.emitted('confirm')).toHaveLength(1)
    wrapper.unmount()
  })
})

describe('OnScreenKeyboard (screens.md §4.0)', () => {
  it('types into the bound text', async () => {
    const wrapper = await mountSuspended(OnScreenKeyboard, { props: { 'modelValue': 'ab', 'open': true } })

    await wrapper.findAll('button').find(button => button.text() === 'q')!.trigger('click')

    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['abq'])
  })

  it('closes with Done', async () => {
    const wrapper = await mountSuspended(OnScreenKeyboard, { props: { modelValue: '', open: true } })

    await wrapper.findAll('button').find(button => button.text() === 'Done')!.trigger('click')

    expect(wrapper.emitted('update:open')).toEqual([[false]])
  })

  it('closes with Esc', async () => {
    const wrapper = await mountSuspended(OnScreenKeyboard, { props: { modelValue: '', open: true } })

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(wrapper.emitted('update:open')).toEqual([[false]])
    wrapper.unmount()
  })

  it('shows nothing while closed', async () => {
    const wrapper = await mountSuspended(OnScreenKeyboard, { props: { modelValue: '', open: false } })

    expect(wrapper.find('[role="group"]').exists()).toBe(false)
  })
})

describe('SessionExpiredDialog (screens.md §6)', () => {
  it('asks to log in again when a logged-in session expires', async () => {
    useSession().set({ id: 'u', name: 'R', email: 'r@x.in', role: 'STUDENT', status: 'ACTIVE', has_password: true, performance_shared: false })
    const wrapper = await mountSuspended(SessionExpiredDialog, { attachTo: document.body })

    notifySessionExpired()
    await flushPromises()

    expect(document.body.textContent).toContain('Please log in again')
    wrapper.unmount()
  })
})
