import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import { ApiProblem } from '~/api/problems'
import DataTable from '~/shared/components/DataTable.vue'
import ErrorState from '~/shared/components/ErrorState.vue'

const problem = new ApiProblem({
  status: 500,
  code: 'internal_error',
  detail: 'boom',
  traceId: 'ref-4bf92f35',
})
const columns = [{ accessorKey: 'name', header: 'Name' }]

describe('ErrorState', () => {
  it('shows the message and the reference code', async () => {
    const wrapper = await mountSuspended(ErrorState, { props: { problem } })

    expect(wrapper.text()).toContain('Something went wrong on our side.')
    expect(wrapper.text()).toContain('Reference code: ref-4bf92f35')
  })

  it('asks to be retried', async () => {
    const wrapper = await mountSuspended(ErrorState, { props: { problem } })

    await wrapper.get('button').trigger('click')

    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})

describe('DataTable', () => {
  it('shows the rows', async () => {
    const wrapper = await mountSuspended(DataTable, {
      props: { rows: [{ name: 'Rina' }, { name: 'Arjun' }], columns, emptyTitle: 'No students' },
    })

    expect(wrapper.text()).toContain('Rina')
    expect(wrapper.text()).toContain('Arjun')
  })

  it('shows the empty state when there are no rows', async () => {
    const wrapper = await mountSuspended(DataTable, {
      props: { rows: [], columns, emptyTitle: 'No students yet' },
    })

    expect(wrapper.text()).toContain('No students yet')
  })

  it('shows the error state instead of the table', async () => {
    const wrapper = await mountSuspended(DataTable, {
      props: { rows: [], columns, emptyTitle: 'No students', error: problem },
    })

    expect(wrapper.find('table').exists()).toBe(false)
    expect(wrapper.text()).toContain('ref-4bf92f35')
  })
})
